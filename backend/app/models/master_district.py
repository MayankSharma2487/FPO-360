from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.database import Base


class MasterDistrict(Base):
    __tablename__ = "master_districts"

    id = Column(Integer, primary_key=True, index=True)
    district_name = Column(String(150), nullable=False)
    state_id = Column(Integer, ForeignKey("master_states.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    state = relationship("MasterState", back_populates="districts")
    blocks = relationship("MasterBlock", back_populates="district")