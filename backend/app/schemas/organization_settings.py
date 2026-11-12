from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class OrganizationSettingsBase(BaseModel):
    logo_url: Optional[str] = Field(None, max_length=500)
    address: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=255)


class OrganizationSettingsCreate(OrganizationSettingsBase):
    pass


class OrganizationSettingsUpdate(OrganizationSettingsBase):
    pass


class OrganizationSettingsResponse(OrganizationSettingsBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
