from typing import Optional

from pydantic import BaseModel, Field


class OrganizationCreate(BaseModel):
    organization_name: str = Field(..., min_length=2, max_length=255)
    registration_number: str = Field(..., min_length=2, max_length=100)
    pan_number: Optional[str] = None
    gst_number: Optional[str] = None
    fssai_number: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None


class OrganizationUpdate(BaseModel):
    organization_name: Optional[str] = Field(None, min_length=2, max_length=255)
    registration_number: Optional[str] = Field(None, min_length=2, max_length=100)
    pan_number: Optional[str] = None
    gst_number: Optional[str] = None
    fssai_number: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None


class OrganizationResponse(BaseModel):
    id: int
    organization_name: str
    registration_number: str
    pan_number: Optional[str] = None
    gst_number: Optional[str] = None
    fssai_number: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None

    class Config:
        from_attributes = True