from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.sql import func
from app.database.database import Base
class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    payment_no = Column(String, unique=True, index=True, nullable=True) # Populated after flush
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=False)
    procurement_id = Column(Integer, ForeignKey("procurements.id"), nullable=False)
    
    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime(timezone=True), default=func.now())
    payment_method = Column(String, nullable=False)
    reference_no = Column(String, nullable=True)
    status = Column(String, default="Pending")
    remarks = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())