"""add shareholders table

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        "shareholders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("shareholder_no", sa.String(length=50), nullable=False),
        sa.Column("share_certificate_no", sa.String(length=100), nullable=True),
        sa.Column("share_count", sa.Integer(), nullable=False),
        sa.Column("share_value", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("total_share_capital", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("joining_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("farmer_id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("shareholder_no", name="uq_shareholders_shareholder_no"),
        sa.UniqueConstraint("share_certificate_no", name="uq_shareholders_certificate_no"),
        sa.ForeignKeyConstraint(["farmer_id"], ["farmers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_shareholders_id", "shareholders", ["id"])
    op.create_index("ix_shareholders_farmer_id", "shareholders", ["farmer_id"], unique=True)
    op.create_index("ix_shareholders_organization_id", "shareholders", ["organization_id"])


def downgrade() -> None:
    op.drop_table("shareholders")