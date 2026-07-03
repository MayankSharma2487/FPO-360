from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.user import UserRegister, UserLogin, UserCreate
from app.auth.password import hash_password, verify_password
from app.auth.jwt_handler import create_access_token
from app.services.user_service import UserService


class AuthService:

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.role_repo = RoleRepository(db)
        self.organization_repo = OrganizationRepository(db)
        self.user_service = UserService(db)

    def register_user(self, payload: UserRegister) -> User:
        # Internal use only - admins call create_user_admin
        existing_user = self.user_repo.get_by_email(payload.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        organization = self.organization_repo.get_by_id(payload.organization_id)
        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")

        role = self.role_repo.get_by_name(payload.role_name)
        if not role:
            raise HTTPException(status_code=404, detail=f"Role '{payload.role_name}' not found")

        new_user = User(
            full_name=payload.full_name,
            email=payload.email,
            password=hash_password(payload.password),
            role_id=role.id,
            organization_id=organization.id,
            is_active=True
        )
        return self.user_repo.create(new_user)

    def authenticate_user(self, payload: UserLogin) -> User:
        user = self.user_repo.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.password):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="User account is inactive")

        return user

    def create_token(self, user: User) -> str:
        role_name = user.role.name if user.role else None
        return create_access_token({
            "user_id": user.id,
            "email": user.email,
            "role": role_name,
            "organization_id": user.organization_id
        })

    def create_user_for_admin(self, payload: UserCreate, current_user: User) -> User:
        return self.user_service.create_user_admin(payload, current_user)

    def reset_user_password(self, user: User):
        # Generate temporary password (in production use email service)
        temp_password = "TempPass123!"
        user.password = hash_password(temp_password)
        self.user_repo.update(user)
        # TODO: Send email with temp password