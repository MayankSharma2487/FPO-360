from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse
)
from app.services.organization_service import OrganizationService
from app.auth.dependencies import get_current_user, require_roles
from app.models.user import User

router = APIRouter(
    prefix="/organizations",
    tags=["Organizations"]
)


@router.post(
    "/",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED
)
def create_organization(
    organization: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin"))
):
    service = OrganizationService(db)
    return service.create_organization(organization)


@router.get("/", response_model=list[OrganizationResponse])
def get_organizations(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin"))
):
    service = OrganizationService(db)
    return service.list_organizations()


@router.get("/{organization_id}", response_model=OrganizationResponse)
def get_organization(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = OrganizationService(db)
    org = service.get_organization(organization_id)

    if current_user.role.name != "Super Admin" and org.id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied to organization")

    return org


@router.put("/{organization_id}", response_model=OrganizationResponse)
def update_organization(
    organization_id: int,
    organization: OrganizationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin"))
):
    service = OrganizationService(db)
    return service.update_organization(organization_id, organization)


# No delete endpoint - organizations are critical, use soft delete if needed in future