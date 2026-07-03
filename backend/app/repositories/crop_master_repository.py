from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.crop_master import CropMaster


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