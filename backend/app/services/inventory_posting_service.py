from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from fastapi import HTTPException
from sqlalchemy import case, func, select, tuple_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.crop_master import CropMaster
from app.models.inventory import InventoryBalance, InventoryLedger


ZERO = Decimal("0.000000")


@dataclass(frozen=True)
class StockEvent:
    organization_id: int
    item_id: int
    transaction_type: str
    quantity: Decimal
    reference_type: str
    reference_id: int | None
    idempotency_key: str
    remarks: str | None = None
    reverses_id: int | None = None
    source_revision: int = 1
    expected_base_unit: str | None = None


class InventoryPostingService:
    """Posts immutable ledger events and their locked balance projection atomically."""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _delta(event: StockEvent) -> Decimal:
        if event.transaction_type not in ("IN", "OUT"):
            raise HTTPException(400, "Inventory movement must be IN or OUT")
        quantity = Decimal(event.quantity)
        if not quantity.is_finite() or quantity <= 0 or quantity.as_tuple().exponent < -6:
            raise HTTPException(400, "Quantity must be positive with at most 6 decimal places")
        return quantity if event.transaction_type == "IN" else -quantity

    @staticmethod
    def _matches(row: InventoryLedger, event: StockEvent) -> bool:
        return (
            row.item_id == event.item_id
            and row.transaction_type == event.transaction_type
            and Decimal(row.quantity) == Decimal(event.quantity)
            and row.reference_type == event.reference_type
            and row.reference_id == event.reference_id
            and row.reverses_id == event.reverses_id
            and row.source_revision == event.source_revision
            and row.remarks == event.remarks
        )

    def _find_idempotent(self, org_id: int, events: list[StockEvent]):
        rows = []
        for event in events:
            row = self.db.query(InventoryLedger).filter(
                InventoryLedger.organization_id == org_id,
                InventoryLedger.idempotency_key == event.idempotency_key,
            ).first()
            if row is not None and not self._matches(row, event):
                raise HTTPException(409, "Idempotency key was already used for a different stock operation")
            rows.append(row)
        if any(rows):
            if not all(rows):
                raise HTTPException(409, "Partial inventory event set exists; reconciliation is required")
            return rows
        return None

    def _lock_idempotency_keys(self, org_id: int, events: list[StockEvent]) -> None:
        if self.db.get_bind().dialect.name != "postgresql":
            return
        for key in sorted({event.idempotency_key for event in events}):
            self.db.execute(
                text("SELECT pg_advisory_xact_lock(:namespace, hashtext(:request_key))"),
                {"namespace": 360361, "request_key": f"{org_id}:{key}"},
            )

    def _ensure_and_lock_balances(self, keys: list[tuple[int, int]], org_id: int, events: list[StockEvent]):
        dialect = self.db.get_bind().dialect.name
        insert_fn = pg_insert if dialect == "postgresql" else sqlite_insert if dialect == "sqlite" else None
        if insert_fn is None:
            raise HTTPException(500, f"Inventory posting is unsupported for database dialect {dialect}")
        for org_id, item_id in keys:
            statement = insert_fn(InventoryBalance).values(
                organization_id=org_id, item_id=item_id, quantity=ZERO,
            ).on_conflict_do_nothing(index_elements=["organization_id", "item_id"])
            self.db.execute(statement)

        balances = self.db.execute(
            select(InventoryBalance)
            .where(
                tuple_(InventoryBalance.organization_id, InventoryBalance.item_id).in_(keys)
            )
            .order_by(InventoryBalance.organization_id, InventoryBalance.item_id)
            .with_for_update()
        ).scalars().all()
        # Another request with the same key may have committed while this
        # transaction waited for the balance row lock.
        existing = self._find_idempotent(org_id, events)
        return {(row.organization_id, row.item_id): row for row in balances}, existing

    def _ledger_balance(self, org_id: int, item_id: int) -> Decimal:
        value = self.db.scalar(
            select(func.coalesce(func.sum(
                case(
                    (InventoryLedger.transaction_type == "IN", InventoryLedger.quantity),
                    else_=-InventoryLedger.quantity,
                )
            ), 0)).where(
                InventoryLedger.organization_id == org_id,
                InventoryLedger.item_id == item_id,
                InventoryLedger.is_active.is_(True),
            )
        )
        return Decimal(str(value or 0)).quantize(Decimal("0.000001"))

    def post_events(self, events: Iterable[StockEvent]) -> list[InventoryLedger]:
        events = list(events)
        if not events:
            return []
        org_ids = {event.organization_id for event in events}
        if len(org_ids) != 1 or next(iter(org_ids)) is None:
            raise HTTPException(403, "Inventory operations require an organization context")
        org_id = next(iter(org_ids))
        if any(not event.idempotency_key.strip() or len(event.idempotency_key) > 128 for event in events):
            raise HTTPException(400, "A valid idempotency key is required for every stock event")
        if len({event.idempotency_key for event in events}) != len(events):
            raise HTTPException(400, "Each inventory event requires a distinct idempotency key")

        existing = self._find_idempotent(org_id, events)
        if existing is not None:
            return existing
        # Serialize the same key even when conflicting requests target different items.
        # Balance-row locks still serialize all distinct writers for each stock key.
        self._lock_idempotency_keys(org_id, events)

        deltas: dict[int, Decimal] = {}
        for event in events:
            deltas[event.item_id] = deltas.get(event.item_id, ZERO) + self._delta(event)
        keys = sorted((org_id, item_id) for item_id in deltas)
        item_ids = sorted({event.item_id for event in events})
        locked_items = self.db.query(CropMaster).filter(
            CropMaster.id.in_(item_ids)
        ).order_by(CropMaster.id).with_for_update(key_share=True).all()
        items_by_id = {item.id: item for item in locked_items}
        if len(items_by_id) != len(item_ids):
            raise HTTPException(404, "Catalogue item not found")
        for item_id, item in items_by_id.items():
            if item.organization_id is not None and item.organization_id != org_id:
                raise HTTPException(404, "Inventory item not found")
            expected_units = {
                event.expected_base_unit for event in events
                if event.item_id == item_id and event.expected_base_unit is not None
            }
            if expected_units and (len(expected_units) != 1 or item.base_unit not in expected_units):
                raise HTTPException(409, "Item base unit changed while posting; reload and retry")
            if not item.is_active and any(
                event.item_id == item_id and event.reverses_id is None for event in events
            ):
                raise HTTPException(400, "Inactive items cannot be used for new stock operations")

        # All stock writers lock catalogue rows first, then balances in the
        # deterministic (organization_id, item_id) order. Unit edits use the
        # catalogue row lock, so conversion cannot race a base-unit change.
        balances, existing = self._ensure_and_lock_balances(keys, org_id, events)
        if existing is not None:
            return existing
        if len(balances) != len(keys):
            raise HTTPException(409, "Could not establish all inventory balance locks")

        # The ledger is checked under the same item lock before trusting the projection.
        for key, balance in balances.items():
            ledger_total = self._ledger_balance(*key)
            if Decimal(balance.quantity) != ledger_total:
                raise HTTPException(
                    409,
                    f"Inventory balance mismatch for item {key[1]}; reconcile before posting",
                )
            projected = Decimal(balance.quantity) + deltas[key[1]]
            if projected < ZERO:
                raise HTTPException(400, f"Insufficient stock for item {key[1]}")

        for key, balance in balances.items():
            balance.quantity = Decimal(balance.quantity) + deltas[key[1]]

        rows = []
        for event in events:
            row = InventoryLedger(
                organization_id=event.organization_id,
                item_id=event.item_id,
                crop_id=(
                    event.item_id
                    if items_by_id[event.item_id].item_type == "AGRICULTURAL_COMMODITY"
                    else None
                ),
                transaction_type=event.transaction_type,
                quantity=Decimal(event.quantity),
                reference_type=event.reference_type,
                reference_id=event.reference_id,
                idempotency_key=event.idempotency_key,
                reverses_id=event.reverses_id,
                source_revision=event.source_revision,
                remarks=event.remarks,
                is_active=True,
            )
            self.db.add(row)
            rows.append(row)
        self.db.flush()
        return rows

    def post_manual(
        self, organization_id: int, item_id: int, transaction_type: str,
        quantity: Decimal, reference_type: str, idempotency_key: str,
        remarks: str | None = None, expected_base_unit: str | None = None,
    ) -> InventoryLedger:
        event = StockEvent(
            organization_id=organization_id,
            item_id=item_id,
            transaction_type=transaction_type,
            quantity=quantity,
            reference_type=reference_type,
            reference_id=None,
            idempotency_key=idempotency_key,
            remarks=remarks,
            expected_base_unit=expected_base_unit,
        )
        return self.post_events([event])[0]

    def source_history(self, organization_id: int, reference_type: str, reference_id: int):
        return self.db.query(InventoryLedger).filter(
            InventoryLedger.organization_id == organization_id,
            InventoryLedger.reference_type == reference_type,
            InventoryLedger.reference_id == reference_id,
            InventoryLedger.reverses_id.is_(None),
        ).order_by(InventoryLedger.source_revision.desc(), InventoryLedger.id.desc()).all()

    def current_source_movement(self, organization_id: int, reference_type: str, reference_id: int):
        reversed_ids = select(InventoryLedger.reverses_id).where(InventoryLedger.reverses_id.is_not(None))
        return self.db.query(InventoryLedger).filter(
            InventoryLedger.organization_id == organization_id,
            InventoryLedger.reference_type == reference_type,
            InventoryLedger.reference_id == reference_id,
            InventoryLedger.reverses_id.is_(None),
            InventoryLedger.is_active.is_(True),
            ~InventoryLedger.id.in_(reversed_ids),
        ).order_by(InventoryLedger.source_revision.desc(), InventoryLedger.id.desc()).first()

    def next_source_revision(self, organization_id: int, reference_type: str, reference_id: int) -> int:
        revision = self.db.query(func.max(InventoryLedger.source_revision)).filter(
            InventoryLedger.organization_id == organization_id,
            InventoryLedger.reference_type == reference_type,
            InventoryLedger.reference_id == reference_id,
        ).scalar()
        return int(revision or 0) + 1

    def reversal_event(self, movement: InventoryLedger, revision: int) -> StockEvent:
        return StockEvent(
            organization_id=movement.organization_id,
            item_id=movement.item_id,
            transaction_type="OUT" if movement.transaction_type == "IN" else "IN",
            quantity=Decimal(movement.quantity),
            reference_type=movement.reference_type,
            reference_id=movement.reference_id,
            idempotency_key=f"{movement.reference_type}:{movement.reference_id}:r{revision}:REVERSAL",
            remarks=f"Reversal of inventory movement {movement.id}",
            reverses_id=movement.id,
            source_revision=revision,
        )

    def source_event(
        self, organization_id: int, item_id: int, direction: str, quantity: Decimal,
        reference_type: str, reference_id: int, revision: int, remarks: str | None = None,
    ) -> StockEvent:
        return StockEvent(
            organization_id=organization_id,
            item_id=item_id,
            transaction_type=direction,
            quantity=quantity,
            reference_type=reference_type,
            reference_id=reference_id,
            idempotency_key=f"{reference_type}:{reference_id}:r{revision}:POST",
            remarks=remarks,
            source_revision=revision,
        )
