from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.database import Base


class CropMaster(Base):
    __tablename__ = "crop_masters"

    id = Column(Integer, primary_key=True, index=True)
    crop_code = Column(String(50), unique=True, nullable=False, index=True)
    crop_name = Column(String(150), nullable=False)
    crop_category = Column(String(100), nullable=True)
    unit = Column(String(20), default="Kg", nullable=False)  # Kg, Quintal, Ton etc.
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    farmer_crops = relationship("FarmerCrop", back_populates="crop")
    procurements = relationship("Procurement", back_populates="crop")