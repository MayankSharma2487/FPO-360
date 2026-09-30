from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.auth.dependencies import get_current_user, require_roles
from app.models.user import User
from app.schemas.inventory import (
    InventoryAdjustRequest,
    InventoryLedgerResponse,
    InventoryBalanceResponse,
)
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("/balances", response_model=list[InventoryBalanceResponse])
def list_balances(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("Super Admin", "FPO Admin", "Manager", "Accountant", "Viewer")
    ),
):
    return InventoryService(db).list_balances(current_user)


@router.get("/{crop_id}/ledger", response_model=list[InventoryLedgerResponse])
def get_ledger(
    crop_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("Super Admin", "FPO Admin", "Manager", "Accountant", "Viewer")
    ),
):
    return InventoryService(db).get_ledger(crop_id, current_user)


@router.post(
    "/adjust",
    response_model=InventoryLedgerResponse,
    status_code=status.HTTP_201_CREATED,
)
def adjust_stock(
    payload: InventoryAdjustRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("Super Admin", "FPO Admin", "Manager")
    ),
):
    return InventoryService(db).adjust_stock(payload, current_user)