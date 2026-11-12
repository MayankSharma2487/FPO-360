from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging

from app.models.crop_master import CropMaster
from app.domain.item_catalogue import ItemType, BaseUnit
from app.services.item_service import ItemService
from app.repositories.crop_master_repository import CropMasterRepository
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.crop_master import CropMasterCreate, CropMasterUpdate

logger = logging.getLogger(__name__)


class CropMasterService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CropMasterRepository(db)
        self.org_repo = OrganizationRepository(db)

    def create_crop_master(self, payload: CropMasterCreate, current_user) -> CropMaster:
        try:
            # Validate crop code
            # Validate crop name
            crop_name = payload.crop_name
            if not crop_name or (isinstance(crop_name, str) and len(crop_name.strip()) == 0):
                raise HTTPException(status_code=400, detail="Crop name is required")
            
            crop_name = crop_name.strip() if isinstance(crop_name, str) else crop_name
            
            # Create new crop
            crop = CropMaster(
                crop_code=ItemService(self.db).generate_code(ItemType.AGRICULTURAL_COMMODITY),
                crop_name=crop_name,
                crop_category=payload.crop_category.strip() if payload.crop_category and isinstance(payload.crop_category, str) else payload.crop_category,
                unit=payload.unit.strip() if payload.unit and isinstance(payload.unit, str) else (payload.unit or "Kg"),
                item_type=ItemType.AGRICULTURAL_COMMODITY.value,
                organization_id=None,
                base_unit=BaseUnit.KG.value,
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

    def update_crop_master(self, crop_id: int, payload: CropMasterUpdate, current_user) -> CropMaster:
        try:
            crop = self.repo.get_visible(crop_id, current_user.organization_id if current_user.role.name != "Super Admin" else None, commodity_only=True)
            if not crop:
                raise HTTPException(status_code=404, detail="Crop not found")
            
            # Validate crop_name if provided
            if payload.crop_name:
                crop_name = payload.crop_name
                if isinstance(crop_name, str) and len(crop_name.strip()) == 0:
                    raise HTTPException(status_code=400, detail="Crop name cannot be empty")
            
            # Build update data
            update_data = payload.model_dump(exclude_unset=True)
            # Keep the legacy request field for compatibility, but item codes are immutable.
            update_data.pop("crop_code", None)
            
            # Clean up string fields
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

    def toggle_status(self, crop_id: int, is_active: bool, current_user) -> CropMaster:
        try:
            crop = self.repo.get_visible(crop_id, current_user.organization_id if current_user.role.name != "Super Admin" else None, commodity_only=True)
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

    def list_crop_masters(self, current_user):
        try:
            org_id = None if current_user.role.name == "Super Admin" else current_user.organization_id
            return self.repo.list_visible(org_id)
        except Exception as e:
            logger.error(f"Error listing crop masters: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to list crops: {str(e)}")
