from collections import defaultdict
from datetime import date
from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.domain.item_catalogue import BaseUnit, ItemType
from app.models.crop_master import CropMaster
from app.models.inventory import InventoryBalance, InventoryLedger
from app.models.production import ProductionInput, ProductionRecord
from app.repositories.item_repository import ItemRepository
from app.schemas.production import ProductionCreate
from app.services.inventory_service import InventoryService
from app.services.inventory_posting_service import InventoryPostingService, StockEvent
from app.services.request_idempotency_service import RequestIdempotencyService


WRITE_ROLES = ("FPO Admin", "Manager")
READ_ROLES = ("FPO Admin", "Manager", "Accountant", "Viewer")


class ProductionService:
    def __init__(self, db: Session):
        self.db = db
        self.items = ItemRepository(db)
        self.posting = InventoryPostingService(db)

    @staticmethod
    def _organization_id(user) -> int:
        if user.organization_id is None or user.role.name == "Super Admin":
            raise HTTPException(403, "Production requires an explicit organization context")
        return user.organization_id

    @staticmethod
    def _convert(quantity: Decimal, unit: BaseUnit, item: CropMaster) -> Decimal:
        return InventoryService._to_base(Decimal(quantity), unit, BaseUnit(item.base_unit))

    def _item(self, item_id: int, organization_id: int, expected_type: ItemType) -> CropMaster:
        item = self.items.get_visible(item_id, organization_id)
        if not item or not item.is_active:
            raise HTTPException(400, "Selected production item is missing, inactive, or outside this organization")
        if item.item_type != expected_type.value:
            raise HTTPException(400, f"Selected item must be a {expected_type.value.replace('_', ' ').lower()}")
        return item

    def _get_record(self, record_id: int, organization_id: int):
        return (
            self.db.query(ProductionRecord)
            .options(joinedload(ProductionRecord.finished_item), joinedload(ProductionRecord.inputs).joinedload(ProductionInput.item))
            .filter(ProductionRecord.id == record_id, ProductionRecord.organization_id == organization_id)
            .first()
        )

    @staticmethod
    def _response(record: ProductionRecord) -> dict:
        grouped = defaultdict(Decimal)
        inputs = []
        for line in record.inputs:
            grouped[line.unit.value if isinstance(line.unit, BaseUnit) else line.unit] += Decimal(line.quantity)
            inputs.append({
                "id": line.id,
                "item_id": line.item_id,
                "item_name": line.item.crop_name,
                "item_type": line.item.item_type,
                "quantity": Decimal(line.quantity),
                "unit": line.unit,
                "base_quantity": Decimal(line.base_quantity),
                "base_unit": line.item.base_unit,
            })
        return {
            "id": record.id,
            "reference_no": record.reference_no,
            "production_date": record.production_date,
            "finished_item_id": record.finished_item_id,
            "finished_item_name": record.finished_item.crop_name,
            "output_quantity": Decimal(record.output_quantity),
            "output_unit": record.output_unit,
            "output_base_quantity": Decimal(record.output_base_quantity),
            "base_unit": record.finished_item.base_unit,
            "wastage_quantity": Decimal(record.wastage_quantity),
            "wastage_unit": record.wastage_unit,
            "wastage_base_quantity": Decimal(record.wastage_base_quantity),
            "total_input_consumption": [
                {"quantity": quantity, "unit": unit}
                for unit, quantity in sorted(grouped.items())
            ],
            "inputs": inputs,
            "status": record.status,
            "notes": record.notes,
            "created_by": record.created_by,
            "created_at": record.created_at,
        }

    def create(self, payload: ProductionCreate, user, idempotency_key: str | None):
        if user.role.name not in WRITE_ROLES:
            raise HTTPException(403, "Not authorized to post production")
        organization_id = self._organization_id(user)
        if idempotency_key is None or not idempotency_key.strip() or len(idempotency_key) > 128:
            raise HTTPException(400, "Idempotency-Key header is required (1 to 128 characters)")
        key = idempotency_key.strip()
        payload_hash = RequestIdempotencyService.payload_hash(payload, organization_id)

        try:
            if self.db.get_bind().dialect.name == "postgresql":
                self.db.execute(
                    text("SELECT pg_advisory_xact_lock(:namespace, hashtext(:request_key))"),
                    {"namespace": 360363, "request_key": f"{organization_id}:PRODUCTION_CREATE:{key}"},
                )
            existing = self.db.query(ProductionRecord).filter_by(
                organization_id=organization_id, idempotency_key=key
            ).with_for_update().first()

            if existing:
                if existing.payload_hash != payload_hash:
                    raise HTTPException(409, "Idempotency-Key was already used for a different production payload")
                return self._response(self._get_record(existing.id, organization_id))

            if len({line.item_id for line in payload.inputs}) != len(payload.inputs):
                raise HTTPException(400, "Use one input row per catalogue item")

            finished = self._item(payload.finished_item_id, organization_id, ItemType.FINISHED_GOOD)
            output_base = self._convert(payload.output_quantity, payload.output_unit, finished)

            if payload.wastage_quantity == 0:
                # Even a zero wastage quantity must use a unit compatible with
                # the finished item's dimension.
                self._convert(Decimal("1"), payload.wastage_unit, finished)
                wastage_base = Decimal("0.000000")
            else:
                wastage_base = self._convert(payload.wastage_quantity, payload.wastage_unit, finished)

            raw_material_types = (
                ItemType.RAW_MATERIAL.value,
                ItemType.AGRICULTURAL_COMMODITY.value,
            )

            checked_inputs = []

            for line in payload.inputs:
                item = self.items.get_visible(line.item_id, organization_id)

                if not item or not item.is_active:
                    raise HTTPException(
                        400,
                        "Selected production input is missing, inactive, or outside this organization"
                    )

                if item.item_type not in (
                    *raw_material_types,
                    ItemType.PACKAGING_MATERIAL.value,
                ):
                    raise HTTPException(
                        400,
                        "Production inputs must be raw or packaging materials"
                    )

                base_quantity = self._convert(line.quantity, line.unit, item)
                checked_inputs.append((line, item, base_quantity))

            if not any(
                item.item_type in raw_material_types
                for _, item, _ in checked_inputs
            ):
                raise HTTPException(400, "At least one raw material input is required")

            reference_no = f"PR-{date.today():%Y%m%d}-{uuid4().hex[:8].upper()}"
            record = ProductionRecord(
                organization_id=organization_id,
                reference_no=reference_no,
                idempotency_key=key,
                payload_hash=payload_hash,
                production_date=payload.production_date,
                finished_item_id=finished.id,
                output_quantity=payload.output_quantity,
                output_unit=payload.output_unit.value,
                output_base_quantity=output_base,
                wastage_quantity=payload.wastage_quantity,
                wastage_unit=payload.wastage_unit.value,
                wastage_base_quantity=wastage_base,
                status="POSTED",
                notes=payload.notes.strip() if payload.notes else None,
                created_by=getattr(user, "id", None),
            )
            self.db.add(record)
            self.db.flush()

            line_rows = []
            for line, item, base_quantity in checked_inputs:
                line_row = ProductionInput(
                    production_id=record.id,
                    organization_id=organization_id,
                    item_id=item.id,
                    input_type=(
                        ItemType.PACKAGING_MATERIAL.value
                        if item.item_type == ItemType.PACKAGING_MATERIAL.value
                        else ItemType.RAW_MATERIAL.value),
                    quantity=line.quantity,
                    unit=line.unit.value,
                    base_quantity=base_quantity,
                )
                self.db.add(line_row)
                line_rows.append((line_row, item))
            self.db.flush()

            events = []
            for line_row, item in line_rows:
                events.append(StockEvent(
                    organization_id=organization_id,
                    item_id=item.id,
                    transaction_type="OUT",
                    quantity=Decimal(line_row.base_quantity),
                    reference_type="PRODUCTION",
                    reference_id=record.id,
                    idempotency_key=f"PRODUCTION:{record.id}:INPUT:{line_row.id}",
                    remarks=f"Production {record.reference_no} input",
                    expected_base_unit=item.base_unit,
                ))
            events.append(StockEvent(
                organization_id=organization_id,
                item_id=finished.id,
                transaction_type="IN",
                quantity=output_base,
                reference_type="PRODUCTION",
                reference_id=record.id,
                idempotency_key=f"PRODUCTION:{record.id}:OUTPUT",
                remarks=f"Production {record.reference_no} output",
                expected_base_unit=finished.base_unit,
            ))
            self.posting.post_events(events)
            self.db.commit()
            return self._response(self._get_record(record.id, organization_id))

        except HTTPException:
            self.db.rollback()
            raise
        except IntegrityError as exc:
            self.db.rollback()
            if "uq_production_org_reference" in str(exc) or "uq_production_org_idempotency" in str(exc):
                raise HTTPException(409, "Production reference or idempotency key already exists") from exc
            raise
        except Exception:
            self.db.rollback()
            raise

    def list(self, user):
        if user.role.name not in READ_ROLES:
            raise HTTPException(403, "Not authorized to view production")
        organization_id = self._organization_id(user)
        records = (
            self.db.query(ProductionRecord)
            .options(joinedload(ProductionRecord.finished_item), joinedload(ProductionRecord.inputs).joinedload(ProductionInput.item))
            .filter(ProductionRecord.organization_id == organization_id)
            .order_by(ProductionRecord.production_date.desc(), ProductionRecord.id.desc())
            .all()
        )
        return [self._response(record) for record in records]

    def get(self, record_id: int, user):
        if user.role.name not in READ_ROLES:
            raise HTTPException(403, "Not authorized to view production")
        record = self._get_record(record_id, self._organization_id(user))
        if not record:
            raise HTTPException(404, "Production record not found")
        return self._response(record)