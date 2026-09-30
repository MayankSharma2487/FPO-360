"""create inventory ledger

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "inventory_ledger",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "crop_id",
            sa.Integer(),
            sa.ForeignKey("crop_masters.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("transaction_type", sa.String(length=10), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("reference_type", sa.String(length=20), nullable=False),
        sa.Column("reference_id", sa.Integer(), nullable=True),
        sa.Column("remarks", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.CheckConstraint(
            "transaction_type IN ('IN', 'OUT')",
            name="ck_inventory_txn_type",
        ),
        sa.CheckConstraint(
            "quantity > 0",
            name="ck_inventory_quantity_positive",
        ),
        sa.UniqueConstraint(
            "organization_id",
            "reference_type",
            "reference_id",
            name="uq_inventory_reference",
        ),
    )

    op.create_index(
        "ix_inventory_ledger_organization_id",
        "inventory_ledger",
        ["organization_id"],
    )
    op.create_index(
        "ix_inventory_ledger_crop_id",
        "inventory_ledger",
        ["crop_id"],
    )
    op.create_index(
        "ix_inventory_ledger_transaction_type",
        "inventory_ledger",
        ["transaction_type"],
    )
    op.create_index(
        "ix_inventory_ledger_reference_type",
        "inventory_ledger",
        ["reference_type"],
    )
    op.create_index(
        "ix_inventory_ledger_reference_id",
        "inventory_ledger",
        ["reference_id"],
    )
    op.create_index(
        "ix_inventory_ledger_is_active",
        "inventory_ledger",
        ["is_active"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_inventory_ledger_is_active",
        table_name="inventory_ledger",
    )
    op.drop_index(
        "ix_inventory_ledger_reference_id",
        table_name="inventory_ledger",
    )
    op.drop_index(
        "ix_inventory_ledger_reference_type",
        table_name="inventory_ledger",
    )
    op.drop_index(
        "ix_inventory_ledger_transaction_type",
        table_name="inventory_ledger",
    )
    op.drop_index(
        "ix_inventory_ledger_crop_id",
        table_name="inventory_ledger",
    )
    op.drop_index(
        "ix_inventory_ledger_organization_id",
        table_name="inventory_ledger",
    )
    op.drop_table("inventory_ledger")
