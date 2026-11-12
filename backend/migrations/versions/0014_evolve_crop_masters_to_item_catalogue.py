"""evolve shared crop master into an organization-aware item catalogue

Revision ID: 0014
Revises: 0013
"""
from alembic import op
import sqlalchemy as sa


revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade():
    # Existing IDs, crop columns and foreign-key references remain unchanged.
    # The defaults classify every pre-existing crop as a shared commodity
    # whose canonical stock unit is KG, matching inventory_ledger storage.
    op.add_column(
        "crop_masters",
        sa.Column(
            "item_type",
            sa.String(length=40),
            nullable=False,
            server_default="AGRICULTURAL_COMMODITY",
        ),
    )
    op.add_column(
        "crop_masters",
        sa.Column("organization_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "crop_masters",
        sa.Column("base_unit", sa.String(length=20), nullable=False, server_default="KG"),
    )
    op.add_column("crop_masters", sa.Column("description", sa.Text(), nullable=True))
    op.create_foreign_key(
        "fk_crop_masters_organization",
        "crop_masters",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_check_constraint(
        "ck_crop_masters_item_type",
        "crop_masters",
        "item_type IN ('AGRICULTURAL_COMMODITY', 'PURCHASED_PRODUCT', "
        "'RAW_MATERIAL', 'PACKAGING_MATERIAL', 'FINISHED_GOOD')",
    )
    op.create_check_constraint(
        "ck_crop_masters_base_unit",
        "crop_masters",
        "base_unit IN ('KG', 'G', 'QUINTAL', 'TON', 'L', 'ML', 'PCS')",
    )
    op.create_check_constraint(
        "ck_crop_masters_commercial_owner",
        "crop_masters",
        "item_type = 'AGRICULTURAL_COMMODITY' OR organization_id IS NOT NULL",
    )
    op.create_index(
        "ix_crop_masters_organization_id",
        "crop_masters",
        ["organization_id"],
    )
    op.create_index(
        "ix_crop_masters_org_type_active",
        "crop_masters",
        ["organization_id", "item_type", "is_active"],
    )


def downgrade():
    # Refuse to discard catalogue ownership/type data. An operator must first
    # explicitly migrate or remove commercial items before downgrading.
    bind = op.get_bind()
    commercial_rows = bind.execute(
        sa.text(
            "SELECT count(*) FROM crop_masters "
            "WHERE item_type <> 'AGRICULTURAL_COMMODITY' OR organization_id IS NOT NULL"
        )
    ).scalar_one()
    if commercial_rows:
        raise RuntimeError(
            "Cannot downgrade item catalogue while commercial or organization-owned items exist"
        )

    op.drop_index("ix_crop_masters_org_type_active", table_name="crop_masters")
    op.drop_index("ix_crop_masters_organization_id", table_name="crop_masters")
    op.drop_constraint("ck_crop_masters_commercial_owner", "crop_masters", type_="check")
    op.drop_constraint("ck_crop_masters_base_unit", "crop_masters", type_="check")
    op.drop_constraint("ck_crop_masters_item_type", "crop_masters", type_="check")
    op.drop_constraint("fk_crop_masters_organization", "crop_masters", type_="foreignkey")
    op.drop_column("crop_masters", "description")
    op.drop_column("crop_masters", "base_unit")
    op.drop_column("crop_masters", "organization_id")
    op.drop_column("crop_masters", "item_type")
