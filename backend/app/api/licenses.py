from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.database.database import get_db
from app.models.user import User
from app.schemas.license import LicenseCreate, LicenseOut, LicenseUpdate
from app.services.license_service import DEFAULT_EXPIRY_WARNING_DAYS, READ_ROLES, WRITE_ROLES, LicenseService

router = APIRouter(prefix="/licenses", tags=["Licenses"])


@router.get("", response_model=list[LicenseOut])
def list_licenses(
    status_filter: str | None = Query(default=None, alias="status", pattern="^(Active|Expired|Pending|Not Applicable|Expiring Soon)$"),
    license_type: str | None = Query(default=None, max_length=100),
    expiry_from: date | None = None,
    expiry_to: date | None = None,
    expiring_soon: bool | None = None,
    expiring_within_days: int = Query(default=DEFAULT_EXPIRY_WARNING_DAYS, ge=1, le=365),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*READ_ROLES)),
):
    return LicenseService(db).list_licenses(
        user,
        status_filter=status_filter,
        license_type=license_type,
        expiry_from=expiry_from,
        expiry_to=expiry_to,
        expiring_soon=expiring_soon,
        expiring_within_days=expiring_within_days,
    )


@router.post("", response_model=LicenseOut, status_code=status.HTTP_201_CREATED)
def create_license(
    payload: LicenseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*WRITE_ROLES)),
):
    return LicenseService(db).create_license(user, payload)


@router.get("/{license_id}", response_model=LicenseOut)
def get_license(
    license_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*READ_ROLES)),
):
    return LicenseService(db).get_license(user, license_id)


@router.put("/{license_id}", response_model=LicenseOut)
def update_license(
    license_id: int,
    payload: LicenseUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*WRITE_ROLES)),
):
    return LicenseService(db).update_license(user, license_id, payload)


@router.patch("/{license_id}/active", response_model=LicenseOut)
def set_license_active(
    license_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*WRITE_ROLES)),
):
    return LicenseService(db).set_active(user, license_id, is_active)


@router.delete("/{license_id}", response_model=LicenseOut)
def delete_license(
    license_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*WRITE_ROLES)),
):
    return LicenseService(db).delete_license(user, license_id)
