from sqlalchemy import Boolean, CheckConstraint, Column, Date, DateTime, ForeignKey, Index, Integer, String, Text, func

from app.database.database import Base


class License(Base):
    __tablename__ = "licenses"
    __table_args__ = (
        CheckConstraint("status IN ('Active','Expired','Pending','Not Applicable')", name="ck_license_status"),
        CheckConstraint("issue_date IS NULL OR expiry_date IS NULL OR expiry_date >= issue_date", name="ck_license_expiry_after_issue"),
        CheckConstraint("issue_date IS NULL OR renewal_date IS NULL OR renewal_date >= issue_date", name="ck_license_renewal_after_issue"),
        Index("ix_licenses_org_expiry", "organization_id", "expiry_date"),
        Index("ix_licenses_org_status", "organization_id", "status"),
    )

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE", name="fk_licenses_organization"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL", name="fk_licenses_created_by_user"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL", name="fk_licenses_updated_by_user"), nullable=True)
    license_type = Column(String(100), nullable=False)
    license_number = Column(String(100), nullable=True)
    issuing_authority = Column(String(200), nullable=False)
    issue_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    status = Column(String(30), nullable=False, server_default="Active")
    renewal_date = Column(Date, nullable=True)
    remarks = Column(Text, nullable=True)
    document_reference = Column(String(500), nullable=True)
    is_active = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
