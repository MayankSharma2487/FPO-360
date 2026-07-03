from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.village import Village
from app.repositories.village_repository import VillageRepository
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.village import VillageCreate, VillageUpdate


class VillageService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = VillageRepository(db)
        self.org_repo = OrganizationRepository(db)

    def _check_permission(self, current_user, target_org_id: int):
        if current_user.role.name == "Super Admin":
            return
        if current_user.organization_id != target_org_id:
            raise HTTPException(status_code=403, detail="Access denied to other organization")
        if current_user.role.name not in ["FPO Admin", "Manager"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")

    def create_village(self, payload: VillageCreate, current_user) -> Village:
        if current_user.role.name != "Super Admin":
            payload.organization_id = current_user.organization_id

        if not payload.organization_id:
            raise HTTPException(status_code=400, detail="Organization ID required")

        org = self.org_repo.get_by_id(payload.organization_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        existing = self.repo.get_by_code(payload.village_code)
        if existing:
            raise HTTPException(status_code=400, detail="Village code already exists")

        new_village = Village(**payload.model_dump())
        return self.repo.create(new_village)

    def update_village(self, village_id: int, payload: VillageUpdate, current_user) -> Village:
        village = self.repo.get_by_id(village_id)
        if not village:
            raise HTTPException(status_code=404, detail="Village not found")

        self._check_permission(current_user, village.organization_id)
        update_data = payload.model_dump(exclude_unset=True)
        return self.repo.update(village, update_data)

    def toggle_village_status(self, village_id: int, is_active: bool, current_user) -> Village:
        village = self.repo.get_by_id(village_id)
        if not village:
            raise HTTPException(status_code=404, detail="Village not found")
        self._check_permission(current_user, village.organization_id)
        return self.repo.toggle_active(village, is_active)

    def list_villages(self, current_user):
        if current_user.role.name == "Super Admin":
            return self.repo.list_all()
        return self.repo.list_all(current_user.organization_id)
    def create_village(self, payload: VillageCreate, current_user) -> Village:
        if current_user.role.name != "Super Admin":
            payload.organization_id = current_user.organization_id

        if not payload.organization_id:
            raise HTTPException(status_code=400, detail="Organization ID required")

        org = self.org_repo.get_by_id(payload.organization_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        # Auto-generate village code if not provided
        if not payload.village_code or payload.village_code.strip() == "":
            # Find highest existing code for this org
            existing = self.db.query(Village).filter(
                Village.organization_id == payload.organization_id
            ).order_by(Village.village_code.desc()).first()

            if existing and existing.village_code.startswith("VIL-"):
                try:
                    num = int(existing.village_code.split("-")[1]) + 1
                except:
                    num = 1
            else:
                num = 1
            payload.village_code = f"VIL-{num:05d}"

        existing = self.repo.get_by_code(payload.village_code)
        if existing:
            raise HTTPException(status_code=400, detail="Village code already exists")

        new_village = Village(**payload.model_dump())
        return self.repo.create(new_village)