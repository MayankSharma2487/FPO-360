from typing import Optional

from sqlalchemy.orm import Session

from app.models.organization_settings import OrganizationSettings


class OrganizationSettingsRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_organization_id(
        self,
        organization_id: int
    ) -> Optional[OrganizationSettings]:
        return (
            self.db.query(OrganizationSettings)
            .filter(OrganizationSettings.organization_id == organization_id)
            .first()
        )

    def create(self, settings: OrganizationSettings) -> OrganizationSettings:
        self.db.add(settings)
        self.db.commit()
        self.db.refresh(settings)

        return settings

    def update(
        self,
        settings: OrganizationSettings,
        data: dict
    ) -> OrganizationSettings:

        for key, value in data.items():
            setattr(settings, key, value)

        self.db.commit()
        self.db.refresh(settings)

        return settings