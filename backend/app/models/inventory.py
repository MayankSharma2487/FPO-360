from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
    event,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base


class InventoryLedger(Base):
    __tablename__ = "inventory_ledger"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # crop_id remains populated for legacy agricultural rows. item_id is the
    # canonical reference and points at the existing crop_masters catalogue.
    crop_id = Column(
        Integer, ForeignKey("crop_masters.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    item_id = Column(
        Integer, ForeignKey("crop_masters.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    transaction_type = Column(String(10), nullable=False, index=True)
    quantity = Column(Numeric(20, 6), nullable=False)
    reference_type = Column(String(20), nullable=False, index=True)
    reference_id = Column(Integer, nullable=True, index=True)
    idempotency_key = Column(String(128), nullable=False, default=lambda: f"direct:{uuid4().hex}")
    reverses_id = Column(
        Integer,
        ForeignKey("inventory_ledger.id", ondelete="RESTRICT"),
        nullable=True,
    )
    source_revision = Column(Integer, nullable=False, default=1, server_default="1")
    remarks = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    crop = relationship("CropMaster", foreign_keys=[crop_id])
    item = relationship("CropMaster", foreign_keys=[item_id])
    reversal = relationship("InventoryLedger", remote_side=[id], foreign_keys=[reverses_id])

    __table_args__ = (
        UniqueConstraint("organization_id", "idempotency_key", name="uq_inventory_idempotency"),
        UniqueConstraint("reverses_id", name="uq_inventory_single_reversal"),
        CheckConstraint("transaction_type IN ('IN','OUT')", name="ck_inventory_txn_type"),
        CheckConstraint("quantity > 0", name="ck_inventory_quantity_positive"),
        CheckConstraint("source_revision > 0", name="ck_inventory_source_revision_positive"),
        CheckConstraint("crop_id IS NULL OR crop_id = item_id", name="ck_inventory_legacy_crop_matches_item"),
        Index("ix_inventory_org_item_active", "organization_id", "item_id", "is_active"),
    )


class InventoryBalance(Base):
    __tablename__ = "inventory_balances"

    organization_id = Column(
        Integer, ForeignKey("organizations.id", ondelete="RESTRICT"), primary_key=True
    )
    item_id = Column(
        Integer, ForeignKey("crop_masters.id", ondelete="RESTRICT"), primary_key=True
    )
    quantity = Column(Numeric(20, 6), nullable=False, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (CheckConstraint("quantity >= 0", name="ck_inventory_balance_nonnegative"),)


class InventoryCreateRequest(Base):
    """Transactional idempotency receipt for Procurement and Sales creation."""

    __tablename__ = "inventory_create_requests"

    organization_id = Column(
        Integer, ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    operation = Column(String(32), nullable=False)
    idempotency_key = Column(String(128), nullable=False)
    payload_hash = Column(String(64), nullable=False)
    source_id = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint(
            "organization_id", "operation", "idempotency_key",
            name="pk_inventory_create_requests",
        ),
        CheckConstraint(
            "operation IN ('PROCUREMENT_CREATE', 'SALE_CREATE')",
            name="ck_inventory_create_request_operation",
        ),
        CheckConstraint("source_id > 0", name="ck_inventory_create_request_source_positive"),
    )


@event.listens_for(InventoryLedger, "before_insert")
def _populate_legacy_item_id(_mapper, _connection, ledger):
    # Retain compatibility for existing crop-facing service/test constructors.
    if ledger.item_id is None and ledger.crop_id is not None:
        ledger.item_id = ledger.crop_id
