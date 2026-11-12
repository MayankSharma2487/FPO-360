"""HTTP contract coverage for required manual adjustment idempotency keys (SQLite)."""
import unittest
from types import SimpleNamespace

from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database.database import Base
from app.models.crop_master import CropMaster
from app.models.inventory import InventoryLedger
from app.api.inventory import adjust_stock
from app.schemas.inventory import InventoryAdjustRequest


class InventoryApiIdempotencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import app.main  # noqa: F401
        cls.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
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
            "VALUES (1,'Test FPO','API-1')"
        ))
        self.db.add(CropMaster(
            id=1, crop_code="AGR-1", crop_name="Wheat",
            item_type="AGRICULTURAL_COMMODITY", base_unit="KG", unit="KG",
            is_active=True,
        ))
        self.db.commit()
        self.user = SimpleNamespace(organization_id=1, role=SimpleNamespace(name="FPO Admin"))

    def tearDown(self):
        self.db.close()

    def test_manual_adjustment_requires_clear_idempotency_header_error(self):
        with self.assertRaises(HTTPException) as error:
            adjust_stock(
                InventoryAdjustRequest(item_id=1, transaction_type="IN", quantity="2.5"),
                idempotency_key=None, db=self.db, current_user=self.user,
            )
        self.assertEqual(400, error.exception.status_code)
        self.assertIn("Idempotency-Key header is required", error.exception.detail)
        self.assertEqual(0, self.db.query(InventoryLedger).count())

    def test_manual_adjustment_key_replay_and_payload_conflict(self):
        body = InventoryAdjustRequest(item_id=1, transaction_type="IN", quantity="2.5")
        first = adjust_stock(body, idempotency_key="manual-api-key", db=self.db, current_user=self.user)
        replay = adjust_stock(body, idempotency_key="manual-api-key", db=self.db, current_user=self.user)
        with self.assertRaises(HTTPException) as conflict:
            adjust_stock(
                InventoryAdjustRequest(item_id=1, transaction_type="IN", quantity="3"),
                idempotency_key="manual-api-key", db=self.db, current_user=self.user,
            )
        self.assertEqual(409, conflict.exception.status_code)
        self.assertEqual(first["id"], replay["id"])
        self.assertEqual(1, self.db.query(InventoryLedger).count())
        self.assertEqual("2.500000", str(self.db.query(InventoryLedger).one().quantity))


if __name__ == "__main__":
    unittest.main()
