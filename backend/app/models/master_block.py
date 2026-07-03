from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.database import Base


class MasterBlock(Base):
    __tablename__ = "master_blocks"

    id = Column(Integer, primary_key=True, index=True)
    block_name = Column(String(150), nullable=False)
    district_id = Column(Integer, ForeignKey("master_districts.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    district = relationship("MasterDistrict", back_populates="blocks")