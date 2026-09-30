from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging

from app.models.crop_master import CropMaster
from app.repositories.crop_master_repository import CropMasterRepository
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.crop_master import CropMasterCreate, CropMasterUpdate

logger = logging.getLogger(__name__)


class CropMasterService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CropMasterRepository(db)
        self.org_repo = OrganizationRepository(db)

    def create_crop_master(self, payload: CropMasterCreate) -> CropMaster:
        try:
            # Validate crop code
            crop_code = payload.crop_code
            if not crop_code or (isinstance(crop_code, str) and len(crop_code.strip()) == 0):
                raise HTTPException(status_code=400, detail="Crop code is required")
            
            crop_code = crop_code.strip() if isinstance(crop_code, str) else crop_code
            
            # Validate crop name
            crop_name = payload.crop_name
            if not crop_name or (isinstance(crop_name, str) and len(crop_name.strip()) == 0):
                raise HTTPException(status_code=400, detail="Crop name is required")
            
            crop_name = crop_name.strip() if isinstance(crop_name, str) else crop_name
            
            # Check for duplicate crop code
            existing = self.repo.get_by_code(crop_code)
            if existing:
                raise HTTPException(status_code=400, detail=f"Crop code '{crop_code}' already exists")
            
            # Create new crop
            crop = CropMaster(
                crop_code=crop_code,
                crop_name=crop_name,
                crop_category=payload.crop_category.strip() if payload.crop_category and isinstance(payload.crop_category, str) else payload.crop_category,
                unit=payload.unit.strip() if payload.unit and isinstance(payload.unit, str) else (payload.unit or "Kg"),
                is_active=True
            )
            
            created_crop = self.repo.create(crop)
            self.db.commit()
            return created_crop
            
        except HTTPException:
            self.db.rollback()
            raise
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Database integrity error creating crop: {str(e)}")
            raise HTTPException(status_code=400, detail="Crop code must be unique")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating crop: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create crop: {str(e)}")

    def update_crop_master(self, crop_id: int, payload: CropMasterUpdate) -> CropMaster:
        try:
            crop = self.repo.get_by_id(crop_id)
            if not crop:
                raise HTTPException(status_code=404, detail="Crop not found")
            
            # If crop_code is being changed, check for duplicates
            if payload.crop_code:
                crop_code = payload.crop_code
                if isinstance(crop_code, str):
                    crop_code = crop_code.strip()
                
                if not crop_code:
                    raise HTTPException(status_code=400, detail="Crop code cannot be empty")
                
                existing = self.repo.get_by_code(crop_code)
                if existing and existing.id != crop_id:
                    raise HTTPException(status_code=400, detail=f"Crop code '{crop_code}' already exists")
            
            # Validate crop_name if provided
            if payload.crop_name:
                crop_name = payload.crop_name
                if isinstance(crop_name, str) and len(crop_name.strip()) == 0:
                    raise HTTPException(status_code=400, detail="Crop name cannot be empty")
            
            # Build update data
            update_data = payload.model_dump(exclude_unset=True)
            
            # Clean up string fields
            if 'crop_code' in update_data and update_data['crop_code']:
                update_data['crop_code'] = update_data['crop_code'].strip() if isinstance(update_data['crop_code'], str) else update_data['crop_code']
            
            if 'crop_name' in update_data and update_data['crop_name']:
                update_data['crop_name'] = update_data['crop_name'].strip() if isinstance(update_data['crop_name'], str) else update_data['crop_name']
            
            if 'crop_category' in update_data and update_data['crop_category']:
                update_data['crop_category'] = update_data['crop_category'].strip() if isinstance(update_data['crop_category'], str) else update_data['crop_category']
            
            if 'unit' in update_data and update_data['unit']:
                update_data['unit'] = update_data['unit'].strip() if isinstance(update_data['unit'], str) else update_data['unit']
            
            updated_crop = self.repo.update(crop, update_data)
            self.db.commit()
            return updated_crop
            
        except HTTPException:
            self.db.rollback()
            raise
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Database integrity error updating crop: {str(e)}")
            raise HTTPException(status_code=400, detail="Crop code must be unique")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating crop: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to update crop: {str(e)}")

    def toggle_status(self, crop_id: int, is_active: bool) -> CropMaster:
        try:
            crop = self.repo.get_by_id(crop_id)
            if not crop:
                raise HTTPException(status_code=404, detail="Crop not found")
            
            result = self.repo.toggle_active(crop, is_active)
            self.db.commit()
            return result
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error toggling crop status: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to toggle crop status: {str(e)}")

    def list_crop_masters(self):
        try:
            return self.repo.list_all()
        except Exception as e:
            logger.error(f"Error listing crop masters: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to list crops: {str(e)}")