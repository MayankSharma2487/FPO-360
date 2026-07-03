from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.role import Role
from app.models.permission import Permission
from app.models.role_permission import RolePermission


class RoleRepository:

    def __init__(self, db: Session):
        self.db = db

    def create_role(self, role: Role) -> Role:
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)

        return role

    def get_by_id(self, role_id: int) -> Optional[Role]:
        return (
            self.db.query(Role)
            .filter(Role.id == role_id)
            .first()
        )

    def get_by_name(self, name: str) -> Optional[Role]:
        return (
            self.db.query(Role)
            .filter(Role.name == name)
            .first()
        )

    def list_roles(self) -> List[Role]:
        return self.db.query(Role).all()

    def count_all(self) -> int:
        return self.db.query(Role).count()

    def create_permission(self, permission: Permission) -> Permission:
        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)

        return permission

    def get_permission_by_id(self, permission_id: int) -> Optional[Permission]:
        return (
            self.db.query(Permission)
            .filter(Permission.id == permission_id)
            .first()
        )

    def get_permission_by_name(self, name: str) -> Optional[Permission]:
        return (
            self.db.query(Permission)
            .filter(Permission.name == name)
            .first()
        )

    def list_permissions(self) -> List[Permission]:
        return self.db.query(Permission).all()

    def assign_permissions(
        self,
        role: Role,
        permission_ids: List[int]
    ) -> Role:

        existing_permission_ids = {
            rp.permission_id for rp in role.role_permissions
        }

        for permission_id in permission_ids:
            if permission_id not in existing_permission_ids:
                self.db.add(
                    RolePermission(
                        role_id=role.id,
                        permission_id=permission_id
                    )
                )

        self.db.commit()
        self.db.refresh(role)

        return role