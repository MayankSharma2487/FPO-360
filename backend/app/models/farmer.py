from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base


class Farmer(Base):
    __tablename__ = "farmers"

    id = Column(Integer, primary_key=True, index=True)
    farmer_code = Column(String(50), unique=True, nullable=False, index=True)
    farmer_name = Column(String(150), nullable=False)
    mobile_number = Column(String(15), nullable=False, index=True)
    gender = Column(String(20), nullable=True)
    date_of_birth = Column(DateTime(timezone=True), nullable=True)
    aadhaar_number = Column(String(12), nullable=True, unique=True)
    photo_url = Column(String(500), nullable=True)
    shareholder_no = Column(String(50), nullable=True)
    land_holding_acres = Column(Float, nullable=True)
    farmer_category = Column(String(50), nullable=True)
    is_shareholder = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    village_id = Column(Integer, ForeignKey("villages.id", ondelete="SET NULL"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    village = relationship("Village", back_populates="farmers")
    organization = relationship("Organization", back_populates="farmers")
    shareholder = relationship("Shareholder", back_populates="farmer", uselist=False)
    farmer_crops = relationship("FarmerCrop", back_populates="farmer", cascade="all, delete-orphan")
    procurements = relationship("Procurement", back_populates="farmer")