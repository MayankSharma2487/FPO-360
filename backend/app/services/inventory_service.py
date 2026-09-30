from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.inventory_repository import InventoryRepository
from app.repositories.crop_master_repository import CropMasterRepository
from app.models.inventory import InventoryLedger
from app.schemas.inventory import InventoryAdjustRequest


class InventoryService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = InventoryRepository(db)
        self.crop_repo = CropMasterRepository(db)

    # ─── Read APIs ─────────────────────────────────────────────────────

    def list_balances(self, current_user):
        org_id = current_user.organization_id
        rows = self.repo.get_balances(org_id)
        return [
            {
                "crop_id": r.crop_id,
                "crop_name": r.crop_name,
                "total_in": float(r.total_in or 0.0),
                "total_out": float(r.total_out or 0.0),
                "current_balance": float((r.total_in or 0.0) - (r.total_out or 0.0)),
            }
            for r in rows
        ]

    def get_ledger(self, crop_id: int, current_user):
        org_id = current_user.organization_id
        entries = self.repo.list_ledger_by_crop(org_id, crop_id)
        return [
            {
                "id": e.id,
                "organization_id": e.organization_id,
                "crop_id": e.crop_id,
                "crop_name": e.crop.crop_name if e.crop else None,
                "transaction_type": e.transaction_type,
                "quantity": float(e.quantity),
                "reference_type": e.reference_type,
                "reference_id": e.reference_id,
                "remarks": e.remarks,
                "is_active": e.is_active,
                "created_at": e.created_at,
                "updated_at": e.updated_at,
            }
            for e in entries
        ]

    # ─── Manual adjustment ─────────────────────────────────────────────

    def adjust_stock(self, payload: InventoryAdjustRequest, current_user):
        # Viewer / Accountant cannot mutate stock.
        if current_user.role.name not in ("Super Admin", "FPO Admin", "Manager"):
            raise HTTPException(403, "Not authorized to adjust inventory")

        org_id = current_user.organization_id

        crop = self.crop_repo.get_by_id(payload.crop_id)
        if not crop or not crop.is_active:
            raise HTTPException(400, "Invalid or inactive crop")

        if payload.transaction_type == "OUT":
            available = self.repo.get_balance_for_crop(org_id, payload.crop_id)
            if payload.quantity > available:
                raise HTTPException(
                    400,
                    f"Insufficient stock. Available: {available} KG, "
                    f"requested OUT: {payload.quantity} KG",
                )

        ledger = InventoryLedger(
            organization_id=org_id,
            crop_id=payload.crop_id,
            transaction_type=payload.transaction_type,
            quantity=float(payload.quantity),
            reference_type="MANUAL",
            reference_id=None,
            remarks=payload.remarks,
            is_active=True,
        )

        try:
            self.repo.add(ledger)
            self.repo.commit()
        except Exception:
            self.repo.rollback()
            raise

        self.db.refresh(ledger)
        return {
            "id": ledger.id,
            "organization_id": ledger.organization_id,
            "crop_id": ledger.crop_id,
            "crop_name": crop.crop_name,
            "transaction_type": ledger.transaction_type,
            "quantity": float(ledger.quantity),
            "reference_type": ledger.reference_type,
            "reference_id": ledger.reference_id,
            "remarks": ledger.remarks,
            "is_active": ledger.is_active,
            "created_at": ledger.created_at,
            "updated_at": ledger.updated_at,
        }