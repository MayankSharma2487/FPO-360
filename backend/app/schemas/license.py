from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

LicenseStatus = Literal["Active", "Expired", "Pending", "Not Applicable"]


class LicenseFields(BaseModel):
    license_type: str = Field(min_length=1, max_length=100)
    license_number: str | None = Field(default=None, max_length=100)
    issuing_authority: str = Field(min_length=1, max_length=200)
    issue_date: date | None = None
    expiry_date: date | None = None
    status: LicenseStatus = "Active"
    renewal_date: date | None = None
    remarks: str | None = None
    document_reference: str | None = Field(default=None, max_length=500)

    @field_validator("license_type", "issuing_authority")
    @classmethod
    def required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Field cannot be blank")
        return value

    @field_validator("license_number", "remarks", "document_reference")
    @classmethod
    def optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @model_validator(mode="after")
    def valid_dates(self):
        validate_license_dates(self.issue_date, self.expiry_date, self.renewal_date)
        return self


def validate_license_dates(issue_date: date | None, expiry_date: date | None, renewal_date: date | None) -> None:
    if issue_date and expiry_date and expiry_date < issue_date:
        raise ValueError("expiry_date cannot be before issue_date")
    if issue_date and renewal_date and renewal_date < issue_date:
        raise ValueError("renewal_date cannot be before issue_date")


class LicenseCreate(LicenseFields):
    pass


class LicenseUpdate(BaseModel):
    license_type: str | None = Field(default=None, min_length=1, max_length=100)
    license_number: str | None = Field(default=None, max_length=100)
    issuing_authority: str | None = Field(default=None, min_length=1, max_length=200)
    issue_date: date | None = None
    expiry_date: date | None = None
    status: LicenseStatus | None = None
    renewal_date: date | None = None
    remarks: str | None = None
    document_reference: str | None = Field(default=None, max_length=500)

    @field_validator("license_type", "issuing_authority")
    @classmethod
    def nonblank_if_supplied(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Field cannot be blank")
        return value

    @field_validator("license_number", "remarks", "document_reference")
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class LicenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    created_by: int | None
    updated_by: int | None
    license_type: str
    license_number: str | None
    issuing_authority: str
    issue_date: date | None
    expiry_date: date | None
    status: LicenseStatus
    display_status: str
    expiring_soon: bool
    renewal_date: date | None
    remarks: str | None
    document_reference: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime | None
