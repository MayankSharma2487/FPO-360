from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from app.database.database import Base


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (UniqueConstraint("organization_id", "account_code", name="uq_account_org_code"), UniqueConstraint("organization_id", "system_key", name="uq_account_org_system_key"), UniqueConstraint("id", "organization_id", name="uq_account_id_org"), CheckConstraint("account_type IN ('Asset','Liability','Equity','Income','Expense')", name="ck_account_type"), CheckConstraint("account_subtype IS NULL OR account_subtype IN ('CASH','BANK')", name="ck_account_subtype"),)
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    account_code = Column(String(20), nullable=False)
    account_name = Column(String(150), nullable=False)
    account_type = Column(String(20), nullable=False)
    account_group = Column(String(100), nullable=False)
    account_subtype = Column(String(20))
    system_key = Column(String(60))
    is_active = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
