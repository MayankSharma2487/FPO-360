from typing import Optional

from pydantic import BaseModel, EmailStr


class OrganizationSettingsBase(BaseModel):
    logo_url: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None


class OrganizationSettingsCreate(OrganizationSettingsBase):
    pass


class OrganizationSettingsUpdate(OrganizationSettingsBase):
    pass


class OrganizationSettingsResponse(OrganizationSettingsBase):
    id: int
    organization_id: int

    class Config:
        from_attributes = True