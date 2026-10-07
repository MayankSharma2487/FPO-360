"""Add finance years and accounts. Revision 0011, revises 0010."""
from alembic import op
import sqlalchemy as sa
revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None
def upgrade():
    op.create_table("financial_years", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False), sa.Column("name", sa.String(100), nullable=False), sa.Column("start_date", sa.Date(), nullable=False), sa.Column("end_date", sa.Date(), nullable=False), sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("locked_at", sa.DateTime(timezone=True)), sa.Column("locked_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.UniqueConstraint("organization_id", "name", name="uq_financial_year_org_name"), sa.UniqueConstraint("id", "organization_id", name="uq_financial_year_id_org"), sa.CheckConstraint("end_date > start_date", name="ck_financial_year_dates"))
    op.create_index("ix_financial_years_organization_id", "financial_years", ["organization_id"])
    op.create_index("uq_financial_year_current_org", "financial_years", ["organization_id"], unique=True, postgresql_where=sa.text("is_current"))
    op.create_table("accounts", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False), sa.Column("account_code", sa.String(20), nullable=False), sa.Column("account_name", sa.String(150), nullable=False), sa.Column("account_type", sa.String(20), nullable=False), sa.Column("account_group", sa.String(100), nullable=False), sa.Column("account_subtype", sa.String(20)), sa.Column("system_key", sa.String(60)), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.UniqueConstraint("organization_id", "account_code", name="uq_account_org_code"), sa.UniqueConstraint("organization_id", "system_key", name="uq_account_org_system_key"), sa.UniqueConstraint("id", "organization_id", name="uq_account_id_org"), sa.CheckConstraint("account_type IN ('Asset','Liability','Equity','Income','Expense')", name="ck_account_type"), sa.CheckConstraint("account_subtype IS NULL OR account_subtype IN ('CASH','BANK')", name="ck_account_subtype"))
    op.create_index("ix_accounts_organization_id", "accounts", ["organization_id"])
def downgrade():
    op.drop_table("accounts")
    op.drop_index("uq_financial_year_current_org", table_name="financial_years")
    op.drop_table("financial_years")
