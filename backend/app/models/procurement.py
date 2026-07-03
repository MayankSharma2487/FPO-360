from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Numeric, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.database import Base


class Procurement(Base):
    __tablename__ = "procurements"

    id = Column(Integer, primary_key=True, index=True)
    procurement_no = Column(String(30), unique=True, nullable=False, index=True)  # PR-2026-00001
    procurement_date = Column(DateTime(timezone=True), nullable=False)

    farmer_id = Column(Integer, ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False)
    crop_id = Column(Integer, ForeignKey("crop_masters.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)

    quantity = Column(Float, nullable=False)
    unit = Column(String(20), default="KG", nullable=False)
    rate_per_unit = Column(Numeric(12, 2), nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)

    quality_grade = Column(String(10), nullable=True)   # A, B, C, D
    remarks = Column(String(500), nullable=True)

    # Future-ready fields
    warehouse_id = Column(String(50), nullable=True)
    lot_number = Column(String(50), nullable=True)
    vehicle_number = Column(String(50), nullable=True)
    receipt_no = Column(String(50), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    farmer = relationship("Farmer", back_populates="procurements")
    crop = relationship("CropMaster", back_populates="procurements")
    organization = relationship("Organization", back_populates="procurements")