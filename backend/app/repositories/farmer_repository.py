from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.farmer import Farmer


class FarmerRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, farmer: Farmer) -> Farmer:
        self.db.add(farmer)
        self.db.commit()
        self.db.refresh(farmer)
        return farmer

    def get_by_id(self, farmer_id: int) -> Optional[Farmer]:
        return self.db.query(Farmer).filter(Farmer.id == farmer_id).first()

    def get_by_code(self, farmer_code: str) -> Optional[Farmer]:
        return self.db.query(Farmer).filter(Farmer.farmer_code == farmer_code).first()

    def list_all(self, organization_id: Optional[int] = None) -> List[Farmer]:
        query = self.db.query(Farmer)
        if organization_id is not None:
            query = query.filter(Farmer.organization_id == organization_id)
        return query.all()

    def count_all(self) -> int:
        return self.db.query(Farmer).count()

    def count_active(self) -> int:
        return self.db.query(Farmer).filter(Farmer.is_active == True).count()

    def count_by_organization(self, organization_id: int) -> int:
        return self.db.query(Farmer).filter(
            Farmer.organization_id == organization_id
        ).count()

    def count_active_by_organization(self, organization_id: int) -> int:
        return self.db.query(Farmer).filter(
            Farmer.organization_id == organization_id,
            Farmer.is_active == True
        ).count()

    def count_shareholders(self) -> int:
        return self.db.query(Farmer).filter(
            Farmer.is_shareholder == True,
            Farmer.is_active == True
        ).count()

    def update(self, farmer: Farmer, data: dict) -> Farmer:
        for key, value in data.items():
            if value is not None:
                setattr(farmer, key, value)
        self.db.commit()
        self.db.refresh(farmer)
        return farmer

    def toggle_active(self, farmer: Farmer, is_active: bool) -> Farmer:
        farmer.is_active = is_active
        self.db.commit()
        self.db.refresh(farmer)
        return farmer