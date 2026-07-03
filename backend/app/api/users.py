from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.user import UserResponse, UserCreate, UserUpdate, PasswordResetResponse
from app.schemas.role import AssignRoleRequest
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService
from app.auth.dependencies import get_current_user, require_roles
from app.models.user import User

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.get("/", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin"))
):
    repo = UserRepository(db)
    if current_user.role.name == "Super Admin":
        return repo.list_all()
    return repo.list_all(organization_id=current_user.organization_id)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin"))
):
    service = UserService(db)
    return service.create_user(payload, current_user)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin"))
):
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if current_user.role.name != "Super Admin" and user.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin"))
):
    service = UserService(db)
    return service.update_user(user_id, payload, current_user)


@router.patch("/{user_id}/status", response_model=UserResponse)
def toggle_user_status(
    user_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin"))
):
    service = UserService(db)
    return service.toggle_user_status(user_id, is_active, current_user)


@router.post("/{user_id}/reset-password", response_model=PasswordResetResponse)
def reset_user_password(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin"))
):
    service = UserService(db)
    return service.reset_user_password(user_id, current_user)


@router.put("/{user_id}/role", response_model=UserResponse)
def assign_role_to_user(
    user_id: int,
    payload: AssignRoleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin"))
):
    service = UserService(db)
    return service.assign_role_to_user(user_id, payload.role_id, current_user)