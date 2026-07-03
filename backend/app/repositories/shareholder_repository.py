from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from app.models.shareholder import Shareholder


class ShareholderRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, shareholder: Shareholder) -> Shareholder:
        self.db.add(shareholder)
        self.db.commit()
        self.db.refresh(shareholder)
        return shareholder

    def get_by_id(self, shareholder_id: int) -> Optional[Shareholder]:
        return self.db.query(Shareholder).filter(Shareholder.id == shareholder_id).first()

    def get_by_farmer(self, farmer_id: int) -> Optional[Shareholder]:
        return self.db.query(Shareholder).filter(Shareholder.farmer_id == farmer_id).first()
    
    def list_all(self, organization_id: Optional[int] = None) -> List[Shareholder]:
        query = self.db.query(Shareholder).options(
            joinedload(Shareholder.farmer)
        )
        if organization_id is not None:
            query = query.filter(Shareholder.organization_id == organization_id)
        return query.all()

    def count_all(self) -> int:
        return self.db.query(Shareholder).count()

    def count_active(self) -> int:
        return self.db.query(Shareholder).filter(Shareholder.is_active == True).count()

    # ← ADD THIS METHOD
    def count_by_organization(self, organization_id: int) -> int:
        return self.db.query(Shareholder).filter(
            Shareholder.organization_id == organization_id
        ).count()

    def update(self, shareholder: Shareholder, data: dict) -> Shareholder:
        for key, value in data.items():
            if value is not None:
                setattr(shareholder, key, value)
        self.db.commit()
        self.db.refresh(shareholder)
        return shareholder

    def toggle_active(self, shareholder: Shareholder, is_active: bool) -> Shareholder:
        shareholder.is_active = is_active
        self.db.commit()
        self.db.refresh(shareholder)
        return shareholder