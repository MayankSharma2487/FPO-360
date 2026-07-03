from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.organization import Organization


class OrganizationRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, organization: Organization) -> Organization:
        self.db.add(organization)
        self.db.commit()
        self.db.refresh(organization)

        return organization

    def get_by_id(self, organization_id: int) -> Optional[Organization]:
        return (
            self.db.query(Organization)
            .filter(Organization.id == organization_id)
            .first()
        )

    def get_by_registration_number(
        self,
        registration_number: str
    ) -> Optional[Organization]:
        return (
            self.db.query(Organization)
            .filter(Organization.registration_number == registration_number)
            .first()
        )

    def list_all(self) -> List[Organization]:
        return self.db.query(Organization).all()

    def count_all(self) -> int:
        return self.db.query(Organization).count()

    def update(self, organization: Organization, data: dict) -> Organization:
        for key, value in data.items():
            setattr(organization, key, value)

        self.db.commit()
        self.db.refresh(organization)

        return organization