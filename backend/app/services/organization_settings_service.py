from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.organization_settings import OrganizationSettings
from app.repositories.organization_settings_repository import (
    OrganizationSettingsRepository
)
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.organization_settings import OrganizationSettingsUpdate


class OrganizationSettingsService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = OrganizationSettingsRepository(db)
        self.organization_repo = OrganizationRepository(db)

    def _ensure_organization_exists(self, organization_id: int):

        organization = self.organization_repo.get_by_id(organization_id)

        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )

        return organization

    def get_settings(self, organization_id: int) -> OrganizationSettings:

        self._ensure_organization_exists(organization_id)

        settings = self.repo.get_by_organization_id(organization_id)

        if not settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization settings not found"
            )

        return settings

    def upsert_settings(
        self,
        organization_id: int,
        payload: OrganizationSettingsUpdate
    ) -> OrganizationSettings:

        self._ensure_organization_exists(organization_id)

        settings = self.repo.get_by_organization_id(organization_id)
        update_data = payload.model_dump(exclude_unset=True)

        if settings:
            return self.repo.update(settings, update_data)

        settings = OrganizationSettings(
            organization_id=organization_id,
            **payload.model_dump()
        )

        return self.repo.create(settings)