"""add production and packing records linked to the item catalogue

Revision ID: 0017
Revises: 0016
"""
from alembic import op
import sqlalchemy as sa


revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "production_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("reference_no", sa.String(32), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("production_date", sa.Date(), nullable=False),
        sa.Column("finished_item_id", sa.Integer(), nullable=False),
        sa.Column("output_quantity", sa.Numeric(20, 6), nullable=False),
        sa.Column("output_unit", sa.String(20), nullable=False),
        sa.Column("output_base_quantity", sa.Numeric(20, 6), nullable=False),
        sa.Column("wastage_quantity", sa.Numeric(20, 6), nullable=False, server_default="0"),
        sa.Column("wastage_unit", sa.String(20), nullable=False),
        sa.Column("wastage_base_quantity", sa.Numeric(20, 6), nullable=False, server_default="0"),
        sa.Column("status", sa.String(16), nullable=False, server_default="POSTED"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["finished_item_id"], ["crop_masters.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("organization_id", "reference_no", name="uq_production_org_reference"),
        sa.UniqueConstraint("organization_id", "idempotency_key", name="uq_production_org_idempotency"),
        sa.CheckConstraint("output_quantity > 0", name="ck_production_output_positive"),
        sa.CheckConstraint("output_base_quantity > 0", name="ck_production_output_base_positive"),
        sa.CheckConstraint("wastage_quantity >= 0", name="ck_production_wastage_nonnegative"),
        sa.CheckConstraint("wastage_base_quantity >= 0", name="ck_production_wastage_base_nonnegative"),
        sa.CheckConstraint("status = 'POSTED'", name="ck_production_status_posted"),
    )
    op.create_index("ix_production_records_organization_id", "production_records", ["organization_id"])
    op.create_index("ix_production_records_production_date", "production_records", ["production_date"])
    op.create_index("ix_production_records_finished_item_id", "production_records", ["finished_item_id"])

    op.create_table(
        "production_inputs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("production_id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("input_type", sa.String(20), nullable=False),
        sa.Column("quantity", sa.Numeric(20, 6), nullable=False),
        sa.Column("unit", sa.String(20), nullable=False),
        sa.Column("base_quantity", sa.Numeric(20, 6), nullable=False),
        sa.ForeignKeyConstraint(["production_id"], ["production_records.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["item_id"], ["crop_masters.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("input_type IN ('RAW_MATERIAL','PACKAGING_MATERIAL')", name="ck_production_input_type"),
        sa.CheckConstraint("quantity > 0", name="ck_production_input_quantity_positive"),
        sa.CheckConstraint("base_quantity > 0", name="ck_production_input_base_positive"),
    )
    op.create_index("ix_production_inputs_production_id", "production_inputs", ["production_id"])
    op.create_index("ix_production_inputs_organization_id", "production_inputs", ["organization_id"])
    op.create_index("ix_production_inputs_item_id", "production_inputs", ["item_id"])


def downgrade():
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT 1 FROM inventory_ledger WHERE reference_type='PRODUCTION' LIMIT 1")).first():
        raise RuntimeError(
            "Cannot downgrade Production & Packing while production stock movements exist; "
            "export/reconcile the production history before removing its source tables."
        )
    op.drop_table("production_inputs")
    op.drop_table("production_records")
