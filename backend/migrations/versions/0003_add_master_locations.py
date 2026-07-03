"""add master locations tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-17

"""
from alembic import op
import sqlalchemy as sa


revision = "0003"
down_revision = "0002"


def upgrade():
    op.create_table(
        "master_states",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("state_name", sa.String(100), nullable=False, unique=True),
        sa.Column("state_code", sa.String(10), nullable=True, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "master_districts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("district_name", sa.String(150), nullable=False),
        sa.Column("state_id", sa.Integer(), sa.ForeignKey("master_states.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "master_blocks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("block_name", sa.String(150), nullable=False),
        sa.Column("district_id", sa.Integer(), sa.ForeignKey("master_districts.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("master_blocks")
    op.drop_table("master_districts")
    op.drop_table("master_states")