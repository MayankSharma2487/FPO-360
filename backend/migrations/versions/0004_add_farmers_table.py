"""add farmers table

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        "farmers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("farmer_code", sa.String(length=50), nullable=False),
        sa.Column("farmer_name", sa.String(length=150), nullable=False),
        sa.Column("mobile_number", sa.String(length=15), nullable=False),
        sa.Column("gender", sa.String(length=20), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("aadhaar_number", sa.String(length=12), nullable=True),
        sa.Column("photo_url", sa.String(length=500), nullable=True),
        sa.Column("shareholder_no", sa.String(length=50), nullable=True),
        sa.Column("land_holding_acres", sa.Float(), nullable=True),
        sa.Column("farmer_category", sa.String(length=50), nullable=True),
        sa.Column("is_shareholder", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("village_id", sa.Integer(), nullable=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("farmer_code", name="uq_farmers_farmer_code"),
        sa.ForeignKeyConstraint(["village_id"], ["villages.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_farmers_id", "farmers", ["id"])
    op.create_index("ix_farmers_farmer_code", "farmers", ["farmer_code"], unique=True)
    op.create_index("ix_farmers_organization_id", "farmers", ["organization_id"])
    op.create_index("ix_farmers_village_id", "farmers", ["village_id"])


def downgrade() -> None:
    op.drop_table("farmers")