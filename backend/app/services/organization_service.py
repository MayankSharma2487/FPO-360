from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.organization import OrganizationCreate, OrganizationUpdate


class OrganizationService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = OrganizationRepository(db)

    def create_organization(self, payload: OrganizationCreate) -> Organization:

        existing = self.repo.get_by_registration_number(
            payload.registration_number
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization with this registration number already exists"
            )

        organization = Organization(**payload.model_dump())

        return self.repo.create(organization)

    def get_organization(self, organization_id: int) -> Organization:

        organization = self.repo.get_by_id(organization_id)

        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )

        return organization

    def list_organizations(self):
        return self.repo.list_all()

    def update_organization(
        self,
        organization_id: int,
        payload: OrganizationUpdate
    ) -> Organization:

        organization = self.get_organization(organization_id)

        update_data = payload.model_dump(exclude_unset=True)

        if "registration_number" in update_data:
            existing = self.repo.get_by_registration_number(
                update_data["registration_number"]
            )

            if existing and existing.id != organization_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Organization with this registration number already exists"
                )

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided for update"
            )

        return self.repo.update(organization, update_data)