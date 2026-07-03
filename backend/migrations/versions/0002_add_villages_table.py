"""add villages table

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        "villages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("village_code", sa.String(length=50), nullable=False),
        sa.Column("village_name", sa.String(length=150), nullable=False),
        sa.Column("block", sa.String(length=100), nullable=True),
        sa.Column("district", sa.String(length=100), nullable=False),
        sa.Column("state", sa.String(length=100), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("village_code", name="uq_villages_village_code"),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE"
        ),
    )
    op.create_index("ix_villages_id", "villages", ["id"])
    op.create_index("ix_villages_village_code", "villages", ["village_code"], unique=True)
    op.create_index("ix_villages_organization_id", "villages", ["organization_id"])


def downgrade() -> None:
    op.drop_table("villages")