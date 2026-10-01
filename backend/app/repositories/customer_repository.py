from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.customer import Customer


class CustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, customer: Customer, commit: bool = True) -> Customer:
        self.db.add(customer)
        self.db.flush()
        if commit:
            self.db.commit()
            self.db.refresh(customer)
        return customer

    def get_by_id(self, customer_id: int) -> Optional[Customer]:
        return self.db.query(Customer).filter(Customer.id == customer_id).first()

    def get_latest_by_org(self, organization_id: int) -> Optional[Customer]:
        return (
            self.db.query(Customer)
            .filter(Customer.organization_id == organization_id)
            .order_by(Customer.id.desc())
            .first()
        )

    def list_all(self, organization_id: Optional[int] = None) -> List[Customer]:
        query = self.db.query(Customer).order_by(Customer.customer_name.asc())
        if organization_id is not None:
            query = query.filter(Customer.organization_id == organization_id)
        return query.all()

    def list_active(self, organization_id: Optional[int] = None) -> List[Customer]:
        """
        Return only active customers.
        organization_id=None → all orgs (Super Admin).
        organization_id set → scoped to that org.
        """
        query = (
            self.db.query(Customer)
            .filter(Customer.is_active.is_(True))
            .order_by(Customer.customer_name.asc())
        )
        if organization_id is not None:
            query = query.filter(Customer.organization_id == organization_id)
        return query.all()

    def update(self, customer: Customer, commit: bool = True) -> Customer:
        self.db.flush()
        if commit:
            self.db.commit()
            self.db.refresh(customer)
        return customer
