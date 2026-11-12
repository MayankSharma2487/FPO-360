"""Procurement and inventory ledger lifecycle integration tests (SQLite)."""
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.models.organization import Organization
from app.models.village import Village
from app.models.farmer import Farmer
from app.models.crop_master import CropMaster
from app.models.procurement import Procurement
from app.models.inventory import InventoryBalance, InventoryCreateRequest, InventoryLedger
from app.schemas.procurement import ProcurementCreate, ProcurementUpdate
from app.services.procurement_service import ProcurementService


class ProcurementInventoryLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import app.main  # Register all ORM relationship targets.

        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        with cls.engine.begin() as connection:
            for model in (Organization, Village, Farmer, CropMaster, Procurement, InventoryBalance, InventoryLedger, InventoryCreateRequest):
                model.__table__.create(connection)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def setUp(self):
        self.connection = self.engine.connect()
        self.transaction = self.connection.begin()
        self.db = Session(bind=self.connection, join_transaction_mode="create_savepoint")
        # SQLite's legacy transaction mode may leave setup inserts behind when
        # the outer test transaction is rolled back; reset this isolated DB.
        for table in ("inventory_ledger", "inventory_balances", "inventory_create_requests", "procurements", "farmers", "villages", "crop_masters", "organizations"):
            self.db.execute(text(f"DELETE FROM {table}"))
        self.db.execute(text(
            "INSERT INTO organizations(id, organization_name, registration_number) "
            "VALUES (1,'First','R1'), (2,'Other','R2')"
        ))
        self.db.execute(text(
            "INSERT INTO villages(id, village_code, village_name, district, state, organization_id, is_active) "
            "VALUES (1,'V1','Village One','D','S',1,1), (2,'V2','Village Two','D','S',2,1)"
        ))
        self.db.add_all([
            Farmer(id=1, organization_id=1, village_id=1, farmer_code="F-1", farmer_name="Farmer One", mobile_number="9000000001", is_active=True),
            Farmer(id=2, organization_id=2, village_id=2, farmer_code="F-2", farmer_name="Farmer Two", mobile_number="9000000002", is_active=True),
            CropMaster(id=1, crop_code="C-1", crop_name="Wheat", is_active=True),
        ])
        self.db.flush()
        self.service = ProcurementService(self.db)
        self.user = SimpleNamespace(id=10, organization_id=1, role=SimpleNamespace(name="FPO Admin"))

    def tearDown(self):
        self.db.close()
        self.transaction.rollback()
        self.connection.close()

    def create(self, quantity=10, unit="KG", rate="5.00", organization_id=None, idempotency_key=None):
        return self.service.create_procurement(
            ProcurementCreate(
                procurement_date=datetime(2026, 8, 1, tzinfo=timezone.utc),
                farmer_id=1,
                crop_id=1,
                quantity=quantity,
                unit=unit,
                rate_per_unit=Decimal(rate),
                organization_id=organization_id,
            ),
            self.user,
            idempotency_key,
        )

    def test_create_request_key_replays_original_and_rejects_changed_payload(self):
        original = self.create(idempotency_key="procurement-request-1")
        replay = self.create(idempotency_key="procurement-request-1")
        self.assertEqual(original.id, replay.id)
        self.assertEqual(1, self.db.query(Procurement).count())
        self.assertEqual(1, self.db.query(InventoryLedger).filter_by(reference_type="PROCUREMENT").count())
        with self.assertRaises(HTTPException) as error:
            self.create(quantity=11, idempotency_key="procurement-request-1")
        self.assertEqual(409, error.exception.status_code)
        self.assertEqual(1, self.db.query(Procurement).count())

    def test_super_admin_procurement_uses_explicit_organization_context(self):
        super_admin = SimpleNamespace(
            id=99, organization_id=None, role=SimpleNamespace(name="Super Admin")
        )
        payload = ProcurementCreate(
            procurement_date=datetime(2026, 8, 1, tzinfo=timezone.utc),
            farmer_id=1,
            crop_id=1,
            quantity=Decimal("10"),
            unit="KG",
            rate_per_unit=Decimal("5.00"),
        )
        with self.assertRaises(HTTPException) as missing_context:
            self.service.create_procurement(payload, super_admin)
        self.assertEqual(403, missing_context.exception.status_code)

        scoped_payload = payload.model_copy(update={"organization_id": 1})
        procurement = self.service.create_procurement(scoped_payload, super_admin)
        updated = self.service.update_procurement(
            procurement.id, ProcurementUpdate(remarks="Reviewed by Super Admin"), super_admin
        )
        self.assertEqual(1, updated.organization_id)
        self.assertEqual("Reviewed by Super Admin", updated.remarks)
        self.assertEqual(Decimal("10.000000"), self.service.inventory_repo.get_balance_for_crop(1, 1))

    def test_failed_create_rolls_back_request_key_source_and_stock(self):
        engine = create_engine("sqlite://", poolclass=StaticPool)
        try:
            for model in (Organization, Village, Farmer, CropMaster, Procurement,
                          InventoryBalance, InventoryLedger, InventoryCreateRequest):
                model.__table__.create(engine)
            with Session(engine) as db:
                db.add(Organization(id=1, organization_name="Rollback FPO", registration_number="RB-1"))
                db.flush()
                db.add(Village(
                    id=1, village_code="RB-V1", village_name="Village",
                    district="District", state="State", organization_id=1, is_active=True,
                ))
                db.add(Farmer(
                    id=1, farmer_code="RB-F1", farmer_name="Farmer", mobile_number="9000000001",
                    village_id=1, organization_id=1, is_active=True,
                ))
                db.add(CropMaster(id=1, crop_code="RB-C1", crop_name="Wheat", is_active=True))
                db.commit()
                db.execute(text(
                    "CREATE TRIGGER fail_procurement_create_ledger BEFORE INSERT ON inventory_ledger "
                    "WHEN NEW.reference_type='PROCUREMENT' BEGIN SELECT RAISE(ABORT, 'forced failure'); END"
                ))
                db.commit()
                service = ProcurementService(db)
                user = SimpleNamespace(organization_id=1, role=SimpleNamespace(name="FPO Admin"))
                payload = ProcurementCreate(
                    procurement_date=datetime(2026, 8, 1, tzinfo=timezone.utc), farmer_id=1,
                    crop_id=1, quantity=10, unit="KG", rate_per_unit=Decimal("5"),
                )
                with self.assertRaises(IntegrityError):
                    service.create_procurement(payload, user, "procurement-rollback")
                self.assertEqual(0, db.query(Procurement).count())
                self.assertEqual(0, db.query(InventoryCreateRequest).count())
                self.assertEqual(0, db.query(InventoryLedger).count())
                self.assertIsNone(db.get(InventoryBalance, (1, 1)))
        finally:
            engine.dispose()

    def linked_movement(self, procurement):
        return self.service.inventory_repo.get_by_reference(
            procurement.organization_id, "PROCUREMENT", procurement.id
        )

    def test_create_writes_exactly_one_active_in_movement(self):
        procurement = self.create(quantity=2, unit="QUINTAL", rate="50.00")
        movements = self.db.query(InventoryLedger).filter_by(
            organization_id=1, reference_type="PROCUREMENT", reference_id=procurement.id
        ).all()
        self.assertEqual(1, len(movements))
        self.assertEqual("IN", movements[0].transaction_type)
        self.assertTrue(movements[0].is_active)
        self.assertEqual(200, movements[0].quantity)
        self.assertEqual(200, self.service.inventory_repo.get_balance_for_crop(1, 1))

    def test_edit_updates_movement_and_rate_only_uses_display_quantity(self):
        procurement = self.create(quantity=2, unit="QUINTAL", rate="50.00")
        movement = self.linked_movement(procurement)
        self.service.update_procurement(
            procurement.id,
            ProcurementUpdate(quantity=3, rate_per_unit=Decimal("60.00")),
            self.user,
        )
        self.assertEqual(200, movement.quantity)
        self.assertEqual(300, self.linked_movement(procurement).quantity)
        self.assertEqual(3, self.db.query(InventoryLedger).filter_by(
            organization_id=1, reference_type="PROCUREMENT", reference_id=procurement.id
        ).count())
        self.assertEqual(300, self.service.inventory_repo.get_balance_for_crop(1, 1))
        self.assertEqual(Decimal("180.00"), procurement.total_amount)
        self.service.update_procurement(
            procurement.id,
            ProcurementUpdate(rate_per_unit=Decimal("70.00")),
            self.user,
        )
        self.assertEqual(200, movement.quantity)
        self.assertEqual(3, self.db.query(InventoryLedger).filter_by(
            organization_id=1, reference_type="PROCUREMENT", reference_id=procurement.id
        ).count())
        self.assertEqual(300, self.service.inventory_repo.get_balance_for_crop(1, 1))
        self.assertEqual(Decimal("210.00"), procurement.total_amount)

    def test_deactivate_and_reactivate_append_reversal_and_new_movement(self):
        procurement = self.create(quantity=10)
        movement = self.linked_movement(procurement)
        self.service.toggle_procurement_status(procurement.id, False, self.user)
        self.assertFalse(procurement.is_active)
        self.assertTrue(movement.is_active)
        self.assertEqual(1, self.db.query(InventoryLedger).filter_by(reverses_id=movement.id).count())
        self.assertEqual(0, self.service.inventory_repo.get_balance_for_crop(1, 1))
        self.service.toggle_procurement_status(procurement.id, True, self.user)
        self.assertTrue(movement.is_active)
        self.assertEqual(3, self.db.query(InventoryLedger).filter_by(
            organization_id=1, reference_type="PROCUREMENT", reference_id=procurement.id
        ).count())
        self.assertEqual(10, self.service.inventory_repo.get_balance_for_crop(1, 1))

    def test_repeated_edits_and_status_changes_do_not_duplicate_movement(self):
        procurement = self.create(quantity=10)
        for quantity in (12, 15, 8, 8):
            self.service.update_procurement(procurement.id, ProcurementUpdate(quantity=quantity), self.user)
        for active in (False, False, True, True, False, True):
            self.service.toggle_procurement_status(procurement.id, active, self.user)
        self.assertEqual(11, self.db.query(InventoryLedger).filter_by(
            organization_id=1, reference_type="PROCUREMENT", reference_id=procurement.id
        ).count())
        self.assertEqual(5, self.db.query(InventoryLedger).filter(
            InventoryLedger.reference_type == "PROCUREMENT",
            InventoryLedger.reference_id == procurement.id,
            InventoryLedger.reverses_id.is_not(None),
        ).count())
        self.assertEqual(8, self.service.inventory_repo.get_balance_for_crop(1, 1))

    def test_inventory_update_failure_rolls_back_procurement(self):
        procurement = self.create(quantity=10)
        movement = self.linked_movement(procurement)
        trigger_name = "fail_procurement_inventory_update"
        self.connection.exec_driver_sql(
            f"CREATE TRIGGER {trigger_name} BEFORE INSERT ON inventory_ledger "
            "BEGIN SELECT RAISE(ABORT, 'forced inventory update failure'); END"
        )
        try:
            with self.assertRaises(IntegrityError):
                self.service.update_procurement(
                    procurement.id, ProcurementUpdate(quantity=20), self.user
                )
        finally:
            self.connection.exec_driver_sql(f"DROP TRIGGER IF EXISTS {trigger_name}")
        self.db.expire_all()
        persisted = self.db.query(Procurement).filter_by(id=procurement.id).one()
        persisted_movement = self.linked_movement(persisted)
        self.assertEqual(10, persisted.quantity)
        self.assertEqual(10, persisted_movement.quantity)
        self.assertEqual(1, self.db.query(InventoryLedger).filter_by(
            organization_id=1, reference_type="PROCUREMENT", reference_id=procurement.id
        ).count())
        self.assertEqual(10, self.service.inventory_repo.get_balance_for_crop(1, 1))

    def test_missing_linked_movement_fails_existing_lifecycle_operations(self):
        procurement = self.create(quantity=10)
        movement = self.linked_movement(procurement)
        self.db.delete(movement)
        self.db.commit()

        with self.assertRaises(HTTPException) as edit_error:
            self.service.update_procurement(
                procurement.id, ProcurementUpdate(quantity=20), self.user
            )
        self.assertEqual(409, edit_error.exception.status_code)
        self.db.expire_all()
        persisted = self.db.query(Procurement).filter_by(id=procurement.id).one()
        self.assertEqual(10, persisted.quantity)
        self.assertIsNone(self.linked_movement(persisted))

        with self.assertRaises(HTTPException) as deactivate_error:
            self.service.toggle_procurement_status(procurement.id, False, self.user)
        self.assertEqual(409, deactivate_error.exception.status_code)
        self.assertTrue(persisted.is_active)

        # Exercise the reactivation path with an inactive procurement whose
        # expected historical movement is absent as well.
        persisted.is_active = False
        self.db.commit()
        with self.assertRaises(HTTPException) as reactivate_error:
            self.service.toggle_procurement_status(procurement.id, True, self.user)
        self.assertEqual(409, reactivate_error.exception.status_code)
        self.db.expire_all()
        persisted = self.db.query(Procurement).filter_by(id=procurement.id).one()
        self.assertFalse(persisted.is_active)
        self.assertIsNone(self.linked_movement(persisted))

    def test_foreign_organization_update_and_status_change_are_rejected(self):
        other = Procurement(
            procurement_no="PR-OTHER", procurement_date=datetime(2026, 8, 2, tzinfo=timezone.utc),
            farmer_id=2, crop_id=1, organization_id=2, quantity=10, unit="KG",
            rate_per_unit=Decimal("5.00"), total_amount=Decimal("50.00"), is_active=True,
        )
        self.db.add(other)
        self.db.flush()
        with self.assertRaises(HTTPException) as update_error:
            self.service.update_procurement(other.id, ProcurementUpdate(quantity=20), self.user)
        self.assertEqual(403, update_error.exception.status_code)
        with self.assertRaises(HTTPException) as status_error:
            self.service.toggle_procurement_status(other.id, False, self.user)
        self.assertEqual(403, status_error.exception.status_code)
        self.assertEqual(10, other.quantity)
        self.assertFalse(self.db.query(InventoryLedger).filter_by(organization_id=2).first())

    def test_foreign_organization_create_is_rejected(self):
        with self.assertRaises(HTTPException) as error:
            self.create(organization_id=2)
        self.assertEqual(403, error.exception.status_code)
        self.assertEqual(0, self.db.query(Procurement).count())

    def test_quantity_reduction_or_deactivation_cannot_make_stock_negative(self):
        procurement = self.create(quantity=10)
        from app.services.inventory_posting_service import InventoryPostingService
        InventoryPostingService(self.db).post_manual(
            1, 1, "OUT", Decimal("8"), "MANUAL", "lifecycle-manual-out"
        )
        self.db.commit()
        with self.assertRaises(HTTPException) as edit_error:
            self.service.update_procurement(procurement.id, ProcurementUpdate(quantity=5), self.user)
        self.assertEqual(400, edit_error.exception.status_code)
        with self.assertRaises(HTTPException) as deactivate_error:
            self.service.toggle_procurement_status(procurement.id, False, self.user)
        self.assertEqual(400, deactivate_error.exception.status_code)
        self.assertTrue(procurement.is_active)
        self.assertEqual(10, self.linked_movement(procurement).quantity)


if __name__ == "__main__":
    unittest.main()
