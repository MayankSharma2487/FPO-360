from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.database import Base

class FarmerCrop(Base):
    __tablename__ = "farmer_crops"

    id = Column(Integer, primary_key=True, index=True)

    farmer_id = Column(Integer, ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False)
    crop_id = Column(Integer, ForeignKey("crop_masters.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)

    season = Column(String(50), nullable=True)  # Kharif, Rabi, Zaid
    year = Column(Integer, nullable=False)
    area_acres = Column(Float, nullable=True)
    sowing_date = Column(DateTime(timezone=True), nullable=True)
    harvest_date = Column(DateTime(timezone=True), nullable=True)
    expected_yield = Column(Float, nullable=True)  # in unit per acre
    actual_yield = Column(Float, nullable=True)
    remarks = Column(String(500), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    farmer = relationship("Farmer", back_populates="farmer_crops")
    crop = relationship("CropMaster", back_populates="farmer_crops")
    organization = relationship("Organization")