from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Numeric, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.database import Base


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    sale_no = Column(String(30), unique=True, nullable=False, index=True)  # SA-YYYY-00001
    sale_date = Column(DateTime(timezone=True), nullable=False)

    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    crop_id = Column(Integer, ForeignKey("crop_masters.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    # quantity stored in KG (same convention as Procurement)
    quantity = Column(Float, nullable=False)
    unit = Column(String(20), default="KG", nullable=False)
    rate_per_unit = Column(Numeric(12, 2), nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)

    payment_status = Column(String(20), default="Pending", nullable=False)  # Pending / Paid
    remarks = Column(String(500), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    customer = relationship("Customer", back_populates="sales")
    crop = relationship("CropMaster")
    organization = relationship("Organization")
