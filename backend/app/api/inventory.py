from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.auth.dependencies import get_current_user, require_roles
from app.models.user import User
from app.schemas.inventory import (
    InventoryAdjustRequest,
    InventoryLedgerResponse,
    InventoryBalanceResponse,
    InventoryReconciliationResponse,
)
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("/balances", response_model=list[InventoryBalanceResponse])
def list_balances(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("FPO Admin", "Manager", "Accountant", "Viewer")
    ),
):
    return InventoryService(db).list_balances(current_user)


@router.get("/reconciliation", response_model=list[InventoryReconciliationResponse])
def reconcile_inventory(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("FPO Admin", "Manager", "Accountant", "Viewer")),
):
    return InventoryService(db).reconcile(current_user)


@router.get("/ledger", response_model=list[InventoryLedgerResponse])
def list_ledger(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("FPO Admin", "Manager", "Accountant", "Viewer")
    ),
):
    return InventoryService(db).list_ledger(current_user)


@router.get("/{crop_id}/ledger", response_model=list[InventoryLedgerResponse])
def get_ledger(
    crop_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("FPO Admin", "Manager", "Accountant", "Viewer")
    ),
):
    return InventoryService(db).get_ledger(crop_id, current_user)


@router.get("/items/{item_id}/ledger", response_model=list[InventoryLedgerResponse])
def get_item_ledger(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("FPO Admin", "Manager", "Accountant", "Viewer")
    ),
):
    return InventoryService(db).get_ledger(item_id, current_user)


@router.post(
    "/adjust",
    response_model=InventoryLedgerResponse,
    status_code=status.HTTP_201_CREATED,
)
def adjust_stock(
    payload: InventoryAdjustRequest,
    idempotency_key: str | None = Header(
        None, alias="Idempotency-Key", min_length=1, max_length=128,
        description="Required for safe retry of a manual stock movement.",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("FPO Admin", "Manager")),
):
    if idempotency_key is None:
        raise HTTPException(
            400,
            "Idempotency-Key header is required for manual stock movements; retry with the same key.",
        )
    return InventoryService(db).adjust_stock(payload, current_user, idempotency_key)
