from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal

from app.repositories.sale_repository import SaleRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.crop_master_repository import CropMasterRepository
from app.repositories.inventory_repository import InventoryRepository
from app.models.sale import Sale
from app.schemas.sale import SaleCreate, SaleUpdate
from app.services.inventory_posting_service import InventoryPostingService
from app.services.request_idempotency_service import RequestIdempotencyService
from app.domain.item_catalogue import BaseUnit
from app.services.inventory_service import InventoryService


class SaleService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SaleRepository(db)
        self.customer_repo = CustomerRepository(db)
        self.crop_repo = CropMasterRepository(db)
        self.inventory_repo = InventoryRepository(db)
        self.inventory_posting = InventoryPostingService(db)
        self.request_idempotency = RequestIdempotencyService(db)

    def _generate_sale_no(self, organization_id: int) -> str:
        year = datetime.now().year
        latest = self.repo.get_latest_by_org(organization_id)
        if not latest or not latest.sale_no.startswith(f"SA-{year}"):
            return f"SA-{year}-00001"
        try:
            num = int(latest.sale_no.split("-")[2])
            return f"SA-{year}-{num + 1:05d}"
        except Exception:
            return f"SA-{year}-00001"

    def _convert_to_base(self, quantity: Decimal, unit: str, base_unit: str) -> Decimal:
        try:
            return InventoryService._to_base(Decimal(quantity), BaseUnit(unit), BaseUnit(base_unit))
        except ValueError as exc:
            raise HTTPException(400, "Invalid sale unit") from exc

    def _calculate_total_amount(self, user_entered_quantity: float, rate_per_unit: Decimal) -> Decimal:
        return Decimal(user_entered_quantity) * Decimal(rate_per_unit)

    def create_sale(
        self, payload: SaleCreate, current_user, idempotency_key: str | None = None
    ) -> Sale:
        if current_user.role.name not in ["Super Admin", "FPO Admin", "Manager"]:
            raise HTTPException(403, "Not authorized")

        org_id = payload.organization_id or current_user.organization_id
        if current_user.role.name != "Super Admin" and org_id != current_user.organization_id:
            raise HTTPException(403, "Cannot create sale for another organization")

        try:
            payload_hash = self.request_idempotency.payload_hash(payload, org_id)
            existing = self.request_idempotency.find_existing(
                org_id, "SALE_CREATE", idempotency_key, payload_hash
            )
            if existing is not None:
                original = self.repo.get_by_id(existing.source_id)
                if original is None or original.organization_id != org_id:
                    raise HTTPException(409, "Idempotent sale result is no longer available")
                return original

            customer = self.customer_repo.get_by_id(payload.customer_id)
            if not customer or customer.organization_id != org_id or not customer.is_active:
                raise HTTPException(400, "Invalid or inactive customer")
            crop = self.crop_repo.get_active_sellable_item(payload.crop_id, org_id)
            if not crop:
                raise HTTPException(400, "Invalid or inactive sale item")
            if payload.quantity <= 0 or payload.rate_per_unit <= 0:
                raise HTTPException(400, "Quantity and rate must be positive")
            if payload.payment_status not in ("Pending", "Paid"):
                raise HTTPException(400, "Payment status must be Pending or Paid")

            quantity_in_kg = self._convert_to_base(payload.quantity, payload.unit, crop.base_unit)
            total_amount = self._calculate_total_amount(payload.quantity, payload.rate_per_unit)
            sale = Sale(
                sale_no=self._generate_sale_no(org_id),
                sale_date=payload.sale_date,
                customer_id=payload.customer_id,
                crop_id=payload.crop_id,
                organization_id=org_id,
                quantity=quantity_in_kg,
                unit=payload.unit,
                rate_per_unit=payload.rate_per_unit,
                total_amount=total_amount,
                payment_status=payload.payment_status,
                remarks=payload.remarks,
                is_active=True,
            )
            self.repo.create(sale, commit=False)

            self.inventory_posting.post_events([
                self.inventory_posting.source_event(
                    sale.organization_id,
                    sale.crop_id,
                    "OUT",
                    Decimal(sale.quantity),
                    "SALE",
                    sale.id,
                    1,
                    f"Sale {sale.sale_no}",
                )
            ])

            self.request_idempotency.store(
                org_id, "SALE_CREATE", idempotency_key, payload_hash, sale.id
            )

            self.db.commit()
            self.db.refresh(sale)
            return sale
        except Exception:
            self.db.rollback()
            raise

    def update_sale(self, sale_id: int, payload: SaleUpdate, current_user) -> Sale:
        if current_user.role.name not in ["Super Admin", "FPO Admin", "Manager"]:
            raise HTTPException(403, "Not authorized")

        sale = self.repo.get_by_id_for_update(sale_id)
        if not sale:
            raise HTTPException(404, "Sale not found")

        if current_user.role.name != "Super Admin" and sale.organization_id != current_user.organization_id:
            raise HTTPException(403, "Not authorized to update this sale")

        # Require quantity when unit changes (prevents inconsistent KG/unit pairs).
        # Stored quantity is always in KG. Silently treating that KG value as a
        # user-entered quantity in a new unit (e.g. 100 KG → unit=QUINTAL)
        # would be incorrect. Match the safe rule: unit change needs a new quantity.
        if payload.unit is not None and payload.quantity is None:
            if payload.unit != sale.unit:
                raise HTTPException(
                    400,
                    "Quantity is required when changing unit. "
                    "Provide the quantity in the new unit so it can be converted to KG correctly.",
                )

        new_customer_id = payload.customer_id if payload.customer_id is not None else sale.customer_id
        new_crop_id = payload.crop_id if payload.crop_id is not None else sale.crop_id
        new_unit = payload.unit if payload.unit is not None else sale.unit
        new_rate = payload.rate_per_unit if payload.rate_per_unit is not None else sale.rate_per_unit

        if payload.crop_id is not None and new_crop_id != sale.crop_id and payload.quantity is None:
            raise HTTPException(400, "Quantity is required when changing the sale item")

        if payload.customer_id is not None:
            customer = self.customer_repo.get_by_id(new_customer_id)
            if not customer or customer.organization_id != sale.organization_id or not customer.is_active:
                raise HTTPException(400, "Invalid or inactive customer")

        if payload.crop_id is not None:
            crop = self.crop_repo.get_active_sellable_item(new_crop_id, sale.organization_id)
            if not crop:
                raise HTTPException(400, "Invalid or inactive sale item")

        try:
            target_item = crop if payload.crop_id is not None else self.crop_repo.get_by_id(sale.crop_id)
            quantity_in_kg = (
                self._convert_to_base(payload.quantity, new_unit, target_item.base_unit)
                if payload.quantity is not None else Decimal(sale.quantity)
            )
            target_active = payload.is_active if payload.is_active is not None else sale.is_active
            stock_changed = (
                target_active != sale.is_active
                or quantity_in_kg != Decimal(sale.quantity)
                or new_crop_id != sale.crop_id
            )
            history = self.inventory_posting.source_history(sale.organization_id, "SALE", sale.id)
            current_movement = self.inventory_posting.current_source_movement(
                sale.organization_id, "SALE", sale.id
            )
            if stock_changed and not history:
                raise HTTPException(409, "Sale inventory movement is missing; reconcile before editing")
            if sale.is_active and stock_changed and current_movement is None:
                raise HTTPException(409, "Active sale has no current inventory movement; reconcile before editing")

            revision = self.inventory_posting.next_source_revision(sale.organization_id, "SALE", sale.id)
            events = []
            if current_movement is not None and stock_changed:
                events.append(self.inventory_posting.reversal_event(current_movement, revision))
            if target_active and stock_changed:
                events.append(self.inventory_posting.source_event(
                    sale.organization_id,
                    new_crop_id,
                    "OUT",
                    quantity_in_kg,
                    "SALE",
                    sale.id,
                    revision,
                    f"Sale {sale.sale_no}",
                ))
            if events:
                self.inventory_posting.post_events(events)

            sale.quantity = quantity_in_kg
            sale.unit = new_unit
            sale.crop_id = new_crop_id
            sale.is_active = target_active
            if payload.sale_date is not None:
                sale.sale_date = payload.sale_date
            if payload.customer_id is not None:
                sale.customer_id = new_customer_id
            if payload.rate_per_unit is not None:
                sale.rate_per_unit = new_rate
            if payload.payment_status is not None:
                if payload.payment_status not in ("Pending", "Paid"):
                    raise HTTPException(400, "Payment status must be Pending or Paid")
                sale.payment_status = payload.payment_status
            if payload.remarks is not None:
                sale.remarks = payload.remarks

            if payload.quantity is not None:
                sale.total_amount = self._calculate_total_amount(payload.quantity, new_rate)
            elif payload.rate_per_unit is not None:
                item = self.crop_repo.get_by_id(sale.crop_id)
                display_quantity = InventoryService._to_base(
                    Decimal(sale.quantity), BaseUnit(item.base_unit), BaseUnit(sale.unit)
                )
                sale.total_amount = self._calculate_total_amount(display_quantity, new_rate)

            self.repo.update(sale, commit=True)
            return sale
        except Exception:
            self.db.rollback()
            raise

    def toggle_sale_status(self, sale_id: int, is_active: bool, current_user) -> Sale:
        if current_user.role.name not in ["Super Admin", "FPO Admin", "Manager"]:
            raise HTTPException(403, "Not authorized")

        sale = self.repo.get_by_id_for_update(sale_id)
        if not sale:
            raise HTTPException(404, "Sale not found")

        if current_user.role.name != "Super Admin" and sale.organization_id != current_user.organization_id:
            raise HTTPException(403, "Not authorized")

        if sale.is_active == is_active:
            return sale
        try:
            history = self.inventory_posting.source_history(sale.organization_id, "SALE", sale.id)
            current_movement = self.inventory_posting.current_source_movement(
                sale.organization_id, "SALE", sale.id
            )
            if not history:
                raise HTTPException(409, "Sale inventory movement is missing; reconcile before changing status")
            if sale.is_active and current_movement is None:
                raise HTTPException(409, "Active sale has no current inventory movement; reconcile before changing status")
            revision = self.inventory_posting.next_source_revision(sale.organization_id, "SALE", sale.id)
            events = []
            if current_movement is not None:
                events.append(self.inventory_posting.reversal_event(current_movement, revision))
            if is_active:
                events.append(self.inventory_posting.source_event(
                    sale.organization_id, sale.crop_id, "OUT", Decimal(sale.quantity),
                    "SALE", sale.id, revision, f"Sale {sale.sale_no}",
                ))
            self.inventory_posting.post_events(events)
            sale.is_active = is_active
            self.db.commit()
            self.db.refresh(sale)
            return sale
        except Exception:
            self.db.rollback()
            raise

    def list_sales(self, current_user):
        if current_user.role.name == "Super Admin":
            sales = self.repo.list_all()
        else:
            sales = self.repo.list_all(current_user.organization_id)

        result = []
        for s in sales:
            result.append({
                "id": s.id,
                "sale_no": s.sale_no,
                "sale_date": s.sale_date,
                "customer_id": s.customer_id,
                "crop_id": s.crop_id,
                "organization_id": s.organization_id,
                "quantity": s.quantity,
                "unit": s.unit,
                "rate_per_unit": s.rate_per_unit,
                "total_amount": s.total_amount,
                "payment_status": s.payment_status,
                "remarks": s.remarks,
                "is_active": s.is_active,
                "created_at": s.created_at,
                "updated_at": s.updated_at,
                "customer_name": s.customer.customer_name if s.customer else "—",
                "crop_name": s.crop.crop_name if s.crop else "—",
                "item_type": s.crop.item_type if s.crop else None,
                "base_unit": s.crop.base_unit if s.crop else None,
            })
        return result

    def get_sale(self, sale_id: int, current_user) -> Sale:
        sale = self.repo.get_by_id(sale_id)
        if not sale:
            raise HTTPException(404, "Sale not found")
        if current_user.role.name != "Super Admin" and sale.organization_id != current_user.organization_id:
            raise HTTPException(403, "Not authorized to view this sale")
        return sale
