from datetime import date, timedelta

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models.license import License
from app.repositories.license_repository import LicenseRepository
from app.schemas.license import LicenseCreate, LicenseFields, LicenseOut, LicenseUpdate

READ_ROLES = {"Super Admin", "FPO Admin", "Manager", "Accountant", "Viewer"}
WRITE_ROLES = {"Super Admin", "FPO Admin", "Manager"}
DEFAULT_EXPIRY_WARNING_DAYS = 30


class LicenseService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = LicenseRepository(db)

    def _organization_id(self, user) -> int:
        organization_id = getattr(user, "organization_id", None)
        if organization_id is None:
            raise HTTPException(status_code=403, detail="License access requires an organization assignment")
        return organization_id

    def _require_writer(self, user) -> int:
        organization_id = self._organization_id(user)
        role_name = getattr(getattr(user, "role", None), "name", None)
        if role_name not in WRITE_ROLES:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return organization_id

    @staticmethod
    def _present(record: License, expiring_within_days: int = DEFAULT_EXPIRY_WARNING_DAYS) -> LicenseOut:
        today = date.today()
        expiring_soon = bool(
            record.status == "Active"
            and record.expiry_date is not None
            and today <= record.expiry_date <= today + timedelta(days=expiring_within_days)
        )
        display_status = record.status
        if record.status == "Active" and record.expiry_date is not None and record.expiry_date < today:
            display_status = "Expired"
        values = {column.name: getattr(record, column.name) for column in License.__table__.columns}
        values.update(display_status=display_status, expiring_soon=expiring_soon)
        return LicenseOut.model_validate(values)

    def list_licenses(
        self,
        user,
        *,
        status_filter: str | None = None,
        license_type: str | None = None,
        expiry_from: date | None = None,
        expiry_to: date | None = None,
        expiring_soon: bool | None = None,
        expiring_within_days: int = DEFAULT_EXPIRY_WARNING_DAYS,
    ):
        organization_id = self._organization_id(user)
        if expiry_from and expiry_to and expiry_from > expiry_to:
            raise HTTPException(status_code=400, detail="expiry_from cannot be after expiry_to")
        records = self.repo.list_for_organization(
            organization_id,
            status=status_filter,
            license_type=license_type,
            expiry_from=expiry_from,
            expiry_to=expiry_to,
            expiring_soon=expiring_soon,
            expiring_within_days=expiring_within_days,
        )
        return [self._present(record, expiring_within_days) for record in records]

    def get_license(self, user, license_id: int) -> LicenseOut:
        record = self.repo.get_for_organization(self._organization_id(user), license_id)
        if not record:
            raise HTTPException(status_code=404, detail="License not found")
        return self._present(record)

    def create_license(self, user, payload: LicenseCreate) -> LicenseOut:
        organization_id = self._require_writer(user)
        record = License(organization_id=organization_id, created_by=getattr(user, "id", None), **payload.model_dump())
        return self._present(self.repo.create(record))

    def update_license(self, user, license_id: int, payload: LicenseUpdate) -> LicenseOut:
        organization_id = self._require_writer(user)
        record = self.repo.get_for_organization(organization_id, license_id)
        if not record:
            raise HTTPException(status_code=404, detail="License not found")
        changes = payload.model_dump(exclude_unset=True)
        changes["updated_by"] = getattr(user, "id", None)
        current = {column.name: getattr(record, column.name) for column in License.__table__.columns}
        proposed = {key: current[key] for key in (
            "license_type", "license_number", "issuing_authority", "issue_date", "expiry_date",
            "status", "renewal_date", "remarks", "document_reference",
        )}
        proposed.update(changes)
        try:
            LicenseFields.model_validate(proposed)
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=exc.errors()[0]["msg"]) from exc
        updated = self.repo.update(record, changes)
        return self._present(updated)

    def set_active(self, user, license_id: int, is_active: bool) -> LicenseOut:
        organization_id = self._require_writer(user)
        record = self.repo.get_for_organization(organization_id, license_id)
        if not record:
            raise HTTPException(status_code=404, detail="License not found")
        record.updated_by = getattr(user, "id", None)
        return self._present(self.repo.set_active(record, is_active))

    def delete_license(self, user, license_id: int) -> LicenseOut:
        return self.set_active(user, license_id, False)
