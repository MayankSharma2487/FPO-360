from sqlalchemy import CheckConstraint, Column, Date, DateTime, ForeignKey, ForeignKeyConstraint, Integer, Numeric, String, Text, UniqueConstraint, func, Index
from sqlalchemy.orm import relationship
from app.database.database import Base


class JournalEntry(Base):
    __tablename__ = "journal_entries"
    __table_args__ = (UniqueConstraint("organization_id", "journal_no", name="uq_journal_org_no"), UniqueConstraint("id", "organization_id", name="uq_journal_id_org"), ForeignKeyConstraint(["financial_year_id", "organization_id"], ["financial_years.id", "financial_years.organization_id"], name="fk_journal_financial_year_org"), CheckConstraint("source_type IN ('MANUAL','OPENING')", name="ck_journal_source_type"), CheckConstraint("source_id IS NULL", name="ck_journal_source_id"), CheckConstraint("status IN ('Draft','Posted','Void')", name="ck_journal_status"), Index("ix_journal_org_status_date", "organization_id", "status", "entry_date"), Index("ix_journal_org_fy_date", "organization_id", "financial_year_id", "entry_date"))
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    journal_no = Column(String(30), nullable=False)
    entry_date = Column(Date, nullable=False)
    financial_year_id = Column(Integer, nullable=False)
    narration = Column(Text, nullable=False)
    source_type = Column(String(30), nullable=False)
    source_id = Column(Integer)
    status = Column(String(10), nullable=False, server_default="Draft")
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    voided_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    voided_at = Column(DateTime(timezone=True))
    void_reason = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    lines = relationship("JournalLine", cascade="all, delete-orphan", order_by="JournalLine.line_no")


class JournalLine(Base):
    __tablename__ = "journal_lines"
    __table_args__ = (UniqueConstraint("journal_entry_id", "line_no", name="uq_journal_line_no"), CheckConstraint("(debit > 0 AND credit = 0) OR (credit > 0 AND debit = 0)", name="ck_journal_line_one_side"), CheckConstraint("debit >= 0 AND credit >= 0", name="ck_journal_line_nonnegative"), CheckConstraint("party_type IS NULL OR party_type IN ('FARMER','CUSTOMER')", name="ck_journal_party_type"), CheckConstraint("(party_type IS NULL) = (party_id IS NULL)", name="ck_journal_party_pair"), ForeignKeyConstraint(["journal_entry_id", "organization_id"], ["journal_entries.id", "journal_entries.organization_id"], ondelete="RESTRICT", name="fk_journal_line_entry_org"), ForeignKeyConstraint(["account_id", "organization_id"], ["accounts.id", "accounts.organization_id"], ondelete="RESTRICT", name="fk_journal_line_account_org"), Index("ix_journal_lines_org_account", "organization_id", "account_id"), Index("ix_journal_lines_party", "organization_id", "party_type", "party_id"))
    id = Column(Integer, primary_key=True)
    journal_entry_id = Column(Integer, nullable=False)
    organization_id = Column(Integer, nullable=False)
    line_no = Column(Integer, nullable=False)
    account_id = Column(Integer, nullable=False)
    debit = Column(Numeric(14, 2), nullable=False, server_default="0")
    credit = Column(Numeric(14, 2), nullable=False, server_default="0")
    party_type = Column(String(20))
    party_id = Column(Integer)
    line_narration = Column(Text)
