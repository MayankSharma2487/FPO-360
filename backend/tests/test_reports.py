import asyncio
import unittest
from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.reports import _output, router
from app.models.account import Account
from app.models.customer import Customer
from app.models.crop_master import CropMaster
from app.models.farmer import Farmer
from app.models.financial_year import FinancialYear
from app.models.inventory import InventoryLedger
from app.models.journal import JournalEntry, JournalLine
from app.models.license import License
from app.models.organization import Organization
from app.models.payment import Payment
from app.models.procurement import Procurement
from app.models.sale import Sale
from app.models.village import Village
from app.services.reports_service import ReportsService


class ReportsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import app.main  # register all ORM relationship targets
        cls.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        with cls.engine.begin() as conn:
            Organization.__table__.create(conn)
            Village.__table__.create(conn)
            Farmer.__table__.create(conn)
            CropMaster.__table__.create(conn)
            Procurement.__table__.create(conn)
            Payment.__table__.create(conn)
            InventoryLedger.__table__.create(conn)
            Customer.__table__.create(conn)
            Sale.__table__.create(conn)
            FinancialYear.__table__.create(conn)
            Account.__table__.create(conn)
            JournalEntry.__table__.create(conn)
            JournalLine.__table__.create(conn)
            License.__table__.create(conn)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def setUp(self):
        self.connection = self.engine.connect()
        self.transaction = self.connection.begin()
        self.db = Session(bind=self.connection, join_transaction_mode="create_savepoint")
        self.db.execute(text("INSERT INTO organizations(id, organization_name, registration_number) VALUES (1,'First','R1'), (2,'Other','R2')"))
        self.db.add_all([
            Farmer(id=1, organization_id=1, farmer_code="F-1", farmer_name="Farmer One", mobile_number="9000000001", is_active=True, is_shareholder=True),
            Farmer(id=2, organization_id=2, farmer_code="F-2", farmer_name="Farmer Two", mobile_number="9000000002", is_active=True),
            CropMaster(id=1, crop_code="C-1", crop_name="Wheat"),
            Customer(id=1, organization_id=1, customer_code="CU-1", customer_name="Buyer One"),
            Customer(id=2, organization_id=2, customer_code="CU-2", customer_name="Buyer Two"),
        ])
        self.db.flush()
        now = datetime(2025, 7, 1, tzinfo=timezone.utc)
        self.db.add_all([
            Procurement(id=1, organization_id=1, farmer_id=1, crop_id=1, procurement_no="PR-1", procurement_date=now, quantity=100, unit="KG", rate_per_unit=Decimal("10"), total_amount=Decimal("1000"), is_active=True),
            Procurement(id=2, organization_id=2, farmer_id=2, crop_id=1, procurement_no="PR-2", procurement_date=now, quantity=900, unit="KG", rate_per_unit=Decimal("20"), total_amount=Decimal("18000"), is_active=True),
            Payment(id=1, organization_id=1, farmer_id=1, procurement_id=1, payment_no="PAY-1", payment_date=now, amount=250, payment_method="Cash", status="Paid", is_active=True),
            Payment(id=2, organization_id=2, farmer_id=2, procurement_id=2, payment_no="PAY-2", payment_date=now, amount=950, payment_method="Bank", status="Paid", is_active=True),
            InventoryLedger(id=1, organization_id=1, crop_id=1, transaction_type="IN", quantity=100, reference_type="PROCUREMENT", reference_id=1, is_active=True, created_at=now),
            InventoryLedger(id=2, organization_id=2, crop_id=1, transaction_type="IN", quantity=900, reference_type="PROCUREMENT", reference_id=2, is_active=True, created_at=now),
            Sale(id=1, organization_id=1, customer_id=1, crop_id=1, sale_no="SA-1", sale_date=now, quantity=20, unit="KG", rate_per_unit=Decimal("30"), total_amount=Decimal("600"), payment_status="Pending", is_active=True),
            Sale(id=2, organization_id=2, customer_id=2, crop_id=1, sale_no="SA-2", sale_date=now, quantity=90, unit="KG", rate_per_unit=Decimal("30"), total_amount=Decimal("2700"), payment_status="Paid", is_active=True),
            FinancialYear(id=1, organization_id=1, name="FY25", start_date=date(2025, 4, 1), end_date=date(2026, 3, 31), is_current=True),
            Account(id=1, organization_id=1, account_code="1001", account_name="Cash", account_type="Asset", account_group="Cash", account_subtype="CASH", system_key="CASH_IN_HAND", is_active=True),
            Account(id=2, organization_id=1, account_code="4001", account_name="Sales", account_type="Income", account_group="Income", system_key="SALES_REVENUE", is_active=True),
            Account(id=3, organization_id=2, account_code="1001", account_name="Cash Other", account_type="Asset", account_group="Cash", account_subtype="CASH", system_key="CASH_IN_HAND", is_active=True),
            JournalEntry(id=1, organization_id=1, journal_no="JV-1", entry_date=date(2025, 7, 1), financial_year_id=1, narration="Sale", source_type="MANUAL", status="Posted"),
            JournalEntry(id=2, organization_id=2, journal_no="JV-2", entry_date=date(2025, 7, 1), financial_year_id=1, narration="Other", source_type="MANUAL", status="Posted"),
        ])
        self.db.flush()
        self.db.add_all([
            JournalLine(id=1, journal_entry_id=1, organization_id=1, line_no=1, account_id=1, debit=Decimal("100"), credit=0),
            JournalLine(id=2, journal_entry_id=1, organization_id=1, line_no=2, account_id=2, debit=0, credit=Decimal("100")),
            JournalLine(id=3, journal_entry_id=2, organization_id=2, line_no=1, account_id=3, debit=Decimal("900"), credit=0),
        ])
        self.db.add(License(organization_id=1, license_type="FSSAI", issuing_authority="Food Safety", status="Active", expiry_date=date.today()))
        self.db.flush()
        self.service = ReportsService(self.db)
        self.user = SimpleNamespace(organization_id=1, role=SimpleNamespace(name="Super Admin"))

    def tearDown(self):
        self.db.close(); self.transaction.rollback(); self.connection.close()

    def test_procurement_scope_filter_summary_and_pagination(self):
        result = self.service.get_procurement_report(self.user, {"from_date": date(2025, 7, 1), "to_date": date(2025, 7, 2)}, 1, 1)
        self.assertEqual(1, result["total"])
        self.assertEqual("PR-1", result["items"][0]["procurement_no"])
        self.assertEqual(100, result["summary"]["quantity"])
        self.assertEqual(1000, result["summary"]["value"])
        self.assertEqual(1, result["summary"]["farmers"])

    def test_payments_inventory_sales_and_farmer_reports(self):
        self.assertEqual(250, self.service.get_payment_report(self.user, {}, 1, 25)["summary"]["paid"])
        inventory = self.service.get_inventory_report(self.user, {"movement_type": "IN"}, 1, 25)
        self.assertEqual(100, inventory["summary"]["current_stock"])
        self.assertEqual(1, inventory["total"])
        sales = self.service.get_sales_report(self.user, {"payment_status": "Pending"}, 1, 25)
        self.assertEqual(600, sales["summary"]["pending"])
        farmers = self.service.get_farmer_report(self.user, {}, 1, 25)
        self.assertEqual(["F-1"], [row["farmer_code"] for row in farmers["items"]])
        self.assertEqual(250, farmers["items"][0]["payment_total"])

    def test_empty_filters_csv_export_finance_and_license_scope(self):
        empty = self.service.get_sales_report(self.user, {"from_date": date(2026, 1, 1)}, 1, 25)
        self.assertEqual(0, empty["total"])
        self.assertEqual(0, empty["summary"]["value"])
        csv_response = _output(self.service.get_procurement_report(self.user, {}, 1, 25), True)
        body = "".join(asyncio.run(_collect(csv_response.body_iterator)))
        self.assertIn("procurement_no", body)
        finance = self.service.get_finance_summary(self.user)
        self.assertEqual(100, finance["revenue"])
        self.assertEqual(100, finance["cash"])
        licenses = self.service.get_license_summary(self.user)
        self.assertEqual({"total": 1, "active": 1, "expiring_soon": 1, "expired": 0}, licenses)

    def test_read_roles_only_and_unassigned_super_admin_denied(self):
        read_route = next(r for r in router.routes if r.path == "/reports/procurement")
        dependency = next(d for d in read_route.dependant.dependencies if d.name == "user")
        checker = dependency.call
        for role in ("Super Admin", "FPO Admin", "Manager", "Accountant", "Viewer"):
            self.assertEqual(role, checker(SimpleNamespace(role=SimpleNamespace(name=role))).role.name)
        with self.assertRaises(Exception):
            checker(SimpleNamespace(role=SimpleNamespace(name="Guest")))
        with self.assertRaises(Exception):
            self.service.get_procurement_report(SimpleNamespace(organization_id=None), {}, 1, 25)


async def _collect(iterator):
    return [chunk async for chunk in iterator]


if __name__ == "__main__":
    unittest.main()
