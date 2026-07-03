from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.village import Village


class VillageRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, village: Village) -> Village:
        self.db.add(village)
        self.db.commit()
        self.db.refresh(village)
        return village

    def get_by_id(self, village_id: int) -> Optional[Village]:
        return self.db.query(Village).filter(Village.id == village_id).first()

    def get_by_code(self, village_code: str) -> Optional[Village]:
        return self.db.query(Village).filter(Village.village_code == village_code).first()

    def list_all(self, organization_id: Optional[int] = None) -> List[Village]:
        query = self.db.query(Village)
        if organization_id is not None:
            query = query.filter(Village.organization_id == organization_id)
        return query.all()

    def count_all(self) -> int:
        return self.db.query(Village).count()

    def count_active(self) -> int:
        return self.db.query(Village).filter(Village.is_active == True).count()

    def count_by_organization(self, organization_id: int) -> int:
        return self.db.query(Village).filter(
            Village.organization_id == organization_id
        ).count()

    def count_active_by_organization(self, organization_id: int) -> int:
        return self.db.query(Village).filter(
            Village.organization_id == organization_id,
            Village.is_active == True
        ).count()

    def update(self, village: Village, data: dict) -> Village:
        for key, value in data.items():
            if value is not None:
                setattr(village, key, value)
        self.db.commit()
        self.db.refresh(village)
        return village

    def toggle_active(self, village: Village, is_active: bool) -> Village:
        village.is_active = is_active
        self.db.commit()
        self.db.refresh(village)
        return village