from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.role import (
    RoleCreate,
    RoleResponse,
    PermissionCreate,
    PermissionResponse,
    AssignPermissionsRequest
)
from app.services.role_service import RoleService
from app.auth.dependencies import require_roles
from app.models.user import User

router = APIRouter(
    prefix="/roles",
    tags=["Roles & Permissions"]
)


@router.post(
    "/",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED
)
def create_role(
    role: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin"))
):
    service = RoleService(db)

    return service.create_role(role)


@router.get("/", response_model=list[RoleResponse])
def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin"))
):
    service = RoleService(db)

    return service.list_roles()


@router.get("/permissions", response_model=list[PermissionResponse])
def list_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin"))
):
    service = RoleService(db)

    return service.list_permissions()


@router.post(
    "/permissions",
    response_model=PermissionResponse,
    status_code=status.HTTP_201_CREATED
)
def create_permission(
    permission: PermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin"))
):
    service = RoleService(db)

    return service.create_permission(permission)


@router.get("/{role_id}", response_model=RoleResponse)
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin"))
):
    service = RoleService(db)

    return service.get_role(role_id)


@router.post("/{role_id}/permissions", response_model=RoleResponse)
def assign_permissions_to_role(
    role_id: int,
    payload: AssignPermissionsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin"))
):
    service = RoleService(db)

    return service.assign_permissions_to_role(role_id, payload)