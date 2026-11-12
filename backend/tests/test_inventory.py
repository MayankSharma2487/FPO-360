"""Inventory business rules on SQLite; row-lock correctness is PostgreSQL-only."""
import unittest
from decimal import Decimal
from types import SimpleNamespace

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database.database import Base
from app.domain.item_catalogue import BaseUnit, ItemType
from app.models.crop_master import CropMaster
from app.models.inventory import InventoryBalance, InventoryCreateRequest, InventoryLedger
from app.schemas.inventory import InventoryAdjustRequest
from app.services.inventory_service import InventoryService
from app.services.request_idempotency_service import RequestIdempotencyService


class InventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import app.main  # noqa: F401 - register all mapped tables
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
            "VALUES (1,'FPO One','I-1'),(2,'FPO Two','I-2')"
        ))
        units = {
            ItemType.AGRICULTURAL_COMMODITY: BaseUnit.KG,
            ItemType.PURCHASED_PRODUCT: BaseUnit.PCS,
            ItemType.RAW_MATERIAL: BaseUnit.G,
            ItemType.PACKAGING_MATERIAL: BaseUnit.ML,
            ItemType.FINISHED_GOOD: BaseUnit.L,
        }
        self.db.add_all([
            CropMaster(
                id=index,
                crop_code=f"IT-{index}",
                crop_name=f"Item {index}",
                item_type=kind.value,
                organization_id=None if kind == ItemType.AGRICULTURAL_COMMODITY else 1,
                base_unit=units[kind].value,
                unit="KG",
                is_active=True,
            )
            for index, kind in enumerate(ItemType, 1)
        ] + [CropMaster(
            id=9, crop_code="PRIVATE-2", crop_name="Other tenant item",
            item_type=ItemType.RAW_MATERIAL.value, organization_id=2,
            base_unit=BaseUnit.KG.value, unit="KG", is_active=True,
        )])
        self.db.commit()
        self.service = InventoryService(self.db)
        self.admin = SimpleNamespace(organization_id=1, role=SimpleNamespace(name="FPO Admin"))
        self.manager = SimpleNamespace(organization_id=1, role=SimpleNamespace(name="Manager"))
        self.accountant = SimpleNamespace(organization_id=1, role=SimpleNamespace(name="Accountant"))
        self.viewer = SimpleNamespace(organization_id=1, role=SimpleNamespace(name="Viewer"))
        self.super_admin = SimpleNamespace(organization_id=None, role=SimpleNamespace(name="Super Admin"))

    def tearDown(self):
        self.db.close()
        self.conn.close()

    def adjust(self, item_id, direction, qty, key, unit=None, user=None, remarks=None):
        payload = InventoryAdjustRequest(
            item_id=item_id, transaction_type=direction, quantity=Decimal(str(qty)),
            unit=unit, remarks=remarks,
        )
        return self.service.adjust_stock(payload, user or self.admin, key)

    def test_manual_in_out_for_all_five_catalogue_types(self):
        for item_id, kind in enumerate(ItemType, 1):
            unit = BaseUnit({
                ItemType.AGRICULTURAL_COMMODITY: "KG",
                ItemType.PURCHASED_PRODUCT: "PCS",
                ItemType.RAW_MATERIAL: "G",
                ItemType.PACKAGING_MATERIAL: "ML",
                ItemType.FINISHED_GOOD: "L",
            }[kind])
            received = self.adjust(item_id, "IN", 10, f"in-{item_id}", remarks="Opening balance")
            issued = self.adjust(item_id, "OUT", 3, f"out-{item_id}")
            self.assertEqual(kind.value, received["item_type"])
            self.assertEqual(Decimal("10.000000"), received["quantity"])
            self.assertEqual(Decimal("3.000000"), issued["quantity"])
            balance = self.db.get(InventoryBalance, (1, item_id))
            self.assertEqual(Decimal("7.000000"), balance.quantity)
            self.assertEqual(item_id if kind == ItemType.AGRICULTURAL_COMMODITY else None, issued["crop_id"])

        for item_id in range(2, 6):
            with self.assertRaises(HTTPException) as error:
                self.service.adjust_stock(
                    InventoryAdjustRequest(
                        crop_id=item_id, transaction_type="IN", quantity=Decimal("1")
                    ),
                    self.admin,
                    f"invalid-crop-alias-{item_id}",
                )
            self.assertEqual(400, error.exception.status_code)
            self.assertEqual(unit.value, issued["base_unit"])

    def test_explicit_mass_and_volume_conversions_and_rejections(self):
        self.adjust(1, "IN", "2500", "mass-conversion", BaseUnit.G)
        self.assertEqual(Decimal("2.500000"), self.db.get(InventoryBalance, (1, 1)).quantity)
        self.adjust(5, "IN", "1000", "volume-conversion", BaseUnit.ML)
        self.assertEqual(Decimal("1.000000"), self.db.get(InventoryBalance, (1, 5)).quantity)
        with self.assertRaises(HTTPException):
            self.adjust(2, "IN", "1.5", "fractional-pcs")
        with self.assertRaises(HTTPException):
            self.adjust(2, "IN", "2", "wrong-dimension", BaseUnit.KG)
        with self.assertRaises(ValidationError):
            InventoryAdjustRequest(item_id=1, transaction_type="IN", quantity="0.0000001")
        with self.assertRaises(ValidationError):
            InventoryAdjustRequest(item_id=1, transaction_type="IN", quantity=0)

    def test_negative_stock_is_rejected_and_ledger_is_unchanged(self):
        self.adjust(1, "IN", 2, "seed")
        with self.assertRaises(HTTPException) as error:
            self.adjust(1, "OUT", 3, "too-much")
        self.assertEqual(400, error.exception.status_code)
        self.assertEqual(1, self.db.query(InventoryLedger).count())
        self.assertEqual(Decimal("2.000000"), self.db.get(InventoryBalance, (1, 1)).quantity)

    def test_idempotency_replay_and_key_conflict(self):
        first = self.adjust(1, "IN", 5, "request-1")
        retry = self.adjust(1, "IN", 5, "request-1")
        self.assertEqual(first["id"], retry["id"])
        self.assertEqual(1, self.db.query(InventoryLedger).count())
        with self.assertRaises(HTTPException) as conflict:
            self.adjust(1, "IN", 6, "request-1")
        self.assertEqual(409, conflict.exception.status_code)

    def test_organization_ledger_lists_mixed_items_without_cross_tenant_rows(self):
        self.adjust(1, "IN", 4, "aggregate-ledger-crop")
        self.adjust(2, "IN", 7, "aggregate-ledger-generic")
        other_org_movement = InventoryLedger(
            organization_id=2, item_id=9, transaction_type="IN", quantity=Decimal("2"),
            reference_type="MANUAL", reference_id=None, idempotency_key="other-org-ledger",
            is_active=True,
        )
        self.db.add(other_org_movement)
        self.db.commit()

        rows = self.service.list_ledger(self.admin)
        self.assertEqual({1, 2}, {row["item_id"] for row in rows})
        self.assertTrue(all(row["organization_id"] == 1 for row in rows))
        self.assertEqual({1, None}, {row["crop_id"] for row in rows})

    def test_rollback_when_ledger_insert_fails(self):
        self.conn.exec_driver_sql(
            "CREATE TRIGGER fail_inventory_insert BEFORE INSERT ON inventory_ledger "
            "BEGIN SELECT RAISE(ABORT, 'forced ledger failure'); END"
        )
        try:
            with self.assertRaises(IntegrityError):
                self.adjust(1, "IN", 2, "rollback-key")
        finally:
            self.conn.exec_driver_sql("DROP TRIGGER IF EXISTS fail_inventory_insert")
        self.assertIsNone(self.db.get(InventoryBalance, (1, 1)))
        self.assertEqual(0, self.db.query(InventoryLedger).count())

    def test_tenant_activity_role_and_super_admin_context(self):
        with self.assertRaises(HTTPException) as private:
            self.adjust(9, "IN", 1, "foreign", user=self.admin)
        self.assertEqual(404, private.exception.status_code)
        with self.assertRaises(HTTPException) as inactive:
            self.db.query(CropMaster).filter_by(id=2).one().is_active = False
            self.db.commit()
            self.adjust(2, "IN", 1, "inactive")
        self.assertEqual(400, inactive.exception.status_code)
        self.assertEqual([], self.service.list_balances(self.accountant))
        self.assertEqual([], self.service.list_balances(self.viewer))
        with self.assertRaises(HTTPException):
            self.adjust(1, "IN", 1, "accountant-write", user=self.accountant)
        with self.assertRaises(HTTPException):
            self.service.list_balances(self.super_admin)
        with self.assertRaises(HTTPException):
            self.adjust(1, "IN", 1, "super-write", user=self.super_admin)

    def test_reconciliation_reports_drift_without_repair(self):
        self.adjust(1, "IN", 5, "reconcile-seed")
        balance = self.db.get(InventoryBalance, (1, 1))
        balance.quantity = Decimal("6")
        self.db.commit()
        result = self.service.reconcile(self.admin)
        self.assertEqual(1, len(result))
        self.assertEqual(Decimal("1.000000"), result[0]["difference"])
        self.assertEqual(Decimal("6.000000"), self.db.get(InventoryBalance, (1, 1)).quantity)

    def test_create_request_keys_are_scoped_by_organization_and_operation(self):
        requests = RequestIdempotencyService(self.db)
        payload_hash = requests.payload_hash(
            InventoryAdjustRequest(item_id=1, transaction_type="IN", quantity=1), 1
        )
        self.assertEqual(
            payload_hash,
            requests.payload_hash(
                InventoryAdjustRequest(item_id=1, transaction_type="IN", quantity=Decimal("1.00")),
                1,
            ),
        )
        self.assertIsNone(requests.find_existing(1, "PROCUREMENT_CREATE", "shared-key", payload_hash))
        requests.store(1, "PROCUREMENT_CREATE", "shared-key", payload_hash, 10)
        self.db.commit()

        self.assertIsNone(requests.find_existing(1, "SALE_CREATE", "shared-key", payload_hash))
        requests.store(1, "SALE_CREATE", "shared-key", payload_hash, 11)
        self.assertIsNone(requests.find_existing(2, "PROCUREMENT_CREATE", "shared-key", payload_hash))
        requests.store(2, "PROCUREMENT_CREATE", "shared-key", payload_hash, 12)
        self.db.commit()
        self.assertEqual(3, self.db.query(InventoryCreateRequest).count())


if __name__ == "__main__":
    unittest.main()
