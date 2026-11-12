from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.crop_master import CropMaster
from app.domain.item_catalogue import ItemType


class CropMasterRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, crop: CropMaster) -> CropMaster:
        self.db.add(crop)
        self.db.commit()
        self.db.refresh(crop)
        return crop

    def get_by_id(self, crop_id: int) -> Optional[CropMaster]:
        return self.db.query(CropMaster).filter(CropMaster.id == crop_id).first()

    def get_by_code(self, crop_code: str) -> Optional[CropMaster]:
        return self.db.query(CropMaster).filter(CropMaster.crop_code == crop_code).first()

    def list_all(self) -> List[CropMaster]:
        return self.db.query(CropMaster).all()

    def get_visible(self, crop_id: int, organization_id: Optional[int], *, active_only=False, commodity_only=False):
        query = self.db.query(CropMaster).filter(CropMaster.id == crop_id)
        if commodity_only:
            query = query.filter(CropMaster.item_type == ItemType.AGRICULTURAL_COMMODITY.value)
        if active_only:
            query = query.filter(CropMaster.is_active.is_(True))
        if organization_id is not None:
            query = query.filter(or_(CropMaster.organization_id.is_(None), CropMaster.organization_id == organization_id))
        return query.first()

    def get_active_commodity(self, crop_id: int, organization_id: Optional[int]):
        return self.get_visible(crop_id, organization_id, active_only=True, commodity_only=True)

    def get_active_sellable_item(self, item_id: int, organization_id: Optional[int]):
        return (
            self.db.query(CropMaster)
            .filter(
                CropMaster.id == item_id,
                CropMaster.is_active.is_(True),
                CropMaster.item_type.in_((ItemType.AGRICULTURAL_COMMODITY.value, ItemType.FINISHED_GOOD.value)),
                or_(CropMaster.organization_id.is_(None), CropMaster.organization_id == organization_id),
            )
            .first()
        )

    def list_visible_sellable_items(self, organization_id: Optional[int]):
        query = self.db.query(CropMaster).filter(
            CropMaster.item_type.in_((ItemType.AGRICULTURAL_COMMODITY.value, ItemType.FINISHED_GOOD.value)),
            CropMaster.is_active.is_(True),
        )
        if organization_id is not None:
            query = query.filter(or_(CropMaster.organization_id.is_(None), CropMaster.organization_id == organization_id))
        return query.order_by(CropMaster.crop_name, CropMaster.id).all()

    def list_visible(self, organization_id: Optional[int]):
        query = self.db.query(CropMaster).filter(CropMaster.item_type == ItemType.AGRICULTURAL_COMMODITY.value)
        if organization_id is not None:
            query = query.filter(or_(CropMaster.organization_id.is_(None), CropMaster.organization_id == organization_id))
        return query.all()

    def count_all(self) -> int:
        return self.db.query(CropMaster).count()

    def update(self, crop: CropMaster, data: dict) -> CropMaster:
        for key, value in data.items():
            if value is not None:
                setattr(crop, key, value)
        self.db.commit()
        self.db.refresh(crop)
        return crop

    def toggle_active(self, crop: CropMaster, is_active: bool) -> CropMaster:
        crop.is_active = is_active
        self.db.commit()
        self.db.refresh(crop)
        return crop
