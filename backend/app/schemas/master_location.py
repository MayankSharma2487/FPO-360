from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class MasterStateResponse(BaseModel):
    id: int
    state_name: str
    state_code: Optional[str] = None

    class Config:
        from_attributes = True


class MasterDistrictResponse(BaseModel):
    id: int
    district_name: str
    state_id: int

    class Config:
        from_attributes = True


class MasterBlockResponse(BaseModel):
    id: int
    block_name: str
    district_id: int

    class Config:
        from_attributes = True