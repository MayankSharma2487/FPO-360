from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.farmer_crop import FarmerCrop
from app.repositories.farmer_crop_repository import FarmerCropRepository
from app.repositories.farmer_repository import FarmerRepository
from app.repositories.crop_master_repository import CropMasterRepository
from app.schemas.farmer_crop import FarmerCropCreate, FarmerCropUpdate


class FarmerCropService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = FarmerCropRepository(db)
        self.farmer_repo = FarmerRepository(db)
        self.crop_repo = CropMasterRepository(db)

    def create_farmer_crop(self, payload: FarmerCropCreate, current_user) -> FarmerCrop:
        if current_user.role.name != "Super Admin":
            payload.organization_id = current_user.organization_id

        farmer = self.farmer_repo.get_by_id(payload.farmer_id)
        if not farmer or (current_user.role.name != "Super Admin" and farmer.organization_id != payload.organization_id):
            raise HTTPException(status_code=403, detail="Invalid farmer")

        crop = self.crop_repo.get_by_id(payload.crop_id)
        if not crop:
            raise HTTPException(status_code=404, detail="Crop not found")

        farmer_crop = FarmerCrop(**payload.model_dump())
        return self.repo.create(farmer_crop)

    def update_farmer_crop(self, record_id: int, payload: FarmerCropUpdate, current_user) -> FarmerCrop:
        record = self.repo.get_by_id(record_id)
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")
        if current_user.role.name != "Super Admin" and record.organization_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Access denied")
        update_data = payload.model_dump(exclude_unset=True)
        return self.repo.update(record, update_data)

    def toggle_status(self, record_id: int, is_active: bool, current_user) -> FarmerCrop:
        record = self.repo.get_by_id(record_id)
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")
        if current_user.role.name != "Super Admin" and record.organization_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Access denied")
        return self.repo.toggle_active(record, is_active)

    def list_farmer_crops(self, current_user):
        if current_user.role.name == "Super Admin":
            return self.repo.list_all()
        return self.repo.list_all(current_user.organization_id)