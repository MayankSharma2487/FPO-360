"""add procurement table

Revision ID: 0003_add_procurement_table
Revises: 0002_add_farmer_crops
Create Date: 2025-06-25 10:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import NUMERIC


revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('procurements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('procurement_no', sa.String(length=20), nullable=False),
        sa.Column('procurement_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('farmer_id', sa.Integer(), nullable=False),
        sa.Column('crop_id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=False, server_default='KG'),
        sa.Column('rate_per_unit', NUMERIC(precision=12, scale=2), nullable=False),
        sa.Column('total_amount', NUMERIC(precision=12, scale=2), nullable=False),
        sa.Column('quality_grade', sa.String(length=10), nullable=True),
        sa.Column('remarks', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.Column('warehouse_id', sa.String(50), nullable=True),
        sa.Column('lot_number', sa.String(50), nullable=True),
        sa.Column('vehicle_number', sa.String(50), nullable=True),
        sa.Column('receipt_no', sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('procurement_no', name='uq_procurement_no')
    )
    op.create_index(op.f('ix_procurements_procurement_no'), 'procurements', ['procurement_no'])
    op.create_index(op.f('ix_procurements_organization_id'), 'procurements', ['organization_id'])
    op.create_index(op.f('ix_procurements_farmer_id'), 'procurements', ['farmer_id'])
    op.create_index(op.f('ix_procurements_crop_id'), 'procurements', ['crop_id'])

    op.create_foreign_key('fk_procurement_farmer', 'procurements', 'farmers', ['farmer_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_procurement_crop', 'procurements', 'crop_masters', ['crop_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_procurement_org', 'procurements', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')


def downgrade():
    op.drop_table('procurements')