from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, select, case

from app.models.inventory import InventoryLedger
from app.models.crop_master import CropMaster


class InventoryRepository:
    """
    Transaction rule:
    - Never commit a Procurement-linked ledger from here.
      The ProcurementService owns that transaction.
    - For MANUAL adjustments the InventoryService owns commit/rollback.
    """

    def __init__(self, db: Session):
        self.db = db

    # ─── Writes (no commit) ────────────────────────────────────────────

    def add(self, ledger: InventoryLedger) -> InventoryLedger:
        self.db.add(ledger)
        self.db.flush()  # assigns PK, keeps transaction open
        return ledger

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()

    # ─── Reads ─────────────────────────────────────────────────────────

    def get_by_reference(
        self,
        organization_id: int,
        reference_type: str,
        reference_id: int,
    ) -> Optional[InventoryLedger]:
        return (
            self.db.query(InventoryLedger)
            .filter(
                InventoryLedger.organization_id == organization_id,
                InventoryLedger.reference_type == reference_type,
                InventoryLedger.reference_id == reference_id,
            )
            .first()
        )

    def list_ledger_by_crop(
        self,
        organization_id: int,
        crop_id: int,
    ) -> List[InventoryLedger]:
        return (
            self.db.query(InventoryLedger)
            .options(joinedload(InventoryLedger.crop))
            .filter(
                InventoryLedger.organization_id == organization_id,
                InventoryLedger.crop_id == crop_id,
            )
            .order_by(
                InventoryLedger.created_at.desc(),
                InventoryLedger.id.desc(),
            )
            .all()
        )

    # ─── Aggregation ───────────────────────────────────────────────────

    def get_balances(self, organization_id: int):
        """
        Returns list of (crop_id, crop_name, total_in, total_out).
        Only active ledger rows count. Uses SQL aggregation + join.
        """
        q = (
            self.db.query(
                InventoryLedger.crop_id.label("crop_id"),
                CropMaster.crop_name.label("crop_name"),
                func.coalesce(
                    func.sum(
                        case(
                            (InventoryLedger.transaction_type == "IN",
                             InventoryLedger.quantity),
                            else_=0,
                        )
                    ),
                    0.0,
                ).label("total_in"),
                func.coalesce(
                    func.sum(
                        case(
                            (InventoryLedger.transaction_type == "OUT",
                             InventoryLedger.quantity),
                            else_=0,
                        )
                    ),
                    0.0,
                ).label("total_out"),
            )
            .join(CropMaster, CropMaster.id == InventoryLedger.crop_id)
            .filter(
                InventoryLedger.organization_id == organization_id,
                InventoryLedger.is_active.is_(True),
            )
            .group_by(InventoryLedger.crop_id, CropMaster.crop_name)
            .order_by(CropMaster.crop_name.asc())
        )
        return q.all()

    def get_balance_for_crop(
        self,
        organization_id: int,
        crop_id: int,
    ) -> float:
        """
        Current balance (sum of active IN - sum of active OUT) for a crop.
        Uses SQLAlchemy 2.x select() consistent with procurement_repository.
        """
        stmt = select(
            func.coalesce(
                func.sum(
                    case(
                        (InventoryLedger.transaction_type == "IN",
                         InventoryLedger.quantity),
                        (InventoryLedger.transaction_type == "OUT",
                         -InventoryLedger.quantity),
                        else_=0,
                    )
                ),
                0.0,
            )
        ).where(
            InventoryLedger.organization_id == organization_id,
            InventoryLedger.crop_id == crop_id,
            InventoryLedger.is_active.is_(True),
        )
        result = self.db.scalar(stmt)
        return float(result) if result is not None else 0.0