from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.role import Role
from app.models.permission import Permission
from app.models.user import User
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.role import (
    RoleCreate,
    PermissionCreate,
    AssignPermissionsRequest
)


class RoleService:

    def __init__(self, db: Session):
        self.db = db
        self.role_repo = RoleRepository(db)
        self.user_repo = UserRepository(db)

    def create_role(self, payload: RoleCreate) -> Role:

        existing = self.role_repo.get_by_name(payload.name)

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role with this name already exists"
            )

        role = Role(
            name=payload.name,
            description=payload.description
        )

        return self.role_repo.create_role(role)

    def list_roles(self):
        return self.role_repo.list_roles()

    def get_role(self, role_id: int) -> Role:

        role = self.role_repo.get_by_id(role_id)

        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )

        return role

    def create_permission(self, payload: PermissionCreate) -> Permission:

        existing = self.role_repo.get_permission_by_name(payload.name)

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Permission with this name already exists"
            )

        permission = Permission(
            name=payload.name,
            description=payload.description
        )

        return self.role_repo.create_permission(permission)

    def list_permissions(self):
        return self.role_repo.list_permissions()

    def assign_permissions_to_role(
        self,
        role_id: int,
        payload: AssignPermissionsRequest
    ) -> Role:

        role = self.get_role(role_id)

        for permission_id in payload.permission_ids:
            permission = self.role_repo.get_permission_by_id(permission_id)

            if not permission:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Permission with id {permission_id} not found"
                )

        return self.role_repo.assign_permissions(role, payload.permission_ids)

    def assign_role_to_user(self, user_id: int, role_id: int) -> User:

        user = self.user_repo.get_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        role = self.get_role(role_id)

        return self.user_repo.update_role(user, role.id)