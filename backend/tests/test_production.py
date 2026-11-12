"""Production & Packing business rules against isolated SQLite tables."""
import unittest
from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database.database import Base
from app.domain.item_catalogue import BaseUnit, ItemType
from app.models.crop_master import CropMaster
from app.models.customer import Customer
from app.models.inventory import InventoryBalance, InventoryLedger
from app.models.organization import Organization
from app.models.production import ProductionInput, ProductionRecord
from app.schemas.production import ProductionCreate
from app.schemas.sale import SaleCreate
from app.services.production_service import ProductionService
from app.services.inventory_posting_service import InventoryPostingService, StockEvent
from app.services.sale_service import SaleService
from app.auth.dependencies import get_current_user
from app.database.database import get_db


class ProductionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import app.main  # noqa: F401 - register every model and relationship.
        cls.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(cls.engine)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def setUp(self):
        self.db = Session(self.engine)
        for table in reversed(Base.metadata.sorted_tables):
            self.db.execute(table.delete())
        self.db.execute(text(
            "INSERT INTO organizations(id,organization_name,registration_number) "
            "VALUES (1,'First','R1'),(2,'Other','R2')"
        ))
        self.db.add_all([
            CropMaster(id=1, crop_code="RAW-1", crop_name="Grain", item_type=ItemType.RAW_MATERIAL.value,
                       organization_id=1, base_unit="KG", unit="KG", is_active=True),
            CropMaster(id=2, crop_code="PKG-1", crop_name="Pouch", item_type=ItemType.PACKAGING_MATERIAL.value,
                       organization_id=1, base_unit="PCS", unit="PCS", is_active=True),
            CropMaster(id=3, crop_code="FG-1", crop_name="Packed Flour", item_type=ItemType.FINISHED_GOOD.value,
                       organization_id=1, base_unit="PCS", unit="PCS", is_active=True),
            CropMaster(id=4, crop_code="RAW-OTHER", crop_name="Other FPO grain", item_type=ItemType.RAW_MATERIAL.value,
                       organization_id=2, base_unit="KG", unit="KG", is_active=True),
            CropMaster(id=5, crop_code="AGR-1", crop_name="Wheat", item_type=ItemType.AGRICULTURAL_COMMODITY.value,
                       organization_id=None, base_unit="KG", unit="KG", is_active=True),
        ])
        self.db.add(Customer(id=1, organization_id=1, customer_code="CU-1", customer_name="Buyer", is_active=True))
        self.db.commit()
        InventoryPostingService(self.db).post_events([
            StockEvent(1, 1, "IN", Decimal("100"), "MANUAL", None, "production-fixture-raw", "Test stock"),
            StockEvent(1, 2, "IN", Decimal("100"), "MANUAL", None, "production-fixture-pack", "Test stock"),
        ])
        self.db.commit()
        self.service = ProductionService(self.db)
        self.user = SimpleNamespace(id=None, organization_id=1, role=SimpleNamespace(name="FPO Admin"))

    def tearDown(self):
        from app.main import app
        app.dependency_overrides.clear()
        self.db.close()

    def payload(self, *, output="10", raw="5", raw_unit=BaseUnit.KG, packaging="10", finished_id=3, raw_id=1, package_id=2, wastage="2"):
        return ProductionCreate(
            production_date=date(2026, 10, 1), finished_item_id=finished_id,
            output_quantity=Decimal(output), output_unit=BaseUnit.PCS,
            inputs=[
                {"item_id": raw_id, "quantity": Decimal(raw), "unit": raw_unit},
                {"item_id": package_id, "quantity": Decimal(packaging), "unit": BaseUnit.PCS},
            ],
            wastage_quantity=Decimal(wastage), wastage_unit=BaseUnit.PCS,
            notes="Test production",
        )

    def test_posting_consumes_raw_and_packaging_and_adds_finished_stock(self):
        result = self.service.create(self.payload(raw="5000", raw_unit=BaseUnit.G), self.user, "prod-1")
        self.assertEqual("POSTED", result["status"])
        self.assertEqual("10.000000", str(result["output_base_quantity"]))
        self.assertEqual("2.000000", str(result["wastage_base_quantity"]))
        self.assertEqual(3, self.db.query(InventoryLedger).filter_by(reference_type="PRODUCTION").count())
        self.assertEqual(Decimal("95.000000"), self._ledger_sum(1))
        self.assertEqual(Decimal("90.000000"), self._ledger_sum(2))
        self.assertEqual(Decimal("10.000000"), self._ledger_sum(3))
        self.assertEqual(Decimal("95.000000"), self.db.get(InventoryBalance, (1, 1)).quantity)
        self.assertEqual(Decimal("90.000000"), self.db.get(InventoryBalance, (1, 2)).quantity)
        self.assertEqual(Decimal("10.000000"), self.db.get(InventoryBalance, (1, 3)).quantity)
        self.assertEqual({"G": Decimal("5000"), "PCS": Decimal("10")}, {
            row["unit"]: row["quantity"] for row in result["total_input_consumption"]
        })

    def test_insufficient_stock_rolls_back_header_inputs_balances_and_ledger(self):
        with self.assertRaises(HTTPException) as error:
            self.service.create(self.payload(raw="500"), self.user, "prod-insufficient")
        self.assertEqual(400, error.exception.status_code)
        self.assertEqual(0, self.db.query(ProductionRecord).count())
        self.assertEqual(0, self.db.query(ProductionInput).count())
        self.assertEqual(2, self.db.query(InventoryLedger).count())
        self.assertEqual(2, self.db.query(InventoryBalance).count())

    def test_request_retry_is_idempotent_and_payload_mismatch_conflicts(self):
        first = self.service.create(self.payload(), self.user, "same-key")
        retry = self.service.create(self.payload(), self.user, "same-key")
        self.assertEqual(first["id"], retry["id"])
        self.assertEqual(1, self.db.query(ProductionRecord).count())
        self.assertEqual(3, self.db.query(InventoryLedger).filter_by(reference_type="PRODUCTION").count())
        with self.assertRaises(HTTPException) as error:
            self.service.create(self.payload(output="11"), self.user, "same-key")
        self.assertEqual(409, error.exception.status_code)

    def test_duplicate_input_rows_wrong_item_types_and_tenant_items_are_rejected(self):
        duplicate = self.payload().model_copy(update={
            "inputs": [self.payload().inputs[0], self.payload().inputs[0]],
        })
        with self.assertRaises(HTTPException):
            self.service.create(duplicate, self.user, "duplicate-lines")
        with self.assertRaises(HTTPException):
            self.service.create(self.payload(raw_id=4), self.user, "other-tenant")

        # The rejection test for raw_id=5 (agricultural commodity) was removed here per instructions

        super_admin = SimpleNamespace(id=1, organization_id=None, role=SimpleNamespace(name="Super Admin"))
        with self.assertRaises(HTTPException) as error:
            self.service.create(self.payload(), super_admin, "unscoped")
        self.assertEqual(403, error.exception.status_code)
        self.assertEqual(0, self.db.query(ProductionRecord).count())

    def test_invalid_and_excess_precision_quantities_are_rejected_by_schema(self):
        with self.assertRaises(ValidationError):
            self.payload(output="0")
        with self.assertRaises(ValidationError):
            self.payload(output="1.0000001")

    def test_incompatible_units_and_inactive_items_are_rejected(self):
        with self.assertRaises(HTTPException):
            self.service.create(self.payload().model_copy(update={"output_unit": BaseUnit.KG}), self.user, "wrong-output-unit")
        with self.assertRaises(HTTPException):
            self.service.create(self.payload().model_copy(update={"wastage_unit": BaseUnit.KG, "wastage_quantity": Decimal("0")}), self.user, "wrong-zero-wastage-unit")
        item = self.db.get(CropMaster, 1)
        item.is_active = False
        self.db.commit()
        with self.assertRaises(HTTPException):
            self.service.create(self.payload(), self.user, "inactive-input")
        self.assertEqual(0, self.db.query(ProductionRecord).count())

    def test_ledger_failure_rolls_back_all_production_writes(self):
        self.db.execute(text(
            "CREATE TRIGGER fail_production_ledger BEFORE INSERT ON inventory_ledger "
            "WHEN NEW.reference_type='PRODUCTION' BEGIN SELECT RAISE(ABORT, 'forced production ledger failure'); END"
        ))
        self.db.commit()
        try:
            with self.assertRaises(IntegrityError):
                self.service.create(self.payload(), self.user, "rollback-key")
            self.assertEqual(0, self.db.query(ProductionRecord).count())
            self.assertEqual(0, self.db.query(ProductionInput).count())
            self.assertEqual(2, self.db.query(InventoryLedger).count())
            self.assertEqual(2, self.db.query(InventoryBalance).count())
        finally:
            self.db.execute(text("DROP TRIGGER fail_production_ledger"))
            self.db.commit()

    def test_history_detail_is_tenant_scoped_and_finished_goods_can_be_sold(self):
        produced = self.service.create(self.payload(), self.user, "sale-ready")
        self.assertEqual(produced["id"], self.service.get(produced["id"], self.user)["id"])
        other = SimpleNamespace(id=2, organization_id=2, role=SimpleNamespace(name="Manager"))
        with self.assertRaises(HTTPException) as hidden:
            self.service.get(produced["id"], other)
        self.assertEqual(404, hidden.exception.status_code)

        sale = SaleService(self.db).create_sale(SaleCreate(
            sale_date=datetime(2026, 10, 2, tzinfo=timezone.utc), customer_id=1,
            crop_id=3, quantity=Decimal("3"), unit="PCS", rate_per_unit=Decimal("2"),
        ), self.user, "sale-finished-good")
        self.assertEqual(Decimal("3.000000"), sale.quantity)
        self.assertEqual(Decimal("7.000000"), self.db.get(InventoryBalance, (1, 3)).quantity)
        movements = self.db.query(InventoryLedger).filter_by(reference_type="SALE", reference_id=sale.id).all()
        self.assertEqual(1, len(movements))
        self.assertEqual("OUT", movements[0].transaction_type)

    def test_production_api_create_list_and_detail_contract(self):
        from app.main import app

        def use_db():
            yield self.db

        app.dependency_overrides[get_db] = use_db
        app.dependency_overrides[get_current_user] = lambda: self.user
        client = TestClient(app)
        response = client.post("/production/", headers={"Idempotency-Key": "api-production"}, json={
            "production_date": "2026-10-03",
            "finished_item_id": 3,
            "output_quantity": "8",
            "output_unit": "PCS",
            "inputs": [
                {"item_id": 1, "quantity": "4", "unit": "KG"},
                {"item_id": 2, "quantity": "8", "unit": "PCS"},
            ],
            "wastage_quantity": "1",
            "wastage_unit": "PCS",
            "notes": "API contract",
        })
        self.assertEqual(201, response.status_code, response.text)
        production_id = response.json()["id"]
        self.assertEqual(200, client.get("/production/").status_code)
        detail = client.get(f"/production/{production_id}")
        self.assertEqual(200, detail.status_code)
        self.assertEqual(2, len(detail.json()["inputs"]))

    def _ledger_sum(self, item_id):
        from sqlalchemy import case, func
        value = self.db.query(func.sum(case(
            (InventoryLedger.transaction_type == "IN", InventoryLedger.quantity),
            else_=-InventoryLedger.quantity,
        ))).filter(InventoryLedger.organization_id == 1, InventoryLedger.item_id == item_id).scalar()
        return Decimal(value or 0).quantize(Decimal("0.000001"))

    def test_agricultural_commodity_can_be_used_as_raw_input(self):
        InventoryPostingService(self.db).post_events([
            StockEvent(
                1, 5, "IN", Decimal("100"),
                "MANUAL", None, "agri-stock-test", "Test stock"
            )
        ])
        self.db.commit()

        result = self.service.create(
            self.payload(raw_id=5),
            self.user,
            "agricultural-input-test",
        )

        self.assertEqual("POSTED", result["status"])

        production_input = (
            self.db.query(ProductionInput)
            .filter_by(production_id=result["id"], item_id=5)
            .one()
        )

        # Assuming your service propagates AGRICULTURAL_COMMODITY.
        # If it normalizes to RAW_MATERIAL, keep as RAW_MATERIAL.
        self.assertEqual("RAW_MATERIAL", production_input.input_type)


if __name__ == "__main__":
    unittest.main()