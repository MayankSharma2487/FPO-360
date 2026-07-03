from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.database import Base

class MasterState(Base):
    __tablename__ = "master_states"

    id = Column(Integer, primary_key=True, index=True)
    state_name = Column(String(100), nullable=False, unique=True)
    state_code = Column(String(10), nullable=True, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    districts = relationship("MasterDistrict", back_populates="state")