"""add item-aware inventory balances and append-only event metadata

Revision ID: 0015
Revises: 0014
"""
from alembic import op
import sqlalchemy as sa


revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def _preflight(bind):
    checks = (
        (
            "negative active inventory balances",
            "SELECT organization_id, crop_id FROM inventory_ledger WHERE is_active "
            "GROUP BY organization_id, crop_id HAVING SUM(CASE WHEN transaction_type='IN' "
            "THEN quantity ELSE -quantity END) < 0 LIMIT 1",
        ),
        (
            "inventory rows without a catalogue item",
            "SELECT l.id FROM inventory_ledger l LEFT JOIN crop_masters c ON c.id=l.crop_id "
            "WHERE c.id IS NULL LIMIT 1",
        ),
        (
            "legacy crop movement references a non-agricultural catalogue item",
            "SELECT l.id FROM inventory_ledger l JOIN crop_masters c ON c.id=l.crop_id "
            "WHERE c.item_type <> 'AGRICULTURAL_COMMODITY' LIMIT 1",
        ),
        (
            "duplicate linked inventory source references",
            "SELECT organization_id, reference_type, reference_id FROM inventory_ledger "
            "WHERE reference_type IN ('PROCUREMENT','SALE') AND reference_id IS NOT NULL "
            "GROUP BY organization_id, reference_type, reference_id "
            "HAVING COUNT(*) > 1 LIMIT 1",
        ),
        (
            "invalid inventory reference type or source identifier",
            "SELECT id,reference_type,reference_id FROM inventory_ledger WHERE "
            "reference_type NOT IN ('PROCUREMENT','SALE','MANUAL') "
            "OR (reference_type IN ('PROCUREMENT','SALE') AND reference_id IS NULL) "
            "OR (reference_type='MANUAL' AND reference_id IS NOT NULL) LIMIT 1",
        ),
        (
            "inventory quantities outside NUMERIC(20,6) range or precision",
            "SELECT id FROM inventory_ledger WHERE quantity::text IN ('NaN','Infinity','-Infinity') "
            "OR abs(quantity::numeric) >= 100000000000000 "
            "OR quantity::numeric <> round(quantity::numeric, 6) LIMIT 1",
        ),
        (
            "procurement or sales quantities outside NUMERIC(20,6) range or precision",
            "SELECT 'procurement',id FROM procurements WHERE quantity::text IN ('NaN','Infinity','-Infinity') "
            "OR abs(quantity::numeric) >= 100000000000000 "
            "OR quantity::numeric <> round(quantity::numeric, 6) UNION ALL "
            "SELECT 'sale',id FROM sales WHERE quantity::text IN ('NaN','Infinity','-Infinity') "
            "OR abs(quantity::numeric) >= 100000000000000 "
            "OR quantity::numeric <> round(quantity::numeric, 6) LIMIT 1",
        ),
        (
            "linked inventory movement does not match source organization or crop",
            "SELECT l.id FROM inventory_ledger l LEFT JOIN procurements p "
            "ON l.reference_type='PROCUREMENT' AND p.id=l.reference_id "
            "LEFT JOIN sales s ON l.reference_type='SALE' AND s.id=l.reference_id "
            "WHERE (l.reference_type='PROCUREMENT' AND (p.id IS NULL "
            "OR p.organization_id <> l.organization_id OR p.crop_id <> l.crop_id)) "
            "OR (l.reference_type='SALE' AND (s.id IS NULL "
            "OR s.organization_id <> l.organization_id OR s.crop_id <> l.crop_id)) LIMIT 1",
        ),
        (
            "linked inventory movement quantity differs from its source transaction",
            "SELECT l.id FROM inventory_ledger l LEFT JOIN procurements p "
            "ON l.reference_type='PROCUREMENT' AND p.id=l.reference_id "
            "LEFT JOIN sales s ON l.reference_type='SALE' AND s.id=l.reference_id "
            "WHERE (l.reference_type='PROCUREMENT' AND l.quantity::numeric <> p.quantity::numeric) "
            "OR (l.reference_type='SALE' AND l.quantity::numeric <> s.quantity::numeric) LIMIT 1",
        ),
        (
            "source/ledger active-state mismatch",
            "SELECT l.id FROM inventory_ledger l LEFT JOIN procurements p "
            "ON l.reference_type='PROCUREMENT' AND p.id=l.reference_id "
            "LEFT JOIN sales s ON l.reference_type='SALE' AND s.id=l.reference_id "
            "WHERE (l.reference_type='PROCUREMENT' AND (p.id IS NULL OR p.is_active <> l.is_active)) "
            "OR (l.reference_type='SALE' AND (s.id IS NULL OR s.is_active <> l.is_active)) LIMIT 1",
        ),
    )
    for description, query in checks:
        row = bind.execute(sa.text(query)).first()
        if row:
            raise RuntimeError(
                f"Inventory migration preflight failed: {description}; sample row {tuple(row)}. "
                "Reconcile the source data explicitly, then rerun the migration."
            )


