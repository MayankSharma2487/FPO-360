from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.domain.item_catalogue import BASE_UNIT_VALUES, ITEM_TYPE_VALUES, BaseUnit, ItemType
from app.database.database import Base


_ITEM_TYPE_SQL = ", ".join(f"'{value}'" for value in ITEM_TYPE_VALUES)
_BASE_UNIT_SQL = ", ".join(f"'{value}'" for value in BASE_UNIT_VALUES)


class CropMaster(Base):
    __tablename__ = "crop_masters"
    __table_args__ = (
        CheckConstraint(
            f"item_type IN ({_ITEM_TYPE_SQL})",
            name="ck_crop_masters_item_type",
        ),
        CheckConstraint(
            f"base_unit IN ({_BASE_UNIT_SQL})",
            name="ck_crop_masters_base_unit",
        ),
        CheckConstraint(
            "item_type = 'AGRICULTURAL_COMMODITY' OR organization_id IS NOT NULL",
            name="ck_crop_masters_commercial_owner",
        ),
        Index("ix_crop_masters_org_type_active", "organization_id", "item_type", "is_active"),
    )

    id = Column(Integer, primary_key=True, index=True)
    crop_code = Column(String(50), unique=True, nullable=False, index=True)
    crop_name = Column(String(150), nullable=False)
    crop_category = Column(String(100), nullable=True)
    unit = Column(String(20), default="Kg", nullable=False)  # Kg, Quintal, Ton etc.
    item_type = Column(
        String(40),
        nullable=False,
        default=ItemType.AGRICULTURAL_COMMODITY.value,
        server_default=ItemType.AGRICULTURAL_COMMODITY.value,
    )
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    base_unit = Column(
        String(20),
        nullable=False,
        default=BaseUnit.KG.value,
        server_default=BaseUnit.KG.value,
    )
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    farmer_crops = relationship("FarmerCrop", back_populates="crop")
    procurements = relationship("Procurement", back_populates="crop")
