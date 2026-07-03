from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.organization_repository import OrganizationRepository
from app.auth.password import hash_password
from app.schemas.user import UserCreate, UserUpdate


class UserService:

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.role_repo = RoleRepository(db)
        self.org_repo = OrganizationRepository(db)

    def _check_permission(self, current_user: User, target_user: User | None = None):
        if current_user.role.name == "Super Admin":
            return
        if target_user and target_user.organization_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Access denied to other organization")
        if current_user.role.name != "FPO Admin":
            raise HTTPException(status_code=403, detail="Insufficient permissions")

    def create_user(self, payload: UserCreate, current_user: User) -> User:
        if current_user.role.name == "FPO Admin":
            if payload.role_name in ["Super Admin", "FPO Admin"]:
                raise HTTPException(status_code=403, detail="Cannot create privileged roles")
            payload.organization_id = current_user.organization_id

        if not payload.organization_id:
            raise HTTPException(status_code=400, detail="Organization ID required")

        role = self.role_repo.get_by_name(payload.role_name)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")

        org = self.org_repo.get_by_id(payload.organization_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        existing = self.user_repo.get_by_email(payload.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        new_user = User(
            full_name=payload.full_name,
            email=payload.email,
            password=hash_password(payload.password),
            role_id=role.id,
            organization_id=payload.organization_id,
            is_active=True
        )
        return self.user_repo.create(new_user)

    def update_user(self, user_id: int, payload: UserUpdate, current_user: User) -> User:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        self._check_permission(current_user, user)

        if payload.full_name:
            user.full_name = payload.full_name
        if payload.email:
            user.email = payload.email
        return self.user_repo.update(user)

    def toggle_user_status(self, user_id: int, is_active: bool, current_user: User) -> User:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        self._check_permission(current_user, user)
        return self.user_repo.toggle_active(user, is_active)

    def reset_user_password(self, user_id: int, current_user: User):
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        self._check_permission(current_user, user)
        # Temporary password logic (in production send via email)
        temp_password = "TempPass123!"
        user.password = hash_password(temp_password)
        self.user_repo.update(user)
        return {"message": "Password reset successful. Temporary password generated."}

    def assign_role_to_user(self, user_id: int, role_id: int, current_user: User) -> User:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        self._check_permission(current_user, user)

        role = self.role_repo.get_by_id(role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")

        if current_user.role.name == "FPO Admin" and role.name in ["Super Admin", "FPO Admin"]:
            raise HTTPException(status_code=403, detail="Cannot assign privileged roles")

        return self.user_repo.update_role(user, role.id)