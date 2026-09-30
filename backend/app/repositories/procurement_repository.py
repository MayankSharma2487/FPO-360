from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, select, and_, or_

from app.models.procurement import Procurement



class ProcurementRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, procurement: Procurement, commit: bool = True) -> Procurement:
        self.db.add(procurement)
        self.db.flush()

        if commit:
            self.db.commit()
            self.db.refresh(procurement)

        return procurement

    def get_by_id(self, procurement_id: int) -> Optional[Procurement]:
        return self.db.query(Procurement).options(
            joinedload(Procurement.farmer),
            joinedload(Procurement.crop)
        ).filter(Procurement.id == procurement_id).first()
    def get_latest_by_org(self, organization_id: int) -> Optional[Procurement]:
        return (
            self.db.query(Procurement)
            .filter(Procurement.organization_id == organization_id)
            .order_by(Procurement.id.desc())
            .first()
        )

    def get_by_procurement_no(self, procurement_no: str) -> Optional[Procurement]:
        return self.db.query(Procurement).filter(Procurement.procurement_no == procurement_no).first()

    def list_all(self, organization_id: Optional[int] = None, filters: dict = None) -> List[Procurement]:
        query = self.db.query(Procurement).options(
            joinedload(Procurement.farmer),
            joinedload(Procurement.crop)
        ).order_by(Procurement.procurement_date.desc(), Procurement.id.desc())

        if organization_id is not None:
            query = query.filter(Procurement.organization_id == organization_id)

        if filters:
            if filters.get('farmer_id'):
                query = query.filter(Procurement.farmer_id == filters['farmer_id'])
            if filters.get('crop_id'):
                query = query.filter(Procurement.crop_id == filters['crop_id'])
            if filters.get('from_date'):
                query = query.filter(Procurement.procurement_date >= filters['from_date'])
            if filters.get('to_date'):
                query = query.filter(Procurement.procurement_date <= filters['to_date'])
            if filters.get('quality_grade'):
                query = query.filter(Procurement.quality_grade == filters['quality_grade'])

        return query.all()

    def exists_duplicate(self, farmer_id: int, crop_id: int, procurement_date: date, exclude_id: Optional[int] = None) -> bool:
        query = self.db.query(Procurement).filter(
            Procurement.farmer_id == farmer_id,
            Procurement.crop_id == crop_id,
            func.date(Procurement.procurement_date) == procurement_date
        )
        if exclude_id:
            query = query.filter(Procurement.id != exclude_id)
        return query.first() is not None

    def count_all(self) -> int:
        return self.db.query(Procurement).count()

    def count_by_organization(self, organization_id: int) -> int:
        return self.db.query(Procurement).filter(Procurement.organization_id == organization_id).count()

    def total_quantity(self) -> float:
        result = self.db.scalar(select(func.sum(Procurement.quantity)))
        return float(result) if result else 0.0

    def total_quantity_by_org(self, organization_id: int) -> float:
        result = self.db.scalar(select(func.sum(Procurement.quantity)).where(Procurement.organization_id == organization_id))
        return float(result) if result else 0.0

    def total_value(self) -> float:
        result = self.db.scalar(select(func.sum(Procurement.total_amount)))
        return float(result) if result else 0.0

    def total_value_by_org(self, organization_id: int) -> float:
        result = self.db.scalar(select(func.sum(Procurement.total_amount)).where(Procurement.organization_id == organization_id))
        return float(result) if result else 0.0

    def update(self, procurement: Procurement, commit: bool = True) -> Procurement:
        self.db.flush()

        if commit:
            self.db.commit()
            self.db.refresh(procurement)

        return procurement

    def toggle_active(
        self,
        procurement: Procurement,
        is_active: bool,
        commit: bool = True
    ) -> Procurement:
        procurement.is_active = is_active
        self.db.flush()

        if commit:
            self.db.commit()
            self.db.refresh(procurement)

        return procurement

    def commit(self):
        self.db.commit()


    def rollback(self):
        self.db.rollback()