def upgrade():
    bind = op.get_bind()
    _preflight(bind)

    op.add_column("inventory_ledger", sa.Column("item_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_inventory_ledger_item", "inventory_ledger", "crop_masters",
        ["item_id"], ["id"], ondelete="RESTRICT",
    )
    bind.execute(sa.text("UPDATE inventory_ledger SET item_id = crop_id"))
    op.alter_column("inventory_ledger", "item_id", nullable=False)
    op.alter_column("inventory_ledger", "crop_id", existing_type=sa.Integer(), nullable=True)
    op.create_check_constraint(
        "ck_inventory_legacy_crop_matches_item", "inventory_ledger",
        "crop_id IS NULL OR crop_id = item_id",
    )

    op.add_column("inventory_ledger", sa.Column("idempotency_key", sa.String(128), nullable=True))
    op.add_column(
        "inventory_ledger",
        sa.Column("source_revision", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column("inventory_ledger", sa.Column("reverses_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_inventory_ledger_reverses", "inventory_ledger", "inventory_ledger",
        ["reverses_id"], ["id"], ondelete="RESTRICT",
    )
    bind.execute(sa.text(
        "UPDATE inventory_ledger SET idempotency_key = 'LEGACY:' || id::text"
    ))
    op.alter_column("inventory_ledger", "idempotency_key", nullable=False)
    op.drop_constraint("uq_inventory_reference", "inventory_ledger", type_="unique")
    op.create_unique_constraint(
        "uq_inventory_idempotency", "inventory_ledger", ["organization_id", "idempotency_key"]
    )
    op.create_unique_constraint("uq_inventory_single_reversal", "inventory_ledger", ["reverses_id"])
    op.create_check_constraint(
        "ck_inventory_source_revision_positive", "inventory_ledger", "source_revision > 0"
    )

    op.alter_column(
        "inventory_ledger", "quantity", existing_type=sa.Float(),
        type_=sa.Numeric(20, 6), postgresql_using="quantity::numeric(20,6)",
    )
    op.alter_column(
        "procurements", "quantity", existing_type=sa.Float(),
        type_=sa.Numeric(20, 6), postgresql_using="quantity::numeric(20,6)",
    )
    op.alter_column(
        "sales", "quantity", existing_type=sa.Float(),
        type_=sa.Numeric(20, 6), postgresql_using="quantity::numeric(20,6)",
    )
    op.create_index(
        "ix_inventory_org_item_active", "inventory_ledger",
        ["organization_id", "item_id", "is_active"],
    )

    op.create_table(
        "inventory_balances",
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(20, 6), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["item_id"], ["crop_masters.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("organization_id", "item_id"),
        sa.CheckConstraint("quantity >= 0", name="ck_inventory_balance_nonnegative"),
    )
    bind.execute(sa.text(
        "INSERT INTO inventory_balances(organization_id,item_id,quantity) "
        "SELECT organization_id,item_id,SUM(CASE WHEN transaction_type='IN' THEN quantity "
        "ELSE -quantity END)::numeric(20,6) FROM inventory_ledger WHERE is_active "
        "GROUP BY organization_id,item_id"
    ))
    bind.execute(sa.text(
        "CREATE FUNCTION inventory_ledger_item_identity_guard() RETURNS trigger LANGUAGE plpgsql AS $$ "
        "DECLARE catalogue_type text; BEGIN "
        "SELECT item_type INTO catalogue_type FROM crop_masters WHERE id=NEW.item_id FOR SHARE; "
        "IF NOT FOUND THEN RAISE EXCEPTION 'Inventory catalogue item does not exist'; END IF; "
        "IF catalogue_type='AGRICULTURAL_COMMODITY' AND NEW.crop_id IS DISTINCT FROM NEW.item_id THEN "
        "RAISE EXCEPTION 'Agricultural inventory movement must retain its matching crop_id'; END IF; "
        "IF catalogue_type <> 'AGRICULTURAL_COMMODITY' AND NEW.crop_id IS NOT NULL THEN "
        "RAISE EXCEPTION 'Non-agricultural inventory movement cannot populate crop_id'; END IF; "
        "RETURN NEW; END $$"
    ))
    bind.execute(sa.text(
        "CREATE TRIGGER inventory_ledger_item_identity_guard_trigger BEFORE INSERT ON inventory_ledger "
        "FOR EACH ROW EXECUTE FUNCTION inventory_ledger_item_identity_guard()"
    ))
    bind.execute(sa.text(
        "CREATE FUNCTION inventory_ledger_reversal_guard() RETURNS trigger LANGUAGE plpgsql AS $$ "
        "DECLARE original inventory_ledger%ROWTYPE; BEGIN "
        "SELECT * INTO original FROM inventory_ledger WHERE id=NEW.reverses_id FOR KEY SHARE; "
        "IF NOT FOUND OR original.reverses_id IS NOT NULL "
        "OR original.organization_id <> NEW.organization_id "
        "OR original.item_id <> NEW.item_id "
        "OR original.reference_type <> NEW.reference_type "
        "OR original.reference_id IS DISTINCT FROM NEW.reference_id "
        "OR original.quantity <> NEW.quantity "
        "OR original.transaction_type = NEW.transaction_type THEN "
        "RAISE EXCEPTION 'Invalid inventory reversal'; END IF; RETURN NEW; END $$"
    ))
    bind.execute(sa.text(
        "CREATE TRIGGER inventory_ledger_reversal_guard_trigger BEFORE INSERT ON inventory_ledger "
        "FOR EACH ROW WHEN (NEW.reverses_id IS NOT NULL) "
        "EXECUTE FUNCTION inventory_ledger_reversal_guard()"
    ))
    bind.execute(sa.text(
        "CREATE FUNCTION inventory_ledger_immutable_guard() RETURNS trigger LANGUAGE plpgsql AS $$ "
        "BEGIN RAISE EXCEPTION 'Inventory ledger entries are immutable; post a reversal'; END $$"
    ))
    bind.execute(sa.text(
        "CREATE TRIGGER inventory_ledger_immutable_guard_trigger BEFORE UPDATE OR DELETE ON inventory_ledger "
        "FOR EACH ROW EXECUTE FUNCTION inventory_ledger_immutable_guard()"
    ))


def downgrade():
    bind = op.get_bind()
    unsafe = bind.execute(sa.text(
        "SELECT id FROM inventory_ledger WHERE crop_id IS NULL OR crop_id <> item_id "
        "OR reverses_id IS NOT NULL OR idempotency_key <> 'LEGACY:' || id::text "
        "OR source_revision <> 1 LIMIT 1"
    )).first()
    duplicate_source = bind.execute(sa.text(
        "SELECT organization_id,reference_type,reference_id FROM inventory_ledger "
        "WHERE reference_id IS NOT NULL GROUP BY organization_id,reference_type,reference_id "
        "HAVING COUNT(*) > 1 LIMIT 1"
    )).first()
    non_roundtrip = bind.execute(sa.text(
        "SELECT id FROM inventory_ledger WHERE quantity::double precision::numeric <> quantity LIMIT 1"
    )).first()
    source_non_roundtrip = bind.execute(sa.text(
        "SELECT 'procurement',id FROM procurements "
        "WHERE quantity::double precision::numeric <> quantity LIMIT 1"
    )).first()
    if source_non_roundtrip is None:
        source_non_roundtrip = bind.execute(sa.text(
            "SELECT 'sale',id FROM sales "
            "WHERE quantity::double precision::numeric <> quantity LIMIT 1"
        )).first()
    mismatch = bind.execute(sa.text(
        "SELECT b.organization_id,b.item_id FROM inventory_balances b LEFT JOIN "
        "(SELECT organization_id,item_id,SUM(CASE WHEN transaction_type='IN' THEN quantity "
        "ELSE -quantity END) AS quantity FROM inventory_ledger WHERE is_active "
        "GROUP BY organization_id,item_id) l USING (organization_id,item_id) "
        "WHERE b.quantity <> COALESCE(l.quantity,0) LIMIT 1"
    )).first()
    if unsafe or duplicate_source or non_roundtrip or source_non_roundtrip or mismatch:
        raise RuntimeError(
            "Cannot downgrade inventory without losing generic-item identity, reversal/idempotency "
            "history, exact numeric quantities, or source uniqueness. Preserve the upgraded schema "
            "or perform an operator-reviewed export and migration."
        )

    op.execute("DROP TRIGGER inventory_ledger_immutable_guard_trigger ON inventory_ledger")
    op.execute("DROP FUNCTION inventory_ledger_immutable_guard()")
    op.execute("DROP TRIGGER inventory_ledger_item_identity_guard_trigger ON inventory_ledger")
    op.execute("DROP FUNCTION inventory_ledger_item_identity_guard()")
    op.execute("DROP TRIGGER inventory_ledger_reversal_guard_trigger ON inventory_ledger")
    op.execute("DROP FUNCTION inventory_ledger_reversal_guard()")
    op.drop_table("inventory_balances")
    op.drop_index("ix_inventory_org_item_active", table_name="inventory_ledger")
    op.drop_constraint("ck_inventory_source_revision_positive", "inventory_ledger", type_="check")
    op.drop_constraint("uq_inventory_single_reversal", "inventory_ledger", type_="unique")
    op.drop_constraint("uq_inventory_idempotency", "inventory_ledger", type_="unique")
    op.create_unique_constraint(
        "uq_inventory_reference", "inventory_ledger",
        ["organization_id", "reference_type", "reference_id"],
    )
    op.drop_constraint("fk_inventory_ledger_reverses", "inventory_ledger", type_="foreignkey")
    op.drop_constraint("ck_inventory_legacy_crop_matches_item", "inventory_ledger", type_="check")
    op.drop_constraint("fk_inventory_ledger_item", "inventory_ledger", type_="foreignkey")
    op.drop_column("inventory_ledger", "reverses_id")
    op.drop_column("inventory_ledger", "source_revision")
    op.drop_column("inventory_ledger", "idempotency_key")
    op.alter_column("inventory_ledger", "crop_id", existing_type=sa.Integer(), nullable=False)
    op.drop_column("inventory_ledger", "item_id")
    op.alter_column(
        "inventory_ledger", "quantity", existing_type=sa.Numeric(20, 6),
        type_=sa.Float(), postgresql_using="quantity::double precision",
    )
    op.alter_column(
        "procurements", "quantity", existing_type=sa.Numeric(20, 6),
        type_=sa.Float(), postgresql_using="quantity::double precision",
    )
    op.alter_column(
        "sales", "quantity", existing_type=sa.Numeric(20, 6),
        type_=sa.Float(), postgresql_using="quantity::double precision",
    )
