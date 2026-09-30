from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Float, ForeignKey,
    UniqueConstraint, CheckConstraint
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.database import Base


class InventoryLedger(Base):
    __tablename__ = "inventory_ledger"

    id = Column(Integer, primary_key=True, index=True)

    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    crop_id = Column(
        Integer,
        ForeignKey("crop_masters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # IN / OUT
    transaction_type = Column(String(10), nullable=False, index=True)

    # Always positive magnitude, stored in KG
    quantity = Column(Float, nullable=False)

    # PROCUREMENT / MANUAL
    reference_type = Column(String(20), nullable=False, index=True)

    # procurement.id when reference_type == PROCUREMENT, else NULL
    reference_id = Column(Integer, nullable=True, index=True)

    remarks = Column(String(500), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    crop = relationship("CropMaster")

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "reference_type",
            "reference_id",
            name="uq_inventory_reference",
        ),
        CheckConstraint(
            "transaction_type IN ('IN','OUT')",
            name="ck_inventory_txn_type",
        ),
        CheckConstraint(
            "quantity > 0",
            name="ck_inventory_quantity_positive",
        ),
    )