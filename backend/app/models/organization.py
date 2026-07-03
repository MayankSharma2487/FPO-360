from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)

    organization_name = Column(String(255), nullable=False)
    registration_number = Column(String(100), unique=True, nullable=False)

    pan_number = Column(String(20), nullable=True)
    gst_number = Column(String(20), nullable=True)
    fssai_number = Column(String(20), nullable=True)

    state = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)

    users = relationship(
        "User",
        back_populates="organization",
        cascade="all, delete-orphan"
    )

    settings = relationship(
        "OrganizationSettings",
        back_populates="organization",
        uselist=False,
        cascade="all, delete-orphan"
    )
    villages = relationship(
        "Village",
        back_populates="organization",
        cascade="all, delete-orphan"
    )
        # ... existing code ...

    farmers = relationship(
        "Farmer",
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    shareholders = relationship(
        "Shareholder",
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    farmer_crops = relationship(
        "FarmerCrop",
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    procurements = relationship(
        "Procurement",
        back_populates="organization",
        cascade="all, delete-orphan"
    )