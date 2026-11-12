"""add organization-scoped license registry

Revision ID: 0013
Revises: 0012
"""
from alembic import op
import sqlalchemy as sa


revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "licenses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("license_type", sa.String(length=100), nullable=False),
        sa.Column("license_number", sa.String(length=100), nullable=True),
        sa.Column("issuing_authority", sa.String(length=200), nullable=False),
        sa.Column("issue_date", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="Active"),
        sa.Column("renewal_date", sa.Date(), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("document_reference", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE", name="fk_licenses_organization"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL", name="fk_licenses_created_by_user"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL", name="fk_licenses_updated_by_user"),
        sa.CheckConstraint("status IN ('Active','Expired','Pending','Not Applicable')", name="ck_license_status"),
        sa.CheckConstraint("issue_date IS NULL OR expiry_date IS NULL OR expiry_date >= issue_date", name="ck_license_expiry_after_issue"),
        sa.CheckConstraint("issue_date IS NULL OR renewal_date IS NULL OR renewal_date >= issue_date", name="ck_license_renewal_after_issue"),
    )
    op.create_index("ix_licenses_organization_id", "licenses", ["organization_id"])
    op.create_index("ix_licenses_org_expiry", "licenses", ["organization_id", "expiry_date"])
    op.create_index("ix_licenses_org_status", "licenses", ["organization_id", "status"])


def downgrade():
    op.drop_index("ix_licenses_org_status", table_name="licenses")
    op.drop_index("ix_licenses_org_expiry", table_name="licenses")
    op.drop_index("ix_licenses_organization_id", table_name="licenses")
    op.drop_table("licenses")
