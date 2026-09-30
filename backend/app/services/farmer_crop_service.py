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
        """
        List farmer crops with farmer and crop names populated
        """
        if current_user.role.name == "Super Admin":
            farmer_crops = self.repo.list_all()
        else:
            farmer_crops = self.repo.list_all(current_user.organization_id)

        result = []
        for fc in farmer_crops:
            data = {
                "id": fc.id,
                "farmer_id": fc.farmer_id,
                "crop_id": fc.crop_id,
                "organization_id": fc.organization_id,
                "season": fc.season,
                "year": fc.year,
                "area_acres": fc.area_acres,
                "sowing_date": fc.sowing_date,
                "harvest_date": fc.harvest_date,
                "expected_yield": fc.expected_yield,
                "actual_yield": fc.actual_yield,
                "remarks": fc.remarks,
                "is_active": fc.is_active,
                "created_at": fc.created_at,
                "updated_at": fc.updated_at,
                
                # Populate farmer and crop names
                "farmer_name": fc.farmer.farmer_name if fc.farmer else "—",
                "crop_name": fc.crop.crop_name if fc.crop else "—",
            }
            result.append(data)
        return result