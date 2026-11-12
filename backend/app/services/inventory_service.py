from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.domain.item_catalogue import BaseUnit, ItemType
from app.models.crop_master import CropMaster
from app.models.inventory import InventoryLedger
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.item_repository import ItemRepository
from app.schemas.inventory import InventoryAdjustRequest
from app.services.inventory_posting_service import InventoryPostingService


READ_ROLES = ("FPO Admin", "Manager", "Accountant", "Viewer")
WRITE_ROLES = ("FPO Admin", "Manager")
MASS_FACTORS = {BaseUnit.G: Decimal("0.001"), BaseUnit.KG: Decimal("1"),
                BaseUnit.QUINTAL: Decimal("100"), BaseUnit.TON: Decimal("1000")}
VOLUME_FACTORS = {BaseUnit.ML: Decimal("0.001"), BaseUnit.L: Decimal("1")}


class InventoryService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = InventoryRepository(db)
        self.item_repo = ItemRepository(db)
        self.posting = InventoryPostingService(db)

    @staticmethod
    def _organization_id(user) -> int:
        if user.role.name == "Super Admin" or user.organization_id is None:
            raise HTTPException(403, "Inventory access requires an explicit organization context")
        return user.organization_id

    @staticmethod
    def _item_data(item: CropMaster):
        return {
            "item_id": item.id,
            "item_name": item.crop_name,
            "item_type": item.item_type,
            "base_unit": item.base_unit,
            "crop_id": item.id if item.item_type == ItemType.AGRICULTURAL_COMMODITY.value else None,
            "crop_name": item.crop_name if item.item_type == ItemType.AGRICULTURAL_COMMODITY.value else None,
        }

    @staticmethod
    def _movement_data(movement: InventoryLedger, item: CropMaster):
        return {
            "id": movement.id,
            "organization_id": movement.organization_id,
            **InventoryService._item_data(item),
            "transaction_type": movement.transaction_type,
            "quantity": Decimal(movement.quantity),
            "reference_type": movement.reference_type,
            "reference_id": movement.reference_id,
            "idempotency_key": movement.idempotency_key,
            "reverses_id": movement.reverses_id,
            "source_revision": movement.source_revision,
            "remarks": movement.remarks,
            "is_active": movement.is_active,
            "created_at": movement.created_at,
            "updated_at": movement.updated_at,
        }

    def list_balances(self, current_user):
        if current_user.role.name not in READ_ROLES:
            raise HTTPException(403, "Not authorized to view inventory")
        org_id = self._organization_id(current_user)
        if self.repo.reconciliation(org_id):
            raise HTTPException(409, "Inventory balances do not match the movement ledger; reconcile before viewing stock")
        rows = self.repo.get_balances(org_id)
        return [
            {
                **self._item_data(item),
                "total_in": Decimal(total_in or 0),
                "total_out": Decimal(total_out or 0),
                "current_balance": Decimal(balance.quantity),
            }
            for balance, item, total_in, total_out in rows
        ]

    def get_ledger(self, item_id: int, current_user):
        if current_user.role.name not in READ_ROLES:
            raise HTTPException(403, "Not authorized to view inventory")
        org_id = self._organization_id(current_user)
        item = self.item_repo.get_visible(item_id, org_id)
        if item is None:
            raise HTTPException(404, "Inventory item not found")
        return [
            self._movement_data(entry, item)
            for entry in self.repo.list_ledger_by_item(org_id, item_id)
        ]

    def list_ledger(self, current_user):
        if current_user.role.name not in READ_ROLES:
            raise HTTPException(403, "Not authorized to view inventory")
        org_id = self._organization_id(current_user)
        return [
            self._movement_data(entry, entry.item)
            for entry in self.repo.list_ledger_by_organization(org_id)
        ]

    @staticmethod
    def _to_base(quantity: Decimal, input_unit: BaseUnit, base_unit: BaseUnit) -> Decimal:
        if input_unit in MASS_FACTORS and base_unit in MASS_FACTORS:
            result = quantity * MASS_FACTORS[input_unit] / MASS_FACTORS[base_unit]
        elif input_unit in VOLUME_FACTORS and base_unit in VOLUME_FACTORS:
            result = quantity * VOLUME_FACTORS[input_unit] / VOLUME_FACTORS[base_unit]
        elif input_unit == base_unit == BaseUnit.PCS:
            result = quantity
        else:
            raise HTTPException(400, f"Unsupported conversion from {input_unit.value} to {base_unit.value}")
        if not result.is_finite() or result <= 0 or result.as_tuple().exponent < -6:
            raise HTTPException(400, "Converted quantity must be positive and fit 6 decimal places")
        if base_unit == BaseUnit.PCS and result != result.to_integral_value():
            raise HTTPException(400, "PCS quantities must be whole numbers")
        return result

    def adjust_stock(
        self, payload: InventoryAdjustRequest, current_user, idempotency_key: str,
    ):
        if current_user.role.name not in WRITE_ROLES:
            raise HTTPException(403, "Not authorized to adjust inventory")
        org_id = self._organization_id(current_user)
        item_id = payload.item_id or payload.crop_id
        item = self.item_repo.get_visible(item_id, org_id)
        if item is None:
            raise HTTPException(404, "Inventory item not found")
        if payload.crop_id is not None and item.item_type != ItemType.AGRICULTURAL_COMMODITY.value:
            raise HTTPException(400, "crop_id is reserved for agricultural commodities; use item_id")
        if not item.is_active:
            raise HTTPException(400, "Inactive items cannot be used for new stock operations")
        try:
            base_unit = BaseUnit(item.base_unit)
            input_unit = payload.unit or base_unit
        except ValueError:
            raise HTTPException(400, "Item has an unsupported base unit")
        if item.item_type == ItemType.AGRICULTURAL_COMMODITY.value and base_unit != BaseUnit.KG:
            raise HTTPException(409, "Agricultural inventory must use KG as its base unit")
        quantity = self._to_base(payload.quantity, input_unit, base_unit)

        try:
            movement = self.posting.post_manual(
                org_id,
                item.id,
                payload.transaction_type,
                quantity,
                "MANUAL",
                idempotency_key,
                payload.remarks,
                expected_base_unit=base_unit.value,
            )
            self.db.commit()
            self.db.refresh(movement)
            return self._movement_data(movement, item)
        except Exception:
            self.db.rollback()
            raise

    def reconcile(self, current_user):
        if current_user.role.name not in READ_ROLES:
            raise HTTPException(403, "Not authorized to view inventory reconciliation")
        org_id = self._organization_id(current_user)
        return [
            {
                "organization_id": row.organization_id,
                "item_id": row.item_id,
                "item_name": row.crop_name,
                "balance_quantity": Decimal(row.balance_quantity),
                "ledger_quantity": Decimal(row.ledger_quantity),
                "difference": Decimal(row.difference),
            }
            for row in self.repo.reconciliation(org_id)
        ]
