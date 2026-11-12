"""SQLite integration coverage for sales-to-inventory immutable lifecycle events."""
import unittest
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database.database import Base
from app.models.crop_master import CropMaster
from app.models.customer import Customer
from app.models.inventory import InventoryBalance, InventoryCreateRequest, InventoryLedger
from app.models.organization import Organization
from app.models.sale import Sale
from app.schemas.inventory import InventoryAdjustRequest
from app.schemas.sale import SaleCreate, SaleUpdate
from app.services.inventory_service import InventoryService
from app.services.sale_service import SaleService


class SalesInventoryLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import app.main  # noqa: F401
        cls.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(cls.engine)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def setUp(self):
        self.conn = self.engine.connect()
        self.db = Session(bind=self.conn)
        for table in reversed(Base.metadata.sorted_tables):
            self.db.execute(table.delete())
        self.db.execute(text(
            "INSERT INTO organizations(id,organization_name,registration_number) "
            "VALUES (1,'First','S-1'),(2,'Other','S-2')"
        ))
        self.db.add_all([
            CropMaster(id=1, crop_code="AGR-1", crop_name="Wheat", item_type="AGRICULTURAL_COMMODITY", base_unit="KG", is_active=True),
            Customer(id=1, organization_id=1, customer_code="CU-1", customer_name="Buyer", is_active=True),
        ])
        self.db.commit()
        self.user = SimpleNamespace(organization_id=1, role=SimpleNamespace(name="FPO Admin"))
        self.service = SaleService(self.db)
        self.inventory = InventoryService(self.db)
        self.inventory.adjust_stock(
            InventoryAdjustRequest(crop_id=1, transaction_type="IN", quantity=Decimal("10")),
            self.user, "sales-test-opening",
        )

    def tearDown(self):
        self.db.close()
        self.conn.close()

    def create(self, quantity=3, idempotency_key=None):
        return self.service.create_sale(SaleCreate(
            sale_date=datetime(2026, 10, 1), customer_id=1, crop_id=1,
            quantity=Decimal(str(quantity)), rate_per_unit=Decimal("5"),
        ), self.user, idempotency_key)

    def test_create_request_key_replays_original_and_rejects_changed_payload(self):
        original = self.create(3, "sale-request-1")
        replay = self.create("3.00", "sale-request-1")
        self.assertEqual(original.id, replay.id)
        self.assertEqual(1, self.db.query(Sale).count())
        self.assertEqual(1, self.db.query(InventoryLedger).filter_by(reference_type="SALE").count())
        with self.assertRaises(HTTPException) as error:
            self.create(4, "sale-request-1")
        self.assertEqual(409, error.exception.status_code)
        self.assertEqual(1, self.db.query(Sale).count())

    def test_legacy_create_without_key_remains_supported_but_is_not_idempotent(self):
        first = self.create(2)
        second = self.create(2)
        self.assertNotEqual(first.id, second.id)
        self.assertEqual(2, self.db.query(Sale).count())
        self.assertEqual(0, self.db.query(InventoryCreateRequest).count())
        self.assertEqual(Decimal("6.000000"), self.balance())

    def test_failed_create_rolls_back_request_key_source_and_stock(self):
        self.conn.exec_driver_sql(
            "CREATE TRIGGER fail_sale_create_ledger BEFORE INSERT ON inventory_ledger "
            "WHEN NEW.reference_type='SALE' BEGIN SELECT RAISE(ABORT, 'forced failure'); END"
        )
        try:
            with self.assertRaises(IntegrityError):
                self.create(3, "sale-create-rollback")
        finally:
            self.conn.exec_driver_sql("DROP TRIGGER IF EXISTS fail_sale_create_ledger")
        self.db.expire_all()
        self.assertEqual(0, self.db.query(Sale).count())
        self.assertEqual(0, self.db.query(InventoryCreateRequest).count())
        self.assertEqual(1, self.db.query(InventoryLedger).filter_by(reference_type="MANUAL").count())
        self.assertEqual(Decimal("10.000000"), self.balance())

    def balance(self):
        return self.inventory.repo.get_balance_for_crop(1, 1)

    def test_create_edit_deactivate_reactivate_append_events(self):
        sale = self.create(3)
        first = self.service.inventory_posting.current_source_movement(1, "SALE", sale.id)
        self.assertEqual(Decimal("7.000000"), self.balance())
        self.service.update_sale(sale.id, SaleUpdate(quantity=Decimal("5")), self.user)
        self.assertEqual(Decimal("3.000000"), first.quantity)
        self.assertEqual(Decimal("5.000000"), self.balance())
        self.assertEqual(3, self.db.query(InventoryLedger).filter_by(reference_type="SALE", reference_id=sale.id).count())
        self.service.toggle_sale_status(sale.id, False, self.user)
        self.assertEqual(Decimal("10.000000"), self.balance())
        self.service.toggle_sale_status(sale.id, True, self.user)
        self.assertEqual(Decimal("5.000000"), self.balance())
        self.assertEqual(5, self.db.query(InventoryLedger).filter_by(reference_type="SALE", reference_id=sale.id).count())
        self.assertEqual(2, self.db.query(InventoryLedger).filter(
            InventoryLedger.reference_type == "SALE", InventoryLedger.reference_id == sale.id,
            InventoryLedger.reverses_id.is_not(None),
        ).count())

    def test_missing_historical_movement_is_not_recreated(self):
        sale = self.create(3)
        self.db.query(InventoryLedger).filter_by(reference_type="SALE", reference_id=sale.id).delete()
        self.db.commit()
        with self.assertRaises(HTTPException) as error:
            self.service.update_sale(sale.id, SaleUpdate(quantity=Decimal("4")), self.user)
        self.assertEqual(409, error.exception.status_code)
        self.assertEqual(7, self.balance())
        self.assertEqual(0, self.db.query(InventoryLedger).filter_by(reference_type="SALE", reference_id=sale.id).count())

    def test_failed_ledger_insert_rolls_back_sale_and_balance(self):
        sale = self.create(3)
        self.conn.exec_driver_sql(
            "CREATE TRIGGER fail_sale_inventory BEFORE INSERT ON inventory_ledger "
            "WHEN NEW.reference_type='SALE' BEGIN SELECT RAISE(ABORT, 'forced failure'); END"
        )
        try:
            with self.assertRaises(IntegrityError):
                self.service.update_sale(sale.id, SaleUpdate(quantity=Decimal("4")), self.user)
        finally:
            self.conn.exec_driver_sql("DROP TRIGGER IF EXISTS fail_sale_inventory")
        self.db.expire_all()
        self.assertEqual(Decimal("3.000000"), self.db.query(Sale).filter_by(id=sale.id).one().quantity)
        self.assertEqual(Decimal("7.000000"), self.balance())
        self.assertEqual(1, self.db.query(InventoryLedger).filter_by(reference_type="SALE", reference_id=sale.id).count())

    def test_cross_tenant_sales_are_denied(self):
        other = Sale(
            sale_no="SA-OTHER", sale_date=datetime(2026, 10, 1), customer_id=1,
            crop_id=1, organization_id=2, quantity=Decimal("1"), unit="KG",
            rate_per_unit=Decimal("5"), total_amount=Decimal("5"), is_active=True,
        )
        self.db.add(other)
        self.db.flush()
        with self.assertRaises(HTTPException) as error:
            self.service.update_sale(other.id, SaleUpdate(quantity=Decimal("2")), self.user)
        self.assertEqual(403, error.exception.status_code)


if __name__ == "__main__":
    unittest.main()
