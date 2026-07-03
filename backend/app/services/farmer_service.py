from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.farmer import Farmer
from app.repositories.farmer_repository import FarmerRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.village_repository import VillageRepository
from app.schemas.farmer import FarmerCreate, FarmerUpdate


class FarmerService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = FarmerRepository(db)
        self.org_repo = OrganizationRepository(db)
        self.village_repo = VillageRepository(db)

    def _check_permission(self, current_user, target_org_id: int):
        if current_user.role.name == "Super Admin":
            return
        if current_user.organization_id != target_org_id:
            raise HTTPException(status_code=403, detail="Access denied to other organization")
        if current_user.role.name not in ["FPO Admin", "Manager"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")

    def create_farmer(self, payload: FarmerCreate, current_user) -> Farmer:
        if current_user.role.name != "Super Admin":
            payload.organization_id = current_user.organization_id

        if not payload.organization_id:
            raise HTTPException(status_code=400, detail="Organization ID required")

        org = self.org_repo.get_by_id(payload.organization_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        if payload.village_id:
            village = self.village_repo.get_by_id(payload.village_id)
            if not village or village.organization_id != payload.organization_id:
                raise HTTPException(status_code=400, detail="Invalid village for this organization")

        # Auto-generate farmer code
        if not payload.farmer_code or payload.farmer_code.strip() == "":
            existing = self.db.query(Farmer).filter(
                Farmer.organization_id == payload.organization_id
            ).order_by(Farmer.farmer_code.desc()).first()

            if existing and existing.farmer_code.startswith("FARM-"):
                try:
                    num = int(existing.farmer_code.split("-")[1]) + 1
                except:
                    num = 1
            else:
                num = 1
            payload.farmer_code = f"FARM-{num:05d}"

        new_farmer = Farmer(**payload.model_dump())
        return self.repo.create(new_farmer)

    def update_farmer(self, farmer_id: int, payload: FarmerUpdate, current_user) -> Farmer:
        farmer = self.repo.get_by_id(farmer_id)
        if not farmer:
            raise HTTPException(status_code=404, detail="Farmer not found")

        self._check_permission(current_user, farmer.organization_id)

        update_data = payload.model_dump(exclude_unset=True)
        return self.repo.update(farmer, update_data)

    def toggle_farmer_status(self, farmer_id: int, is_active: bool, current_user) -> Farmer:
        farmer = self.repo.get_by_id(farmer_id)
        if not farmer:
            raise HTTPException(status_code=404, detail="Farmer not found")
        self._check_permission(current_user, farmer.organization_id)
        return self.repo.toggle_active(farmer, is_active)

    def list_farmers(self, current_user):
        if current_user.role.name == "Super Admin":
            return self.repo.list_all()
        return self.repo.list_all(current_user.organization_id)