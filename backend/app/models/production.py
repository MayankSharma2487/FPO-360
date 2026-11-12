from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base


class ProductionRecord(Base):
    __tablename__ = "production_records"

    id = Column(Integer, primary_key=True)
    organization_id = Column(
        Integer, ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    reference_no = Column(String(32), nullable=False)
    idempotency_key = Column(String(128), nullable=False)
    payload_hash = Column(String(64), nullable=False)
    production_date = Column(Date, nullable=False, index=True)
    finished_item_id = Column(
        Integer, ForeignKey("crop_masters.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    output_quantity = Column(Numeric(20, 6), nullable=False)
    output_unit = Column(String(20), nullable=False)
    output_base_quantity = Column(Numeric(20, 6), nullable=False)
    wastage_quantity = Column(Numeric(20, 6), nullable=False, default=0)
    wastage_unit = Column(String(20), nullable=False)
    wastage_base_quantity = Column(Numeric(20, 6), nullable=False, default=0)
    status = Column(String(16), nullable=False, default="POSTED", server_default="POSTED")
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    finished_item = relationship("CropMaster", foreign_keys=[finished_item_id])
    creator = relationship("User", foreign_keys=[created_by])
    inputs = relationship(
        "ProductionInput", back_populates="production", order_by="ProductionInput.id"
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "reference_no", name="uq_production_org_reference"),
        UniqueConstraint("organization_id", "idempotency_key", name="uq_production_org_idempotency"),
        CheckConstraint("output_quantity > 0", name="ck_production_output_positive"),
        CheckConstraint("output_base_quantity > 0", name="ck_production_output_base_positive"),
        CheckConstraint("wastage_quantity >= 0", name="ck_production_wastage_nonnegative"),
        CheckConstraint("wastage_base_quantity >= 0", name="ck_production_wastage_base_nonnegative"),
        CheckConstraint("status = 'POSTED'", name="ck_production_status_posted"),
    )


class ProductionInput(Base):
    __tablename__ = "production_inputs"

    id = Column(Integer, primary_key=True)
    production_id = Column(
        Integer, ForeignKey("production_records.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    organization_id = Column(
        Integer, ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    item_id = Column(
        Integer, ForeignKey("crop_masters.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    input_type = Column(String(20), nullable=False)
    quantity = Column(Numeric(20, 6), nullable=False)
    unit = Column(String(20), nullable=False)
    base_quantity = Column(Numeric(20, 6), nullable=False)

    production = relationship("ProductionRecord", back_populates="inputs")
    item = relationship("CropMaster", foreign_keys=[item_id])

    __table_args__ = (
        CheckConstraint("input_type IN ('RAW_MATERIAL','PACKAGING_MATERIAL')", name="ck_production_input_type"),
        CheckConstraint("quantity > 0", name="ck_production_input_quantity_positive"),
        CheckConstraint("base_quantity > 0", name="ck_production_input_base_positive"),
    )
