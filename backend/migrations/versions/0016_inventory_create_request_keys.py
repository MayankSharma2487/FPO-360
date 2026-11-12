"""add transactional request idempotency for procurement and sales creates

Revision ID: 0016
Revises: 0015
"""
from alembic import op
import sqlalchemy as sa


revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "inventory_create_requests",
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("operation", sa.String(length=32), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint(
            "organization_id", "operation", "idempotency_key",
            name="pk_inventory_create_requests",
        ),
        sa.CheckConstraint(
            "operation IN ('PROCUREMENT_CREATE', 'SALE_CREATE')",
            name="ck_inventory_create_request_operation",
        ),
        sa.CheckConstraint("source_id > 0", name="ck_inventory_create_request_source_positive"),
    )


def downgrade():
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT 1 FROM inventory_create_requests LIMIT 1")).first():
        raise RuntimeError(
            "Cannot downgrade while Procurement/Sales request idempotency records exist; "
            "removing them would permit duplicate source transactions on retry."
        )
    op.drop_table("inventory_create_requests")
