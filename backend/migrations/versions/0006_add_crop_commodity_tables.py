"""add crop and farmer crop tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-19
"""
from alembic import op
import sqlalchemy as sa


revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'crop_masters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('crop_code', sa.String(length=50), nullable=False),
        sa.Column('crop_name', sa.String(length=150), nullable=False),
        sa.Column('crop_category', sa.String(length=100), nullable=True),
        sa.Column('unit', sa.String(length=20), nullable=False, server_default='Kg'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('crop_code', name='uq_crop_masters_crop_code')
    )
    op.create_index('ix_crop_masters_id', 'crop_masters', ['id'])
    op.create_index('ix_crop_masters_crop_code', 'crop_masters', ['crop_code'])

    op.create_table(
        'farmer_crops',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('farmer_id', sa.Integer(), nullable=False),
        sa.Column('crop_id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('season', sa.String(length=50), nullable=True),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('area_acres', sa.Float(), nullable=True),
        sa.Column('sowing_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('harvest_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expected_yield', sa.Float(), nullable=True),
        sa.Column('actual_yield', sa.Float(), nullable=True),
        sa.Column('remarks', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['farmer_id'], ['farmers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['crop_id'], ['crop_masters.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_farmer_crops_id', 'farmer_crops', ['id'])


def downgrade():
    op.drop_table('farmer_crops')
    op.drop_table('crop_masters')