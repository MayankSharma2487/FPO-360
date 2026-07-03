from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base


class Shareholder(Base):
    __tablename__ = "shareholders"

    id = Column(Integer, primary_key=True, index=True)
    shareholder_no = Column(String(50), unique=True, nullable=False, index=True)
    share_certificate_no = Column(String(100), nullable=True, unique=True)
    share_count = Column(Integer, nullable=False)
    share_value = Column(Numeric(12, 2), nullable=False)
    total_share_capital = Column(Numeric(12, 2), nullable=False)
    joining_date = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    farmer_id = Column(Integer, ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False, unique=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    farmer = relationship("Farmer", back_populates="shareholder")
    organization = relationship("Organization", back_populates="shareholders")