from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.crop_master import CropMaster


class ItemRepository:
    """Catalogue queries over the existing CropMaster table."""

    def __init__(self, db: Session):
        self.db = db

    def visible_query(self, organization_id: Optional[int]):
        query = self.db.query(CropMaster)
        if organization_id is not None:
            query = query.filter(or_(CropMaster.organization_id.is_(None), CropMaster.organization_id == organization_id))
        return query

    def list(self, organization_id, search=None, item_type=None, is_active=None):
        query = self.visible_query(organization_id)
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(or_(CropMaster.crop_name.ilike(pattern), CropMaster.crop_code.ilike(pattern)))
        if item_type:
            query = query.filter(CropMaster.item_type == item_type)
        if is_active is not None:
            query = query.filter(CropMaster.is_active.is_(is_active))
        return query.order_by(CropMaster.crop_name, CropMaster.id).all()

    def get_visible(self, item_id, organization_id):
        return self.visible_query(organization_id).filter(CropMaster.id == item_id).first()

    def get_visible_for_update(self, item_id, organization_id):
        return self.visible_query(organization_id).filter(
            CropMaster.id == item_id
        ).with_for_update().populate_existing().first()
