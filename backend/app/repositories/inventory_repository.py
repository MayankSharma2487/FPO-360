from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.crop_master import CropMaster
from app.models.inventory import InventoryBalance, InventoryLedger


class InventoryRepository:
    """Queries the stock projection and its immutable movement history."""

    def __init__(self, db: Session):
        self.db = db

    def add(self, ledger: InventoryLedger) -> InventoryLedger:
        self.db.add(ledger)
        self.db.flush()
        return ledger

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()

    def get_by_reference(self, organization_id: int, reference_type: str, reference_id: int):
        return self.db.query(InventoryLedger).filter(
            InventoryLedger.organization_id == organization_id,
            InventoryLedger.reference_type == reference_type,
            InventoryLedger.reference_id == reference_id,
            InventoryLedger.reverses_id.is_(None),
        ).order_by(InventoryLedger.source_revision.desc(), InventoryLedger.id.desc()).first()

    def list_ledger_by_item(self, organization_id: int, item_id: int):
        return self.db.query(InventoryLedger).options(
            joinedload(InventoryLedger.item)
        ).filter(
            InventoryLedger.organization_id == organization_id,
            InventoryLedger.item_id == item_id,
        ).order_by(InventoryLedger.created_at.desc(), InventoryLedger.id.desc()).all()

    def list_ledger_by_organization(self, organization_id: int):
        return self.db.query(InventoryLedger).options(
            joinedload(InventoryLedger.item)
        ).filter(
            InventoryLedger.organization_id == organization_id,
        ).order_by(InventoryLedger.created_at.desc(), InventoryLedger.id.desc()).all()

    def get_balances(self, organization_id: int):
        movement_totals = self.db.query(
            InventoryLedger.organization_id.label("organization_id"),
            InventoryLedger.item_id.label("item_id"),
            func.coalesce(func.sum(case(
                (InventoryLedger.transaction_type == "IN", InventoryLedger.quantity), else_=0
            )), 0).label("total_in"),
            func.coalesce(func.sum(case(
                (InventoryLedger.transaction_type == "OUT", InventoryLedger.quantity), else_=0
            )), 0).label("total_out"),
        ).filter(
            InventoryLedger.organization_id == organization_id,
            InventoryLedger.is_active.is_(True),
        ).group_by(InventoryLedger.organization_id, InventoryLedger.item_id).subquery()

        return self.db.query(
            InventoryBalance,
            CropMaster,
            func.coalesce(movement_totals.c.total_in, 0).label("total_in"),
            func.coalesce(movement_totals.c.total_out, 0).label("total_out"),
        ).join(
            CropMaster, CropMaster.id == InventoryBalance.item_id
        ).outerjoin(
            movement_totals,
            (movement_totals.c.organization_id == InventoryBalance.organization_id)
            & (movement_totals.c.item_id == InventoryBalance.item_id),
        ).filter(
            InventoryBalance.organization_id == organization_id,
        ).order_by(CropMaster.crop_name.asc(), CropMaster.id.asc()).all()

    def get_balance_for_item(self, organization_id: int, item_id: int):
        return self.db.get(InventoryBalance, (organization_id, item_id))

    def get_balance_for_crop(self, organization_id: int, crop_id: int):
        """Compatibility query; balances are now read from the authoritative projection."""
        value = self.db.scalar(select(InventoryBalance.quantity).where(
            InventoryBalance.organization_id == organization_id,
            InventoryBalance.item_id == crop_id,
        ))
        return value or 0

    def ledger_balance(self, organization_id: int, item_id: int):
        return self.db.scalar(select(func.coalesce(func.sum(case(
            (InventoryLedger.transaction_type == "IN", InventoryLedger.quantity),
            else_=-InventoryLedger.quantity,
        )), 0)).where(
            InventoryLedger.organization_id == organization_id,
            InventoryLedger.item_id == item_id,
            InventoryLedger.is_active.is_(True),
        ))

    def reconciliation(self, organization_id: int):
        ledger_net = self.db.query(
            InventoryLedger.organization_id.label("organization_id"),
            InventoryLedger.item_id.label("item_id"),
            func.sum(case(
                (InventoryLedger.transaction_type == "IN", InventoryLedger.quantity),
                else_=-InventoryLedger.quantity,
            )).label("ledger_quantity"),
        ).filter(
            InventoryLedger.organization_id == organization_id,
            InventoryLedger.is_active.is_(True),
        ).group_by(InventoryLedger.organization_id, InventoryLedger.item_id).subquery()

        projection_side = self.db.query(
            InventoryBalance.organization_id.label("organization_id"),
            InventoryBalance.item_id.label("item_id"),
            InventoryBalance.quantity.label("balance_quantity"),
            func.coalesce(ledger_net.c.ledger_quantity, 0).label("ledger_quantity"),
        ).outerjoin(
            ledger_net,
            (ledger_net.c.organization_id == InventoryBalance.organization_id)
            & (ledger_net.c.item_id == InventoryBalance.item_id),
        ).filter(InventoryBalance.organization_id == organization_id)

        ledger_only = self.db.query(
            ledger_net.c.organization_id,
            ledger_net.c.item_id,
            func.cast(0, InventoryBalance.quantity.type).label("balance_quantity"),
            ledger_net.c.ledger_quantity,
        ).outerjoin(
            InventoryBalance,
            (InventoryBalance.organization_id == ledger_net.c.organization_id)
            & (InventoryBalance.item_id == ledger_net.c.item_id),
        ).filter(InventoryBalance.item_id.is_(None))

        rows = projection_side.union_all(ledger_only).subquery()
        return self.db.query(
            rows.c.organization_id,
            rows.c.item_id,
            CropMaster.crop_name,
            rows.c.balance_quantity,
            rows.c.ledger_quantity,
            (rows.c.balance_quantity - rows.c.ledger_quantity).label("difference"),
        ).join(CropMaster, CropMaster.id == rows.c.item_id).filter(
            rows.c.balance_quantity != rows.c.ledger_quantity,
        ).order_by(rows.c.item_id).all()
