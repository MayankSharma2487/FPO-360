from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, select

from app.models.farmer_crop import FarmerCrop


class FarmerCropRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, farmer_crop: FarmerCrop) -> FarmerCrop:
        self.db.add(farmer_crop)
        self.db.commit()
        self.db.refresh(farmer_crop)
        return farmer_crop

    def get_by_id(self, record_id: int) -> Optional[FarmerCrop]:
        return self.db.query(FarmerCrop).options(
            joinedload(FarmerCrop.farmer),
            joinedload(FarmerCrop.crop)
        ).filter(FarmerCrop.id == record_id).first()

    def list_all(self, organization_id: Optional[int] = None) -> List[FarmerCrop]:
        query = self.db.query(FarmerCrop).options(
            joinedload(FarmerCrop.farmer),
            joinedload(FarmerCrop.crop)
        )
        if organization_id is not None:
            query = query.filter(FarmerCrop.organization_id == organization_id)
        return query.all()

    def count_all(self) -> int:
        return self.db.query(FarmerCrop).count()

    def count_by_organization(self, organization_id: int) -> int:
        return self.db.query(FarmerCrop).filter(
            FarmerCrop.organization_id == organization_id
        ).count()

    def total_acreage(self) -> Optional[float]:
        result = self.db.scalar(select(func.sum(FarmerCrop.area_acres)))
        return float(result) if result else 0.0

    def total_acreage_by_org(self, organization_id: int) -> Optional[float]:
        result = self.db.scalar(
            select(func.sum(FarmerCrop.area_acres)).filter(FarmerCrop.organization_id == organization_id)
        )
        return float(result) if result else 0.0

    def total_expected_yield(self) -> Optional[float]:
        result = self.db.scalar(select(func.sum(FarmerCrop.expected_yield)))
        return float(result) if result else 0.0

    def total_actual_yield(self) -> Optional[float]:
        result = self.db.scalar(select(func.sum(FarmerCrop.actual_yield)))
        return float(result) if result else 0.0

    def update(self, farmer_crop: FarmerCrop, data: dict) -> FarmerCrop:
        for key, value in data.items():
            if value is not None:
                setattr(farmer_crop, key, value)
        self.db.commit()
        self.db.refresh(farmer_crop)
        return farmer_crop

    def toggle_active(self, farmer_crop: FarmerCrop, is_active: bool) -> FarmerCrop:
        farmer_crop.is_active = is_active
        self.db.commit()
        self.db.refresh(farmer_crop)
        return farmer_crop