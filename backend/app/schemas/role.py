from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


class PermissionBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None


class PermissionCreate(PermissionBase):
    pass


class PermissionResponse(PermissionBase):
    id: int

    class Config:
        from_attributes = True


class RoleBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = None


class RoleCreate(RoleBase):
    pass


class RoleResponse(RoleBase):
    id: int
    permissions: List[PermissionResponse] = []

    @model_validator(mode="before")
    @classmethod
    def extract_permissions(cls, values):
        # ORM object: resolve permissions from role_permissions join table
        if hasattr(values, "role_permissions"):
            values.__dict__["permissions"] = [
                rp.permission
                for rp in values.role_permissions
                if rp.permission is not None
            ]
        return values

    class Config:
        from_attributes = True


class AssignPermissionsRequest(BaseModel):
    permission_ids: List[int] = Field(..., min_length=1)


class AssignRoleRequest(BaseModel):
    role_id: int