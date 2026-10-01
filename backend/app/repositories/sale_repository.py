from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from app.models.sale import Sale


class SaleRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, sale: Sale, commit: bool = True) -> Sale:
        self.db.add(sale)
        self.db.flush()
        if commit:
            self.db.commit()
            self.db.refresh(sale)
        return sale

    def get_by_id(self, sale_id: int) -> Optional[Sale]:
        return (
            self.db.query(Sale)
            .options(joinedload(Sale.customer), joinedload(Sale.crop))
            .filter(Sale.id == sale_id)
            .first()
        )

    def get_latest_by_org(self, organization_id: int) -> Optional[Sale]:
        return (
            self.db.query(Sale)
            .filter(Sale.organization_id == organization_id)
            .order_by(Sale.id.desc())
            .first()
        )

    def list_all(self, organization_id: Optional[int] = None) -> List[Sale]:
        query = (
            self.db.query(Sale)
            .options(joinedload(Sale.customer), joinedload(Sale.crop))
            .order_by(Sale.sale_date.desc(), Sale.id.desc())
        )
        if organization_id is not None:
            query = query.filter(Sale.organization_id == organization_id)
        return query.all()

    def update(self, sale: Sale, commit: bool = True) -> Sale:
        self.db.flush()
        if commit:
            self.db.commit()
            self.db.refresh(sale)
        return sale

    def commit(self):
        self.db.commit()

    def rollback(self):
        self.db.rollback()
