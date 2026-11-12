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

    @staticmethod
    def _authorize_organization(organization_id: int, current_user) -> None:
        if current_user.role.name != "Super Admin" and current_user.organization_id != organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to organization settings",
            )

    def get_settings(self, organization_id: int, current_user) -> OrganizationSettings:

        self._authorize_organization(organization_id, current_user)

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
        payload: OrganizationSettingsUpdate,
        current_user,
    ) -> OrganizationSettings:

        self._authorize_organization(organization_id, current_user)
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
