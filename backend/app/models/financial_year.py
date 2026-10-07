from sqlalchemy import Boolean, CheckConstraint, Column, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, Index, func, text
from app.database.database import Base


class FinancialYear(Base):
    __tablename__ = "financial_years"
    __table_args__ = (UniqueConstraint("organization_id", "name", name="uq_financial_year_org_name"), UniqueConstraint("id", "organization_id", name="uq_financial_year_id_org"), CheckConstraint("end_date > start_date", name="ck_financial_year_dates"), Index("uq_financial_year_current_org", "organization_id", unique=True, postgresql_where=text("is_current")))
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_current = Column(Boolean, nullable=False, server_default="false")
    is_locked = Column(Boolean, nullable=False, server_default="false")
    locked_at = Column(DateTime(timezone=True))
    locked_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
