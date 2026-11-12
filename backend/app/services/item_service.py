from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from sqlalchemy.orm import Session
import re

from app.domain.item_catalogue import ItemType, BaseUnit, ITEM_CODE_PREFIXES
from app.models.crop_master import CropMaster
from app.models.inventory import InventoryBalance, InventoryLedger
from app.repositories.item_repository import ItemRepository
from app.schemas.item import ItemCreate, ItemUpdate


WRITER_ROLES = ("Super Admin", "FPO Admin")


class ItemService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ItemRepository(db)

    @staticmethod
    def _as_dict(item):
        return {
            "id": item.id,
            "item_code": item.crop_code,
            "item_name": item.crop_name,
            "item_type": item.item_type,
            "category": item.crop_category,
            "base_unit": item.base_unit,
            "description": item.description,
            "organization_id": item.organization_id,
            "is_active": item.is_active,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
            "crop_code": item.crop_code,
            "crop_name": item.crop_name,
            "crop_category": item.crop_category,
            "unit": item.unit,
        }

    def _writable(self, user):
        if user.role.name not in WRITER_ROLES:
            raise HTTPException(403, "Not authorized to manage items")

    def generate_code(self, item_type, *, lock=True):
        """Build the next globally unique code; a PostgreSQL transaction lock serializes allocation."""
        try:
            item_type = item_type if isinstance(item_type, ItemType) else ItemType(item_type)
        except ValueError:
            raise HTTPException(400, "Invalid item type")
        prefix = ITEM_CODE_PREFIXES[item_type]
        if lock and self.db.get_bind().dialect.name == "postgresql":
            lock_number = list(ITEM_CODE_PREFIXES).index(item_type) + 1
            self.db.execute(
                text("SELECT pg_advisory_xact_lock(:namespace, :lock_number)"),
                {"namespace": 360360, "lock_number": lock_number},
            )
        pattern = re.compile(rf"^{re.escape(prefix)}-(\d+)$")
        codes = self.db.query(CropMaster.crop_code).filter(
            CropMaster.crop_code.like(f"{prefix}-%")
        ).all()
        largest = max(
            (int(match.group(1)) for (code,) in codes if (match := pattern.fullmatch(code))),
            default=0,
        )
        return f"{prefix}-{largest + 1:05d}"

    def get_next_code(self, item_type, user):
        self._writable(user)
        try:
            parsed_type = item_type if isinstance(item_type, ItemType) else ItemType(item_type)
        except ValueError:
            raise HTTPException(400, "Invalid item type")
        if parsed_type != ItemType.AGRICULTURAL_COMMODITY and user.role.name == "Super Admin":
            raise HTTPException(400, "Commercial items must be created by an organization user")
        return {"item_code": self.generate_code(parsed_type, lock=False)}

    def list_items(self, user, search=None, item_type=None, is_active=None):
        org_id = None if user.role.name == "Super Admin" else user.organization_id
        return [self._as_dict(item) for item in self.repo.list(org_id, search, item_type, is_active)]

    def get_item(self, item_id, user):
        org_id = None if user.role.name == "Super Admin" else user.organization_id
        item = self.repo.get_visible(item_id, org_id)
        if not item:
            raise HTTPException(404, "Item not found")
        return self._as_dict(item)

    def create_item(self, payload: ItemCreate, user):
        self._writable(user)
        item_type = payload.item_type.value
        if item_type == ItemType.AGRICULTURAL_COMMODITY.value and payload.base_unit != BaseUnit.KG:
            raise HTTPException(400, "Agricultural commodities must use KG as the base unit")
        if item_type != ItemType.AGRICULTURAL_COMMODITY.value and user.role.name == "Super Admin":
            raise HTTPException(400, "Commercial items must be created by an organization user")
        try:
            code = self.generate_code(ItemType(item_type))
            item = CropMaster(
                crop_code=code, crop_name=payload.item_name.strip(),
                crop_category=payload.category.strip() if payload.category else None,
                unit="Kg", item_type=item_type,
                organization_id=None if item_type == ItemType.AGRICULTURAL_COMMODITY.value else user.organization_id,
                base_unit=payload.base_unit.value,
                description=payload.description.strip() if payload.description else None,
                is_active=True,
            )
            self.db.add(item)
            self.db.commit()
            self.db.refresh(item)
            return self._as_dict(item)
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(409, "Item code already exists")

    def update_item(self, item_id, payload: ItemUpdate, user):
        self._writable(user)
        org_id = None if user.role.name == "Super Admin" else user.organization_id
        item = self.repo.get_visible_for_update(item_id, org_id)
        if not item:
            raise HTTPException(404, "Item not found")
        changes = payload.model_dump(exclude_unset=True)
        target_type = changes.get("item_type", ItemType(item.item_type))
        target_type = target_type.value if isinstance(target_type, ItemType) else target_type
        if target_type != item.item_type:
            raise HTTPException(400, "Item type cannot change because its generated code is tied to its type")
        new_unit = changes.get("base_unit", BaseUnit(item.base_unit))
        new_unit = new_unit.value if isinstance(new_unit, BaseUnit) else new_unit
        if target_type == ItemType.AGRICULTURAL_COMMODITY.value and new_unit != BaseUnit.KG.value:
            raise HTTPException(400, "Agricultural commodities must use KG as the base unit")
        if new_unit != item.base_unit:
            has_history = self.db.query(InventoryLedger.id).filter(
                InventoryLedger.item_id == item.id
            ).first() is not None
            has_balance = self.db.query(InventoryBalance.item_id).filter(
                InventoryBalance.item_id == item.id
            ).first() is not None
            if has_history or has_balance:
                raise HTTPException(
                    409,
                    "Base unit cannot change after inventory movements or a balance record exist",
                )
        try:
            for field, value in changes.items():
                if field == "item_name":
                    item.crop_name = value.strip()
                elif field == "category":
                    item.crop_category = value.strip() if value else None
                elif field == "item_type":
                    item.item_type = target_type
                elif field == "base_unit":
                    item.base_unit = new_unit
                elif field == "description":
                    item.description = value.strip() if value else None
            self.db.commit()
            self.db.refresh(item)
            return self._as_dict(item)
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(409, "Item code already exists")

    def set_active(self, item_id, is_active, user):
        self._writable(user)
        org_id = None if user.role.name == "Super Admin" else user.organization_id
        item = self.repo.get_visible(item_id, org_id)
        if not item:
            raise HTTPException(404, "Item not found")
        item.is_active = is_active
        self.db.commit()
        self.db.refresh(item)
        return self._as_dict(item)
