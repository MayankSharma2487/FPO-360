"""Dependency-free Finance validation and migration-chain checks."""
import ast
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from app.schemas.financial_year import FinancialYearCreate
from app.schemas.journal import JournalLineIn
from app.services.finance_service import DEFAULT_ACCOUNTS


class FinanceFoundationTests(unittest.TestCase):
    def test_default_chart_contains_23_accounts(self):
        self.assertEqual(23, len(DEFAULT_ACCOUNTS))
        self.assertEqual(23, len({row[0] for row in DEFAULT_ACCOUNTS}))
        keys = [row[5] for row in DEFAULT_ACCOUNTS if row[5]]
        self.assertEqual(10, len(keys))
        self.assertEqual(len(keys), len(set(keys)))
        self.assertIn("RETAINED_EARNINGS", keys)

    def test_financial_year_rejects_invalid_range(self):
        with self.assertRaises(ValueError):
            FinancialYearCreate(name="FY", start_date=date(2026, 4, 1), end_date=date(2026, 4, 1))

    def test_financial_year_accepts_valid_range(self):
        result = FinancialYearCreate(name="FY 2026-27", start_date=date(2026, 4, 1), end_date=date(2027, 3, 31))
        self.assertEqual("FY 2026-27", result.name)

    def test_financial_year_requires_indian_fiscal_boundaries(self):
        with self.assertRaises(ValueError):
            FinancialYearCreate(name="Calendar FY", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))

    def test_journal_amounts_are_decimal_and_limited_to_two_places(self):
        line = JournalLineIn(account_id=1, debit=Decimal("12.34"), credit=0)
        self.assertEqual(Decimal("12.34"), line.debit)
        with self.assertRaises(ValueError):
            JournalLineIn(account_id=1, debit=Decimal("1.001"), credit=0)

    def test_journal_rejects_negative_amount(self):
        with self.assertRaises(ValueError):
            JournalLineIn(account_id=1, debit=Decimal("-1.00"), credit=0)

    def test_journal_line_requires_exactly_one_side(self):
        from app.schemas.journal import JournalCreate
        with self.assertRaises(ValueError):
            JournalCreate(entry_date=date(2026, 4, 1), financial_year_id=1, narration="Invalid", lines=[
                JournalLineIn(account_id=1, debit=Decimal("1.00"), credit=Decimal("1.00")),
                JournalLineIn(account_id=2, debit=Decimal("0.00"), credit=Decimal("0.00")),
            ])

    def test_journal_lines_keep_decimal_precision(self):
        line = JournalLineIn(account_id=1, debit=Decimal("123456789012.34"), credit=0)
        self.assertEqual(Decimal("123456789012.34"), line.debit)

    def test_migrations_form_one_chain_from_0010(self):
        root = Path(__file__).parents[1] / "migrations" / "versions"
        revisions = {}
        for path in root.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            values = {n.targets[0].id: ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id in {"revision", "down_revision"}}
            if values.get("revision") in {"0011", "0012"}:
                revisions[values["revision"]] = values.get("down_revision")
        self.assertEqual({"0011": "0010", "0012": "0011"}, revisions)

    def test_journal_database_metadata_has_composite_tenant_foreign_keys(self):
        from app.models.journal import JournalEntry, JournalLine
        entry_constraints = {constraint.name: constraint for constraint in JournalEntry.__table__.constraints}
        line_constraints = {constraint.name: constraint for constraint in JournalLine.__table__.constraints}
        self.assertEqual(["financial_year_id", "organization_id"], list(entry_constraints["fk_journal_financial_year_org"].column_keys))
        self.assertIn("fk_journal_line_entry_org", line_constraints)
        self.assertIn("fk_journal_line_account_org", line_constraints)

    def test_postgresql_migration_contains_atomic_post_and_immutability_guards(self):
        migration = (Path(__file__).parents[1] / "migrations" / "versions" / "0012_add_journal_tables.py").read_text(encoding="utf-8")
        self.assertIn("DEFERRABLE INITIALLY DEFERRED", migration)
        self.assertIn("A draft journal cannot be committed", migration)
        self.assertIn("Only draft journal lines may be changed", migration)
        self.assertIn("Posted' AND NEW.status='Void", migration)

    def test_finance_write_roles_allow_only_admins_and_accountant(self):
        from fastapi import HTTPException
        from app.api.finance_journals import WRITE
        from app.auth.dependencies import require_roles
        checker = require_roles(*WRITE)
        for role in ("Super Admin", "FPO Admin", "Accountant"):
            self.assertEqual(role, checker(current_user=SimpleNamespace(role=SimpleNamespace(name=role))).role.name)
        for role in ("Manager", "Viewer"):
            with self.assertRaises(HTTPException) as error:
                checker(current_user=SimpleNamespace(role=SimpleNamespace(name=role)))
            self.assertEqual(403, error.exception.status_code)

    def test_finance_read_roles_include_manager_and_viewer(self):
        from fastapi import HTTPException
        from app.api.finance_journals import READ
        from app.auth.dependencies import require_roles
        checker = require_roles(*READ)
        for role in ("Super Admin", "FPO Admin", "Accountant", "Manager", "Viewer"):
            self.assertEqual(role, checker(current_user=SimpleNamespace(role=SimpleNamespace(name=role))).role.name)
        with self.assertRaises(HTTPException):
            checker(current_user=SimpleNamespace(role=None))

    def test_financial_year_lock_is_admin_only(self):
        from fastapi import HTTPException
        from app.api.financial_years import lock_year
        from app.auth.dependencies import require_roles
        allowed = require_roles("Super Admin", "FPO Admin")
        for role in ("Super Admin", "FPO Admin"):
            self.assertEqual(role, allowed(current_user=SimpleNamespace(role=SimpleNamespace(name=role))).role.name)
        for role in ("Accountant", "Manager", "Viewer"):
            with self.assertRaises(HTTPException):
                allowed(current_user=SimpleNamespace(role=SimpleNamespace(name=role)))

    def test_finance_super_admin_requires_organization_scope(self):
        from fastapi import HTTPException
        from app.services.finance_service_base import FinanceServiceBase
        service = FinanceServiceBase(None)
        self.assertEqual(42, service._org(SimpleNamespace(organization_id=42)))
        with self.assertRaises(HTTPException) as error:
            service._org(SimpleNamespace(organization_id=None))
        self.assertEqual(403, error.exception.status_code)


if __name__ == "__main__":
    unittest.main()
