"""add payments table

Revision ID: 0008
Revises: 0007
"""

from alembic import op
import sqlalchemy as sa


revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "payments",

        sa.Column("id", sa.Integer(), nullable=False),

        sa.Column(
            "payment_no",
            sa.String(),
            nullable=True,
        ),

        sa.Column(
            "organization_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "farmer_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "procurement_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "amount",
            sa.Float(),
            nullable=False,
        ),

        sa.Column(
            "payment_date",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "payment_method",
            sa.String(),
            nullable=False,
        ),

        sa.Column(
            "reference_no",
            sa.String(),
            nullable=True,
        ),

        sa.Column(
            "status",
            sa.String(),
            nullable=True,
        ),

        sa.Column(
            "remarks",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.PrimaryKeyConstraint("id"),

        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_payment_org",
            ondelete="CASCADE",
        ),

        sa.ForeignKeyConstraint(
            ["farmer_id"],
            ["farmers.id"],
            name="fk_payment_farmer",
            ondelete="CASCADE",
        ),

        sa.ForeignKeyConstraint(
            ["procurement_id"],
            ["procurements.id"],
            name="fk_payment_procurement",
            ondelete="CASCADE",
        ),

        sa.UniqueConstraint(
            "payment_no",
            name="uq_payment_no",
        ),
    )

    op.create_index(
        op.f("ix_payments_payment_no"),
        "payments",
        ["payment_no"],
    )

    op.create_index(
        op.f("ix_payments_id"),
        "payments",
        ["id"],
    )


def downgrade():
    op.drop_table("payments")