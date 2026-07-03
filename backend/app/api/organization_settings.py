from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.organization_settings import (
    OrganizationSettingsUpdate,
    OrganizationSettingsResponse
)
from app.services.organization_settings_service import OrganizationSettingsService
from app.auth.dependencies import get_current_user, require_roles
from app.models.user import User

router = APIRouter(
    prefix="/organizations",
    tags=["Organization Settings"]
)


@router.get(
    "/{organization_id}/settings",
    response_model=OrganizationSettingsResponse
)
def get_organization_settings(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = OrganizationSettingsService(db)

    return service.get_settings(organization_id)


@router.put(
    "/{organization_id}/settings",
    response_model=OrganizationSettingsResponse
)
def update_organization_settings(
    organization_id: int,
    payload: OrganizationSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin"))
):
    service = OrganizationSettingsService(db)

    return service.upsert_settings(organization_id, payload)