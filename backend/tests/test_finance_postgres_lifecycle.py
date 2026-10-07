"""PostgreSQL trigger integration test; requires FINANCE_TEST_DATABASE_URL.

All DDL and test rows live in one transaction and are rolled back. The URL must
point to a PostgreSQL test database where the role can create a temporary schema.
"""
import os
import unittest
from datetime import date
from decimal import Decimal
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from app.services.finance_report_service import FinanceReportService
from app.services.finance_setup_service import FinanceSetupService
from app.services.journal_service import JournalService
from app.repositories.journal_repository import JournalRepository
from app.models.account import Account
from app.schemas.journal import JournalCreate, JournalLineIn


class PostgreSQLJournalLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        url = os.getenv("FINANCE_TEST_DATABASE_URL")
        if not url:
            raise unittest.SkipTest("FINANCE_TEST_DATABASE_URL is not configured")
        cls.engine = create_engine(url)
        if cls.engine.dialect.name != "postgresql":
            cls.engine.dispose()
            raise unittest.SkipTest("Finance trigger integration tests require PostgreSQL")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "engine"):
            cls.engine.dispose()

    def setUp(self):
        self.conn = self.engine.connect()
        self.transaction = self.conn.begin()
        self.schema = "finance_test_" + uuid4().hex
        self.conn.execute(text(f'CREATE SCHEMA "{self.schema}"'))
        self.conn.execute(text(f'SET LOCAL search_path TO "{self.schema}"'))
        for ddl in (
            "CREATE TABLE organizations(id integer PRIMARY KEY, organization_name varchar(255) NOT NULL, registration_number varchar(100) NOT NULL UNIQUE, pan_number varchar(20), gst_number varchar(20), fssai_number varchar(20), state varchar(100), district varchar(100))",
            "CREATE TABLE users(id integer PRIMARY KEY)",
            "CREATE TABLE customers(id integer PRIMARY KEY, organization_id integer NOT NULL)",
            "CREATE TABLE farmers(id integer PRIMARY KEY, organization_id integer NOT NULL)",
        ):
            self.conn.execute(text(ddl))

        for revision in ("0011_add_financial_years_and_accounts.py", "0012_add_journal_tables.py"):
            path = Path(__file__).parents[1] / "migrations" / "versions" / revision
            spec = spec_from_file_location("finance_migration_test_" + revision[:4], path)
            migration = module_from_spec(spec)
            spec.loader.exec_module(migration)
            with Operations.context(MigrationContext.configure(self.conn)):
                migration.upgrade()

    def tearDown(self):
        self.transaction.rollback()
        self.conn.close()

    def _setup_organization(self, organization_id, user_id, financial_year_id, locked=False):
        self.conn.execute(text("INSERT INTO organizations(id,organization_name,registration_number) VALUES (:id,:name,:reg)"),
                          {"id": organization_id, "name": f"FPO {organization_id}", "reg": f"REG-{organization_id}"})
        self.conn.execute(text("INSERT INTO users VALUES (:id)"), {"id": user_id})
        self.conn.execute(text("INSERT INTO financial_years(id,organization_id,name,start_date,end_date,is_locked) VALUES (:fy,:org,'FY 2026-27','2026-04-01','2027-03-31',:locked)"),
                          {"fy": financial_year_id, "org": organization_id, "locked": locked})
        self.conn.execute(text("INSERT INTO accounts(id,organization_id,account_code,account_name,account_type,account_group) VALUES (:debit,:org,'D','Debit','Asset','Test'),(:credit,:org,'C','Credit','Asset','Test')"),
                          {"debit": organization_id * 10 + 1, "credit": organization_id * 10 + 2, "org": organization_id})

    def _post_balanced(self, organization_id, user_id, financial_year_id, credit="10.00"):
        journal_id = self.conn.execute(text("INSERT INTO journal_entries(organization_id,journal_no,entry_date,financial_year_id,narration,source_type,status,created_by) VALUES (:org,:number,'2026-04-01',:fy,'test','MANUAL','Draft',:user) RETURNING id"),
                                       {"org": organization_id, "number": f"JV-{organization_id}", "fy": financial_year_id, "user": user_id}).scalar_one()
        self.conn.execute(text("INSERT INTO journal_lines(journal_entry_id,organization_id,line_no,account_id,debit,credit) VALUES (:journal,:org,1,:debit,10,0),(:journal,:org,2,:credit,0,:amount)"),
                          {"journal": journal_id, "org": organization_id, "debit": organization_id * 10 + 1,
                           "credit": organization_id * 10 + 2, "amount": credit})
        self.conn.execute(text("UPDATE journal_entries SET status='Posted' WHERE id=:journal"), {"journal": journal_id})
        return journal_id

    def _assert_database_rejects(self, action):
        savepoint = self.conn.begin_nested()
        try:
            action()
        except DBAPIError:
            savepoint.rollback()
            return
        savepoint.rollback()
        self.fail("PostgreSQL should have rejected the invalid finance mutation")

    def _create_posted(self, org, user, fy, journal_no, entry_date, lines, source_type="MANUAL"):
        journal_id = self.conn.execute(text("INSERT INTO journal_entries(organization_id,journal_no,entry_date,financial_year_id,narration,source_type,status,created_by) VALUES (:org,:number,:date,:fy,'report test',:source_type,'Draft',:user) RETURNING id"),
            {"org": org, "number": journal_no, "date": entry_date, "fy": fy, "user": user, "source_type": source_type}).scalar_one()
        for line_no, (account_id, debit, credit) in enumerate(lines, 1):
            self.conn.execute(text("INSERT INTO journal_lines(journal_entry_id,organization_id,line_no,account_id,debit,credit) VALUES (:journal,:org,:line,:account,:debit,:credit)"),
                {"journal": journal_id, "org": org, "line": line_no, "account": account_id, "debit": debit, "credit": credit})
        self.conn.execute(text("UPDATE journal_entries SET status='Posted' WHERE id=:id"), {"id": journal_id})
        return journal_id

    def test_balanced_post_immutability_void_locking_and_tenant_fk(self):
        savepoint = self.conn.begin_nested()
        self.conn.execute(text("SET CONSTRAINTS ALL DEFERRED"))
        self._setup_organization(1, 101, 1001)
        journal_id = self._post_balanced(1, 101, 1001)
        self.conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        self.assertEqual("Posted", self.conn.execute(text("SELECT status FROM journal_entries WHERE id=:id"), {"id": journal_id}).scalar_one())
        savepoint.commit()

        self._assert_database_rejects(lambda: self.conn.execute(text("UPDATE journal_lines SET debit=11 WHERE journal_entry_id=:id AND line_no=1"), {"id": journal_id}))
        self._assert_database_rejects(lambda: self.conn.execute(text("UPDATE journal_entries SET narration='tampered' WHERE id=:id"), {"id": journal_id}))

        savepoint = self.conn.begin_nested()
        self.conn.execute(text("SET CONSTRAINTS ALL DEFERRED"))
        self.conn.execute(text("UPDATE journal_entries SET status='Void',voided_by=101,voided_at=now(),void_reason='test reversal' WHERE id=:id"), {"id": journal_id})
        self.conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        self.assertEqual("Void", self.conn.execute(text("SELECT status FROM journal_entries WHERE id=:id"), {"id": journal_id}).scalar_one())
        savepoint.commit()
        self._assert_database_rejects(lambda: self.conn.execute(text("UPDATE journal_entries SET status='Void',voided_by=101,voided_at=now(),void_reason='again' WHERE id=:id"), {"id": journal_id}))

        savepoint = self.conn.begin_nested()
        self.conn.execute(text("SET CONSTRAINTS ALL DEFERRED"))
        self._setup_organization(7, 107, 1007)
        one_line = self.conn.execute(text("INSERT INTO journal_entries(organization_id,journal_no,entry_date,financial_year_id,narration,source_type,status,created_by) VALUES (7,'JV-7','2026-04-01',1007,'one line','MANUAL','Draft',107) RETURNING id")).scalar_one()
        self.conn.execute(text("INSERT INTO journal_lines(journal_entry_id,organization_id,line_no,account_id,debit,credit) VALUES (:journal,7,1,71,10,0)"), {"journal": one_line})
        self.conn.execute(text("UPDATE journal_entries SET status='Posted' WHERE id=:journal"), {"journal": one_line})
        self._assert_database_rejects(lambda: self.conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE")))
        savepoint.rollback()

        savepoint = self.conn.begin_nested()
        self.conn.execute(text("SET CONSTRAINTS ALL DEFERRED"))
        self._setup_organization(8, 108, 1008)
        bad_line = self.conn.execute(text("INSERT INTO journal_entries(organization_id,journal_no,entry_date,financial_year_id,narration,source_type,status,created_by) VALUES (8,'JV-8','2026-04-01',1008,'invalid line','MANUAL','Draft',108) RETURNING id")).scalar_one()
        self._assert_database_rejects(lambda: self.conn.execute(text("INSERT INTO journal_lines(journal_entry_id,organization_id,line_no,account_id,debit,credit) VALUES (:journal,8,1,81,10,10)"), {"journal": bad_line}))
        savepoint.rollback()

        savepoint = self.conn.begin_nested()
        self.conn.execute(text("SET CONSTRAINTS ALL DEFERRED"))
        self._setup_organization(2, 102, 1002)
        self._post_balanced(2, 102, 1002, credit="9.00")
        self._assert_database_rejects(lambda: self.conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE")))
        savepoint.rollback()

        savepoint = self.conn.begin_nested()
        self.conn.execute(text("SET CONSTRAINTS ALL DEFERRED"))
        self._setup_organization(3, 103, 1003, locked=True)
        self._post_balanced(3, 103, 1003)
        self._assert_database_rejects(lambda: self.conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE")))
        savepoint.rollback()

        savepoint = self.conn.begin_nested()
        self.conn.execute(text("SET CONSTRAINTS ALL DEFERRED"))
        self._setup_organization(4, 104, 1004)
        self._setup_organization(5, 105, 1005)
        self._assert_database_rejects(lambda: self.conn.execute(text("INSERT INTO journal_entries(organization_id,journal_no,entry_date,financial_year_id,narration,source_type,status) VALUES (5,'JV-CROSS','2026-04-01',1004,'cross tenant','MANUAL','Draft')")))
        savepoint.rollback()

        savepoint = self.conn.begin_nested()
        self.conn.execute(text("SET CONSTRAINTS ALL DEFERRED"))
        self._setup_organization(15, 115, 1015)
        self._setup_organization(16, 116, 1016)
        foreign_journal = self.conn.execute(text("INSERT INTO journal_entries(organization_id,journal_no,entry_date,financial_year_id,narration,source_type,status) VALUES (15,'JV-LINE-TENANT','2026-04-01',1015,'cross tenant line','MANUAL','Draft') RETURNING id")).scalar_one()
        self._assert_database_rejects(lambda: self.conn.execute(text("INSERT INTO journal_lines(journal_entry_id,organization_id,line_no,account_id,debit,credit) VALUES (:journal,15,1,161,10,0)"), {"journal": foreign_journal}))
        self._assert_database_rejects(lambda: self.conn.execute(text("INSERT INTO journal_lines(journal_entry_id,organization_id,line_no,account_id,debit,credit) VALUES (:journal,16,1,161,10,0)"), {"journal": foreign_journal}))
        savepoint.rollback()

        savepoint = self.conn.begin_nested()
        self.conn.execute(text("SET CONSTRAINTS ALL DEFERRED"))
        self._setup_organization(6, 106, 1006)
        locked_journal = self._post_balanced(6, 106, 1006)
        self.conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        savepoint.commit()
        savepoint = self.conn.begin_nested()
        self.conn.execute(text("UPDATE financial_years SET is_locked=true WHERE id=1006"))
        self._assert_database_rejects(lambda: self.conn.execute(text("UPDATE journal_entries SET status='Void',voided_by=106,voided_at=now(),void_reason='period locked' WHERE id=:id"), {"id": locked_journal}))
        savepoint.rollback()

    def test_general_ledger_and_trial_balance_follow_fiscal_years_and_void_status(self):
        self.conn.execute(text("INSERT INTO organizations(id,organization_name,registration_number) VALUES (9,'FPO 9','REG-9')"))
        self.conn.execute(text("INSERT INTO users VALUES (109)"))
        self.conn.execute(text("INSERT INTO financial_years(id,organization_id,name,start_date,end_date) VALUES (9005,9,'FY 2025-26','2025-04-01','2026-03-31'),(9006,9,'FY 2026-27','2026-04-01','2027-03-31')"))
        self.conn.execute(text("UPDATE financial_years SET is_current=true WHERE id=9006"))
        self.conn.execute(text("INSERT INTO accounts(id,organization_id,account_code,account_name,account_type,account_group,system_key) VALUES (910,9,'1001','Cash','Asset','Cash',NULL),(911,9,'4001','Sales','Income','Income',NULL),(912,9,'5101','Expenses','Expense','Expense',NULL),(913,9,'3002','Retained earnings','Equity','Equity','RETAINED_EARNINGS')"))
        self._create_posted(9,109,9005,'JV-H1','2025-06-01',[(910,100,0),(911,0,100)])
        self._create_posted(9,109,9005,'JV-H2','2026-03-31',[(912,20,0),(910,0,20)])
        self._create_posted(9,109,9006,'JV-C1','2026-04-02',[(910,10,0),(911,0,10)])
        voided = self._create_posted(9,109,9006,'JV-C2','2026-04-03',[(910,5,0),(911,0,5)])
        self.conn.execute(text("UPDATE journal_entries SET status='Void',voided_by=109,voided_at=now(),void_reason='report exclusion' WHERE id=:id"), {"id": voided})
        self._create_posted(9,109,9006,'JV-C3','2026-04-10',[(910,7,0),(911,0,7)])
        self.conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))

        import app.main  # register the existing ORM model relationships before queries
        with Session(bind=self.conn, join_transaction_mode="create_savepoint") as session:
            reports = FinanceReportService(session)
            user = type("FinanceUser", (), {"organization_id": 9})()
            ledger = reports.general_ledger(user, 911, date(2026,4,1), date(2026,4,3))
            self.assertEqual(Decimal("0.00"), ledger["opening_balance"])
            self.assertEqual(1, len(ledger["lines"]))
            self.assertEqual("JV-C1", ledger["lines"][0]["journal_no"])
            self.assertEqual("Credit", ledger["lines"][0]["balance_side"])
            self.assertEqual(Decimal("10.00"), ledger["lines"][0]["running_balance"])
            trial = reports.trial_balance(user, 9006, date(2026,4,2), False)
            self.assertEqual(trial["debit_total"], trial["credit_total"])
            self.assertEqual(Decimal("90.00"), trial["debit_total"])
            self.assertEqual(Decimal("90.00"), trial["credit_total"])
            retained_line = next(account for account in trial["accounts"] if account["account_code"] == "3002")
            self.assertEqual(Decimal("80.00"), retained_line["credit"])
            self.assertFalse(any(account["account_code"] == "5101" for account in trial["accounts"]))
            full = reports.trial_balance(user, 9006, date(2026,4,2), True)
            self.assertEqual(4, len(full["accounts"]))

    def test_trial_balance_does_not_repeat_retained_earnings_after_closing_journal(self):
        import app.main
        self.conn.execute(text("INSERT INTO organizations(id,organization_name,registration_number) VALUES (20,'FPO 20','REG-20')"))
        self.conn.execute(text("INSERT INTO users VALUES (120)"))
        self.conn.execute(text("INSERT INTO financial_years(id,organization_id,name,start_date,end_date) VALUES (2005,20,'FY 2025-26','2025-04-01','2026-03-31'),(2006,20,'FY 2026-27','2026-04-01','2027-03-31')"))
        self.conn.execute(text("INSERT INTO accounts(id,organization_id,account_code,account_name,account_type,account_group,system_key) VALUES (201,20,'1001','Cash','Asset','Cash',NULL),(202,20,'4001','Sales','Income','Income',NULL),(203,20,'5101','Expenses','Expense','Expense',NULL),(204,20,'3002','Retained earnings','Equity','Equity','RETAINED_EARNINGS')"))
        self._create_posted(20,120,2005,'JV-OLD-1','2025-06-01',[(201,100,0),(202,0,100)])
        self._create_posted(20,120,2005,'JV-OLD-2','2026-03-31',[(203,20,0),(201,0,20)])
        self._create_posted(20,120,2005,'JV-CLOSE','2026-03-31',[(202,100,0),(203,0,20),(204,0,80)])
        self._create_posted(20,120,2006,'JV-NEW','2026-04-02',[(201,25,0),(202,0,25)])
        self.conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        with Session(bind=self.conn, join_transaction_mode="create_savepoint") as session:
            reports = FinanceReportService(session)
            user = SimpleNamespace(organization_id=20)
            trial = reports.trial_balance(user,2006,date(2026,4,2),False)
            retained = next(row for row in trial["accounts"] if row["account_code"]=="3002")
            self.assertEqual(Decimal("80.00"),retained["credit"])
            self.assertEqual(trial["debit_total"],trial["credit_total"])
            self.assertEqual(Decimal("105.00"),trial["debit_total"])

    def test_three_year_trial_balance_subtracts_prior_retained_transfers(self):
        import app.main
        self.conn.execute(text("INSERT INTO organizations(id,organization_name,registration_number) VALUES (21,'FPO 21','REG-21')"))
        self.conn.execute(text("INSERT INTO users VALUES (121)"))
        self.conn.execute(text("INSERT INTO financial_years(id,organization_id,name,start_date,end_date) VALUES (2101,21,'FY 2024-25','2024-04-01','2025-03-31'),(2102,21,'FY 2025-26','2025-04-01','2026-03-31'),(2103,21,'FY 2026-27','2026-04-01','2027-03-31')"))
        self.conn.execute(text("INSERT INTO accounts(id,organization_id,account_code,account_name,account_type,account_group,system_key) VALUES (211,21,'1001','Cash','Asset','Cash',NULL),(212,21,'4001','Sales','Income','Income',NULL),(213,21,'3002','Retained earnings','Equity','Equity','RETAINED_EARNINGS')"))
        # FY1 profit is 100 and is closed by a MANUAL journal.
        self._create_posted(21,121,2101,'FY1-PROFIT','2024-12-01',[(211,100,0),(212,0,100)])
        self._create_posted(21,121,2101,'FY1-CLOSE','2025-03-31',[(212,100,0),(213,0,100)])
        # This void 900 profit must affect neither history nor the transfer reconciliation.
        voided = self._create_posted(21,121,2101,'FY1-VOID','2025-03-20',[(211,900,0),(212,0,900)])
        self.conn.execute(text("UPDATE journal_entries SET status='Void',voided_by=121,voided_at=now(),void_reason='excluded' WHERE id=:id"), {"id": voided})
        # FY2 profit 50 closes through the supported OPENING source type, also touching retained earnings.
        self._create_posted(21,121,2102,'FY2-PROFIT','2025-12-01',[(211,50,0),(212,0,50)])
        self._create_posted(21,121,2102,'FY2-CLOSE','2026-03-31',[(212,50,0),(213,0,50)],source_type="OPENING")
        self.conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        with Session(bind=self.conn, join_transaction_mode="create_savepoint") as session:
            trial = FinanceReportService(session).trial_balance(SimpleNamespace(organization_id=21),2103,date(2026,4,2),False)
        retained = next(row for row in trial["accounts"] if row["account_id"] == 213)
        self.assertEqual(Decimal("150.00"), retained["credit"])
        self.assertEqual(Decimal("150.00"), trial["debit_total"])
        self.assertEqual(Decimal("150.00"), trial["credit_total"])
        self.assertEqual({211, 213}, {row["account_id"] for row in trial["accounts"]})

    def test_locked_financial_year_cannot_be_deleted_but_unlocked_can(self):
        self.conn.execute(text("INSERT INTO organizations(id,organization_name,registration_number) VALUES (22,'FPO 22','REG-22')"))
        self.conn.execute(text("INSERT INTO financial_years(id,organization_id,name,start_date,end_date,is_locked) VALUES (2201,22,'Locked','2024-04-01','2025-03-31',true),(2202,22,'Open','2025-04-01','2026-03-31',false)"))
        self._assert_database_rejects(lambda: self.conn.execute(text("DELETE FROM financial_years WHERE id=2201")))
        self.conn.execute(text("DELETE FROM financial_years WHERE id=2202"))

    def test_financial_year_overlap_and_current_uniqueness_are_database_enforced(self):
        self.conn.execute(text("INSERT INTO organizations(id,organization_name,registration_number) VALUES (10,'FPO 10','REG-10')"))
        self.conn.execute(text("INSERT INTO financial_years(id,organization_id,name,start_date,end_date,is_current) VALUES (10010,10,'FY 2026-27','2026-04-01','2027-03-31',true)"))
        self._assert_database_rejects(lambda: self.conn.execute(text("INSERT INTO financial_years(id,organization_id,name,start_date,end_date) VALUES (10011,10,'Overlap','2026-10-01','2027-03-31')")))
        self._assert_database_rejects(lambda: self.conn.execute(text("INSERT INTO financial_years(id,organization_id,name,start_date,end_date,is_current) VALUES (10012,10,'FY 2027-28','2027-04-01','2028-03-31',true)")))

    def test_journal_sequence_lookup_is_scoped_to_financial_year(self):
        import app.main
        self.conn.execute(text("INSERT INTO organizations(id,organization_name,registration_number) VALUES (12,'FPO 12','REG-12')"))
        self.conn.execute(text("INSERT INTO financial_years(id,organization_id,name,start_date,end_date) VALUES (12001,12,'FY 2026-27','2026-04-01','2027-03-31'),(12002,12,'FY 2027-28','2027-04-01','2028-03-31')"))
        for number, year_id in (("JV-2026-27-00004", 12001), ("JV-2027-28-00099", 12002)):
            self.conn.execute(text("INSERT INTO journal_entries(organization_id,journal_no,entry_date,financial_year_id,narration,source_type,status) VALUES (12,:number,'2026-04-01',:year,'sequence','MANUAL','Draft')"), {"number": number, "year": year_id})
        with Session(bind=self.conn, join_transaction_mode="create_savepoint") as session:
            repo = JournalRepository(session)
            self.assertEqual(5, repo.next_number(12, 12001, "JV-2026-27-"))
            self.assertEqual(100, repo.next_number(12, 12002, "JV-2027-28-"))

    def test_journal_service_posts_balanced_journals_and_numbers_by_fy(self):
        import app.main
        self._setup_organization(18, 118, 1018)
        user = SimpleNamespace(id=118, organization_id=18)
        payload = JournalCreate(entry_date=date(2026,4,1), financial_year_id=1018, narration="Cash opening",
            lines=[JournalLineIn(account_id=181, debit=Decimal("25.00")), JournalLineIn(account_id=182, credit=Decimal("25.00"))])
        with Session(bind=self.conn, join_transaction_mode="create_savepoint") as session:
            service = JournalService(session)
            first = service.create_journal(user, payload)
            self.assertEqual("Posted", first.status)
            self.assertEqual("JV-2026-27-00001", first.journal_no)
            self.assertEqual(2, len(first.lines))
            second = service.create_journal(user, payload)
            self.assertEqual("JV-2026-27-00002", second.journal_no)
            with self.assertRaises(HTTPException):
                service.create_journal(user, JournalCreate(entry_date=date(2026,4,1), financial_year_id=1018,
                    narration="Unbalanced", lines=[JournalLineIn(account_id=181, debit=Decimal("25.00")),
                        JournalLineIn(account_id=182, credit=Decimal("24.00"))]))

    def test_default_chart_setup_is_idempotent_and_rejects_conflicts(self):
        import app.main
        self.conn.execute(text("INSERT INTO organizations(id,organization_name,registration_number) VALUES (13,'Setup FPO','SETUP-13'),(14,'Conflict FPO','SETUP-14')"))
        self.conn.execute(text("INSERT INTO accounts(id,organization_id,account_code,account_name,account_type,account_group) VALUES (1401,14,'1001','Wrong name','Asset','Cash')"))
        with Session(bind=self.conn, join_transaction_mode="create_savepoint") as session:
            configured_user = SimpleNamespace(organization_id=13)
            setup = FinanceSetupService(session)
            self.assertTrue(setup.setup(configured_user)["configured"])
            self.assertTrue(setup.setup(configured_user)["configured"])
            self.assertEqual(23, session.query(Account).filter_by(organization_id=13).count())
            with self.assertRaises(HTTPException):
                FinanceSetupService(session).setup(SimpleNamespace(organization_id=14))
            self.assertEqual(1, session.query(Account).filter_by(organization_id=14).count())


if __name__ == "__main__":
    unittest.main()
