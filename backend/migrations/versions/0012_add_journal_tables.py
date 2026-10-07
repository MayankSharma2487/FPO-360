"""Finance journals with atomic draft-to-post lifecycle."""
from alembic import op
import sqlalchemy as sa

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "journal_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("journal_no", sa.String(30), nullable=False),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column("financial_year_id", sa.Integer(), nullable=False),
        sa.Column("narration", sa.Text(), nullable=False),
        sa.Column("source_type", sa.String(30), nullable=False),
        sa.Column("source_id", sa.Integer()),
        sa.Column("status", sa.String(10), nullable=False, server_default="Draft"),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("voided_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("voided_at", sa.DateTime(timezone=True)),
        sa.Column("void_reason", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "journal_no", name="uq_journal_org_no"),
        sa.UniqueConstraint("id", "organization_id", name="uq_journal_id_org"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["financial_year_id", "organization_id"], ["financial_years.id", "financial_years.organization_id"], name="fk_journal_financial_year_org"),
        sa.CheckConstraint("source_type IN ('MANUAL','OPENING')", name="ck_journal_source_type"),
        sa.CheckConstraint("source_id IS NULL", name="ck_journal_source_id"),
        sa.CheckConstraint("status IN ('Draft','Posted','Void')", name="ck_journal_status"),
    )
    op.create_index("ix_journal_entries_organization_id", "journal_entries", ["organization_id"])
    op.create_index("ix_journal_org_status_date", "journal_entries", ["organization_id", "status", "entry_date"])
    op.create_index("ix_journal_org_fy_date", "journal_entries", ["organization_id", "financial_year_id", "entry_date"])
    op.create_table(
        "journal_lines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("journal_entry_id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("line_no", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("debit", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("credit", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("party_type", sa.String(20)),
        sa.Column("party_id", sa.Integer()),
        sa.Column("line_narration", sa.Text()),
        sa.UniqueConstraint("journal_entry_id", "line_no", name="uq_journal_line_no"),
        sa.ForeignKeyConstraint(["journal_entry_id", "organization_id"], ["journal_entries.id", "journal_entries.organization_id"], ondelete="RESTRICT", name="fk_journal_line_entry_org"),
        sa.ForeignKeyConstraint(["account_id", "organization_id"], ["accounts.id", "accounts.organization_id"], ondelete="RESTRICT", name="fk_journal_line_account_org"),
        sa.CheckConstraint("(debit > 0 AND credit = 0) OR (credit > 0 AND debit = 0)", name="ck_journal_line_one_side"),
        sa.CheckConstraint("debit >= 0 AND credit >= 0", name="ck_journal_line_nonnegative"),
        sa.CheckConstraint("party_type IS NULL OR party_type IN ('FARMER','CUSTOMER')", name="ck_journal_party_type"),
        sa.CheckConstraint("(party_type IS NULL) = (party_id IS NULL)", name="ck_journal_party_pair"),
    )
    op.create_index("ix_journal_lines_org_account", "journal_lines", ["organization_id", "account_id"])
    op.create_index("ix_journal_lines_party", "journal_lines", ["organization_id", "party_type", "party_id"])

    # FY row lock serializes journal allocation and prevents journal/lock races.
    op.execute("""
    CREATE FUNCTION finance_validate_year() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE overlap_id integer;
    BEGIN
      IF TG_OP='DELETE' THEN
        IF OLD.is_locked THEN RAISE EXCEPTION 'Locked financial year cannot be deleted'; END IF;
        RETURN OLD;
      END IF;
      IF TG_OP='UPDATE' THEN
        IF NEW.organization_id IS DISTINCT FROM OLD.organization_id THEN RAISE EXCEPTION 'Financial year organization cannot change'; END IF;
        IF OLD.is_locked AND (NEW.name,NEW.start_date,NEW.end_date) IS DISTINCT FROM (OLD.name,OLD.start_date,OLD.end_date) THEN
          RAISE EXCEPTION 'Locked financial year cannot be changed';
        END IF;
      END IF;
      IF NEW.is_locked AND NEW.is_current THEN RAISE EXCEPTION 'Current financial year cannot be locked'; END IF;
      PERFORM 1 FROM organizations WHERE id=NEW.organization_id FOR UPDATE;
      IF EXTRACT(MONTH FROM NEW.start_date) <> 4 OR EXTRACT(DAY FROM NEW.start_date) <> 1
         OR EXTRACT(MONTH FROM NEW.end_date) <> 3 OR EXTRACT(DAY FROM NEW.end_date) <> 31
         OR EXTRACT(YEAR FROM NEW.end_date) <> EXTRACT(YEAR FROM NEW.start_date)+1 THEN
        RAISE EXCEPTION 'Financial years must run from 1 April through 31 March';
      END IF;
      SELECT id INTO overlap_id FROM financial_years
       WHERE organization_id=NEW.organization_id AND id IS DISTINCT FROM NEW.id
         AND start_date <= NEW.end_date AND end_date >= NEW.start_date LIMIT 1;
      IF overlap_id IS NOT NULL THEN RAISE EXCEPTION 'Financial years cannot overlap'; END IF;
      IF EXISTS(SELECT 1 FROM journal_entries WHERE organization_id=NEW.organization_id AND financial_year_id=NEW.id
        AND (entry_date < NEW.start_date OR entry_date > NEW.end_date)) THEN
        RAISE EXCEPTION 'Financial year dates cannot exclude existing journal entries';
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER trg_finance_year_validate BEFORE INSERT OR UPDATE OR DELETE ON financial_years
      FOR EACH ROW EXECUTE FUNCTION finance_validate_year();
    """)
    op.execute("""
    CREATE FUNCTION finance_check_posted_journal() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE st text; fy financial_years%ROWTYPE; dr numeric(14,2); cr numeric(14,2); n integer;
    BEGIN
      SELECT * INTO fy FROM financial_years WHERE id=NEW.financial_year_id FOR UPDATE;
      SELECT status INTO st FROM journal_entries WHERE id=NEW.id;
      IF st='Draft' THEN RAISE EXCEPTION 'A draft journal cannot be committed'; END IF;
      IF st='Posted' THEN
        IF fy.is_locked THEN RAISE EXCEPTION 'Financial year is locked'; END IF;
        IF NEW.entry_date < fy.start_date OR NEW.entry_date > fy.end_date THEN RAISE EXCEPTION 'Journal date is outside financial year'; END IF;
        SELECT COALESCE(SUM(debit),0),COALESCE(SUM(credit),0),COUNT(*) INTO dr,cr,n FROM journal_lines WHERE journal_entry_id=NEW.id;
        IF n < 2 OR dr <> cr THEN RAISE EXCEPTION 'Posted journal must have at least two balanced lines'; END IF;
      END IF;
      RETURN NULL;
    END $$;
    CREATE CONSTRAINT TRIGGER trg_journal_finalized AFTER INSERT OR UPDATE ON journal_entries
      DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION finance_check_posted_journal();
    """)
    op.execute("""
    CREATE FUNCTION finance_protect_journal() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Journal entries cannot be deleted'; END IF;
      IF OLD.status='Draft' AND NEW.status='Posted' THEN
        IF (to_jsonb(NEW)-'status'-'updated_at') <> (to_jsonb(OLD)-'status'-'updated_at') THEN RAISE EXCEPTION 'Posting cannot change journal accounting fields'; END IF;
        RETURN NEW;
      ELSIF OLD.status='Posted' AND NEW.status='Void' THEN
        IF (to_jsonb(NEW)-'status'-'voided_by'-'voided_at'-'void_reason'-'updated_at') <> (to_jsonb(OLD)-'status'-'voided_by'-'voided_at'-'void_reason'-'updated_at')
          OR NEW.voided_by IS NULL OR NEW.voided_at IS NULL OR length(trim(COALESCE(NEW.void_reason,'')))=0 THEN RAISE EXCEPTION 'Invalid journal void transition'; END IF;
        IF EXISTS(SELECT 1 FROM financial_years WHERE id=OLD.financial_year_id AND is_locked) THEN RAISE EXCEPTION 'Financial year is locked'; END IF;
        RETURN NEW;
      END IF;
      RAISE EXCEPTION 'Journal is immutable';
    END $$;
    CREATE TRIGGER trg_journal_immutable BEFORE UPDATE OR DELETE ON journal_entries
      FOR EACH ROW EXECUTE FUNCTION finance_protect_journal();
    """)
    op.execute("""
    CREATE FUNCTION finance_protect_journal_line() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE target_id integer; st text;
    BEGIN
      target_id := CASE WHEN TG_OP='DELETE' THEN OLD.journal_entry_id ELSE NEW.journal_entry_id END;
      SELECT status INTO st FROM journal_entries WHERE id=target_id FOR UPDATE;
      IF st IS DISTINCT FROM 'Draft' THEN RAISE EXCEPTION 'Only draft journal lines may be changed'; END IF;
      IF TG_OP='DELETE' THEN RETURN OLD; END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER trg_journal_line_immutable BEFORE INSERT OR UPDATE OR DELETE ON journal_lines
      FOR EACH ROW EXECUTE FUNCTION finance_protect_journal_line();
    """)
    op.execute("""
    CREATE FUNCTION finance_validate_party() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE sk text; party_org integer;
    BEGIN
      SELECT system_key INTO sk FROM accounts WHERE id=NEW.account_id AND organization_id=NEW.organization_id;
      IF sk='ACCOUNTS_RECEIVABLE' THEN
        IF NEW.party_type IS DISTINCT FROM 'CUSTOMER' OR NEW.party_id IS NULL OR NOT EXISTS
          (SELECT 1 FROM customers WHERE id=NEW.party_id AND organization_id=NEW.organization_id) THEN
          RAISE EXCEPTION 'Accounts receivable lines require a customer in the same organization'; END IF;
      ELSIF sk='ACCOUNTS_PAYABLE_FARMERS' THEN
        IF NEW.party_type IS DISTINCT FROM 'FARMER' OR NEW.party_id IS NULL OR NOT EXISTS
          (SELECT 1 FROM farmers WHERE id=NEW.party_id AND organization_id=NEW.organization_id) THEN
          RAISE EXCEPTION 'Farmer payable lines require a farmer in the same organization'; END IF;
      ELSIF NEW.party_type IS NOT NULL THEN RAISE EXCEPTION 'Party is not allowed on this account';
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER trg_journal_line_party BEFORE INSERT OR UPDATE ON journal_lines
      FOR EACH ROW EXECUTE FUNCTION finance_validate_party();
    CREATE FUNCTION finance_protect_system_account() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF OLD.system_key IS NOT NULL AND
        (NEW.account_code,NEW.account_name,NEW.account_type,NEW.account_group,NEW.account_subtype,NEW.system_key,NEW.is_active)
        IS DISTINCT FROM
        (OLD.account_code,OLD.account_name,OLD.account_type,OLD.account_group,OLD.account_subtype,OLD.system_key,OLD.is_active) THEN
        RAISE EXCEPTION 'System accounts cannot be changed or deactivated';
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER trg_system_account_immutable BEFORE UPDATE ON accounts
      FOR EACH ROW EXECUTE FUNCTION finance_protect_system_account();
    """)


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS trg_system_account_immutable ON accounts")
    op.execute("DROP FUNCTION IF EXISTS finance_protect_system_account()")
    op.execute("DROP TRIGGER IF EXISTS trg_journal_line_party ON journal_lines")
    op.execute("DROP FUNCTION IF EXISTS finance_validate_party()")
    op.execute("DROP TRIGGER IF EXISTS trg_journal_line_immutable ON journal_lines")
    op.execute("DROP FUNCTION IF EXISTS finance_protect_journal_line()")
    op.execute("DROP TRIGGER IF EXISTS trg_journal_immutable ON journal_entries")
    op.execute("DROP FUNCTION IF EXISTS finance_protect_journal()")
    op.execute("DROP TRIGGER IF EXISTS trg_journal_finalized ON journal_entries")
    op.execute("DROP FUNCTION IF EXISTS finance_check_posted_journal()")
    op.execute("DROP TRIGGER IF EXISTS trg_finance_year_validate ON financial_years")
    op.execute("DROP FUNCTION IF EXISTS finance_validate_year()")
    op.drop_table("journal_lines")
    op.drop_table("journal_entries")
