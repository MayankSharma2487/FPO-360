from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.database.database import get_db
from app.domain.item_catalogue import ItemType
from app.models.user import User
from app.schemas.item import ItemCreate, ItemResponse, ItemUpdate
from app.services.item_service import ItemService

router = APIRouter(prefix="/items", tags=["Item Catalogue"])
READ_ROLES = ("Super Admin", "FPO Admin", "Manager", "Accountant", "Viewer")


@router.get("/", response_model=list[ItemResponse])
def list_items(search: Optional[str] = None, item_type: Optional[ItemType] = None,
               is_active: Optional[bool] = None, db: Session = Depends(get_db),
               current_user: User = Depends(require_roles(*READ_ROLES))):
    return ItemService(db).list_items(current_user, search, item_type.value if item_type else None, is_active)


@router.get("/next-code")
def get_next_code(item_type: ItemType, db: Session = Depends(get_db),
                  current_user: User = Depends(require_roles("Super Admin", "FPO Admin"))):
    return ItemService(db).get_next_code(item_type, current_user)


@router.get("/{item_id}", response_model=ItemResponse)
def get_item(item_id: int, db: Session = Depends(get_db),
             current_user: User = Depends(require_roles(*READ_ROLES))):
    return ItemService(db).get_item(item_id, current_user)


@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(payload: ItemCreate, db: Session = Depends(get_db),
                current_user: User = Depends(require_roles("Super Admin", "FPO Admin"))):
    return ItemService(db).create_item(payload, current_user)


@router.put("/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, payload: ItemUpdate, db: Session = Depends(get_db),
                current_user: User = Depends(require_roles("Super Admin", "FPO Admin"))):
    return ItemService(db).update_item(item_id, payload, current_user)


@router.patch("/{item_id}/status", response_model=ItemResponse)
def set_item_status(item_id: int, is_active: bool = Query(...), db: Session = Depends(get_db),
                    current_user: User = Depends(require_roles("Super Admin", "FPO Admin"))):
    return ItemService(db).set_active(item_id, is_active, current_user)
