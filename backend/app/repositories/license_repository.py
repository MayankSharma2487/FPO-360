from datetime import date, timedelta

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.license import License


class LicenseRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_for_organization(
        self,
        organization_id: int,
        *,
        status: str | None = None,
        license_type: str | None = None,
        expiry_from: date | None = None,
        expiry_to: date | None = None,
        expiring_soon: bool | None = None,
        expiring_within_days: int = 30,
    ):
        today = date.today()
        soon_end = today + timedelta(days=expiring_within_days)
        query = self.db.query(License).filter(License.organization_id == organization_id)
        if license_type:
            query = query.filter(License.license_type.ilike(f"%{license_type.strip()}%"))
        if expiry_from:
            query = query.filter(License.expiry_date >= expiry_from)
        if expiry_to:
            query = query.filter(License.expiry_date <= expiry_to)

        upcoming = and_(License.status == "Active", License.expiry_date >= today, License.expiry_date <= soon_end)
        if status == "Expiring Soon":
            query = query.filter(upcoming)
        elif status == "Expired":
            query = query.filter(or_(License.status == "Expired", and_(License.status == "Active", License.expiry_date < today)))
        elif status == "Active":
            query = query.filter(License.status == "Active", or_(License.expiry_date.is_(None), License.expiry_date >= today))
        elif status:
            query = query.filter(License.status == status)

        if expiring_soon is True:
            query = query.filter(upcoming)
        elif expiring_soon is False:
            query = query.filter(or_(
                License.status != "Active",
                License.expiry_date.is_(None),
                License.expiry_date < today,
                License.expiry_date > soon_end,
            ))
        return query.order_by(License.expiry_date.asc().nullslast(), License.license_type.asc(), License.id.asc()).all()

    def get_for_organization(self, organization_id: int, license_id: int):
        return self.db.query(License).filter(
            License.organization_id == organization_id,
            License.id == license_id,
        ).first()

    def create(self, license_record: License) -> License:
        self.db.add(license_record)
        self.db.commit()
        self.db.refresh(license_record)
        return license_record

    def update(self, license_record: License, values: dict) -> License:
        for key, value in values.items():
            setattr(license_record, key, value)
        self.db.commit()
        self.db.refresh(license_record)
        return license_record

    def set_active(self, license_record: License, is_active: bool) -> License:
        license_record.is_active = is_active
        self.db.commit()
        self.db.refresh(license_record)
        return license_record
