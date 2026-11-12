"""PostgreSQL stock-lock integration tests; requires a dedicated *_test database URL."""
import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from decimal import Decimal
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from threading import Barrier
from types import SimpleNamespace
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from fastapi import HTTPException
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from postgres_test_safety import validate_test_database_url

from app.models.crop_master import CropMaster
from app.models.customer import Customer
from app.models.farmer import Farmer
from app.models.inventory import InventoryBalance, InventoryCreateRequest, InventoryLedger
from app.models.organization import Organization
from app.models.procurement import Procurement
from app.models.sale import Sale
from app.models.village import Village
from app.schemas.inventory import InventoryAdjustRequest
from app.schemas.procurement import ProcurementCreate
from app.schemas.sale import SaleCreate
from app.services.inventory_service import InventoryService
from app.services.inventory_posting_service import InventoryPostingService, StockEvent
from app.services.procurement_service import ProcurementService
from app.services.sale_service import SaleService


class PostgreSQLInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        url = os.getenv("INVENTORY_TEST_DATABASE_URL")
        if not url:
            raise unittest.SkipTest("INVENTORY_TEST_DATABASE_URL is not configured")
        cls.test_database_url = validate_test_database_url(url)
        cls.engine = create_engine(cls.test_database_url, pool_size=6, max_overflow=4)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "engine"):
            validate_test_database_url(os.getenv("INVENTORY_TEST_DATABASE_URL"))
            cls.engine.dispose()

    def setUp(self):
        validate_test_database_url(os.getenv("INVENTORY_TEST_DATABASE_URL"))
        import app.main  # noqa: F401 - register mapped relationships
        self.schema = "inventory_test_" + uuid4().hex
        with self.engine.connect() as conn:
            conn.exec_driver_sql(f'CREATE SCHEMA "{self.schema}"')
            conn.exec_driver_sql(f'SET search_path TO "{self.schema}"')
            Organization.__table__.create(conn)
            Village.__table__.create(conn)
            CropMaster.__table__.create(conn)
            Farmer.__table__.create(conn)
            Customer.__table__.create(conn)
            Sale.__table__.create(conn)
            Procurement.__table__.create(conn)
            InventoryBalance.__table__.create(conn)
            InventoryLedger.__table__.create(conn)
            InventoryCreateRequest.__table__.create(conn)
            conn.execute(text(
                "INSERT INTO organizations(id,organization_name,registration_number) "
                "VALUES (1,'Test FPO','INV-TEST')"
            ))
            conn.execute(text(
                "INSERT INTO crop_masters(id,crop_code,crop_name,crop_category,unit,item_type,"
                "organization_id,base_unit,is_active) VALUES "
                "(1,'AGR-1','Wheat',NULL,'KG','AGRICULTURAL_COMMODITY',NULL,'KG',true), "
                "(2,'RAW-1','Material',NULL,'KG','RAW_MATERIAL',1,'KG',true)"
            ))
            conn.execute(text(
                "INSERT INTO villages(id,village_code,village_name,district,state,organization_id,is_active) "
                "VALUES (1,'V-1','Village','District','State',1,true)"
            ))
            conn.execute(text(
                "INSERT INTO customers(id,customer_code,customer_name,organization_id,is_active) "
                "VALUES (1,'CU-1','Test Buyer',1,true)"
            ))
            conn.execute(text(
                "INSERT INTO farmers(id,farmer_code,farmer_name,mobile_number,is_shareholder,is_active,"
                "village_id,organization_id) VALUES (1,'F-1','Farmer','9000000001',false,true,1,1)"
            ))
            conn.commit()
            conn.exec_driver_sql("RESET search_path")
            conn.commit()
        self.user = SimpleNamespace(organization_id=1, role=SimpleNamespace(name="FPO Admin"))

    def tearDown(self):
        validate_test_database_url(os.getenv("INVENTORY_TEST_DATABASE_URL"))
        with self.engine.connect() as conn:
            conn.exec_driver_sql(f'DROP SCHEMA "{self.schema}" CASCADE')
            conn.commit()

    def _worker(self, action):
        with self.engine.connect() as conn:
            conn.exec_driver_sql(f'SET search_path TO "{self.schema}"')
            # Commit SET before binding a Session so the Session owns the
            # application transaction rather than joining an external one.
            conn.commit()
            try:
                with Session(bind=conn) as db:
                    return action(db)
            finally:
                if conn.in_transaction():
                    conn.rollback()
                conn.exec_driver_sql("RESET search_path")
                conn.commit()

    def _adjust(self, db, direction, quantity, key, item_id=1):
        return InventoryService(db).adjust_stock(
            InventoryAdjustRequest(item_id=item_id, transaction_type=direction, quantity=Decimal(str(quantity))),
            self.user,
            key,
        )

    def _parallel(self, actions):
        barrier = Barrier(len(actions))
        def run(action):
            def wrapped(db):
                barrier.wait(timeout=10)
                try:
                    return ("ok", action(db))
                except HTTPException as error:
                    return ("http", error.status_code, error.detail)
            return self._worker(wrapped)
        with ThreadPoolExecutor(max_workers=len(actions)) as pool:
            return list(pool.map(run, actions))

    def _balance(self, item_id=1):
        return self._worker(lambda db: db.get(InventoryBalance, (1, item_id)).quantity)

    def _event_count(self, ref_type="MANUAL"):
        return self._worker(lambda db: db.query(InventoryLedger).filter_by(reference_type=ref_type).count())

    def test_two_consumers_cannot_both_take_same_stock(self):
        self._worker(lambda db: self._adjust(db, "IN", 5, "seed-limited"))
        results = self._parallel([
            lambda db: self._adjust(db, "OUT", 4, "consume-a"),
            lambda db: self._adjust(db, "OUT", 4, "consume-b"),
        ])
        self.assertEqual(["http", "ok"], sorted((result[0] for result in results)))
        self.assertEqual(Decimal("1.000000"), self._balance())
        self.assertEqual(Decimal("1.000000"), self._worker(
            lambda db: InventoryService(db).repo.ledger_balance(1, 1)
        ))

    def test_concurrent_receipt_and_issue_preserve_nonnegative_projection(self):
        self._worker(lambda db: self._adjust(db, "IN", 5, "seed-mixed"))
        results = self._parallel([
            lambda db: self._adjust(db, "IN", 3, "receipt-mixed"),
            lambda db: self._adjust(db, "OUT", 7, "issue-mixed"),
        ])
        self.assertIn(Decimal(str(self._balance())), (Decimal("1.000000"), Decimal("8.000000")))
        self.assertEqual(self._balance(), self._worker(lambda db: InventoryService(db).repo.ledger_balance(1, 1)))
        self.assertGreaterEqual(sum(result[0] == "ok" for result in results), 1)

    def test_first_balance_row_creation_race(self):
        results = self._parallel([
            lambda db: self._adjust(db, "IN", 2, "first-row-a", item_id=2),
            lambda db: self._adjust(db, "IN", 3, "first-row-b", item_id=2),
        ])
        self.assertEqual(["ok", "ok"], sorted(result[0] for result in results))
        self.assertEqual(Decimal("5.000000"), self._balance(2))
        self.assertEqual(1, self._worker(lambda db: db.query(InventoryBalance).filter_by(organization_id=1, item_id=2).count()))

    def test_concurrent_duplicate_idempotency_key_posts_once(self):
        results = self._parallel([
            lambda db: self._adjust(db, "IN", 2, "same-request"),
            lambda db: self._adjust(db, "IN", 2, "same-request"),
        ])
        self.assertEqual(["ok", "ok"], sorted(result[0] for result in results))
        self.assertEqual(results[0][1]["id"], results[1][1]["id"])
        self.assertEqual(Decimal("2.000000"), self._balance())
        self.assertEqual(1, self._event_count())

    def test_concurrent_sale_create_retry_returns_one_source_and_one_movement(self):
        self._worker(lambda db: self._adjust(db, "IN", 5, "seed-sale-retry"))
        payload = SaleCreate(
            sale_date=datetime(2026, 10, 1), customer_id=1, crop_id=1,
            quantity=Decimal("4"), rate_per_unit=Decimal("5"),
        )
        results = self._parallel([
            lambda db: SaleService(db).create_sale(payload, self.user, "sale-retry-key"),
            lambda db: SaleService(db).create_sale(payload, self.user, "sale-retry-key"),
        ])
        self.assertEqual(["ok", "ok"], sorted(result[0] for result in results))
        self.assertEqual(results[0][1].id, results[1][1].id)
        self.assertEqual(1, self._worker(lambda db: db.query(Sale).count()))
        self.assertEqual(1, self._event_count("SALE"))
        self.assertEqual(Decimal("1.000000"), self._balance())

    def test_concurrent_procurement_create_retry_returns_one_source_and_one_movement(self):
        payload = ProcurementCreate(
            procurement_date=datetime(2026, 10, 1), farmer_id=1, crop_id=1,
            quantity=Decimal("2.5"), rate_per_unit=Decimal("5"),
        )
        results = self._parallel([
            lambda db: ProcurementService(db).create_procurement(payload, self.user, "proc-retry-key"),
            lambda db: ProcurementService(db).create_procurement(payload, self.user, "proc-retry-key"),
        ])
        self.assertEqual(["ok", "ok"], sorted(result[0] for result in results))
        self.assertEqual(results[0][1].id, results[1][1].id)
        self.assertEqual(1, self._worker(lambda db: db.query(Procurement).count()))
        self.assertEqual(1, self._event_count("PROCUREMENT"))
        self.assertEqual(Decimal("2.500000"), self._balance())

    def test_multi_item_postings_lock_in_sorted_order(self):
        def both(db, prefix, reverse):
            ids = [2, 1] if reverse else [1, 2]
            rows = InventoryPostingService(db).post_events([
                StockEvent(1, item_id, "IN", Decimal("1"), "TEST", None,
                           f"{prefix}-{item_id}") for item_id in ids
            ])
            # post_events flushes as part of its caller-owned transaction;
            # commit here to model a source service's atomic transaction.
            db.commit()
            return rows
        results = self._parallel([
            lambda db: both(db, "ordered-a", False),
            lambda db: both(db, "ordered-b", True),
        ])
        self.assertTrue(all(result[0] == "ok" for result in results))
        self.assertEqual(Decimal("2.000000"), self._balance(1))
        self.assertEqual(Decimal("2.000000"), self._balance(2))

    def test_ledger_failure_rolls_back_balance_projection(self):
        def install_trigger(db):
            db.execute(text(
                "CREATE FUNCTION fail_inventory_test() RETURNS trigger LANGUAGE plpgsql AS "
                "$$ BEGIN RAISE EXCEPTION 'forced inventory insert failure'; END $$"
            ))
            db.execute(text(
                "CREATE TRIGGER fail_inventory_insert BEFORE INSERT ON inventory_ledger "
                "FOR EACH ROW EXECUTE FUNCTION fail_inventory_test()"
            ))
            db.commit()
        self._worker(install_trigger)
        with self.assertRaises(DBAPIError):
            self._worker(lambda db: self._adjust(db, "IN", 4, "rollback-pg"))
        self.assertIsNone(self._worker(lambda db: db.get(InventoryBalance, (1, 1))))
        self.assertEqual(0, self._event_count())

    def test_migration_backfills_item_ids_and_balances_without_changing_history(self):
        schema = "inventory_migration_test_" + uuid4().hex
        try:
            with self.engine.connect() as conn:
                conn.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
                conn.exec_driver_sql(f'SET search_path TO "{schema}"')
                for ddl in (
                    "CREATE TABLE organizations(id integer PRIMARY KEY, organization_name varchar(255) NOT NULL, registration_number varchar(100) NOT NULL UNIQUE)",
                    "CREATE TABLE crop_masters(id integer PRIMARY KEY, crop_code varchar(50) NOT NULL, crop_name varchar(150) NOT NULL, crop_category varchar(100), unit varchar(20) NOT NULL DEFAULT 'Kg', is_active boolean NOT NULL DEFAULT true)",
                    "CREATE TABLE procurements(id integer PRIMARY KEY, organization_id integer NOT NULL, crop_id integer NOT NULL, quantity double precision NOT NULL, is_active boolean NOT NULL)",
                    "CREATE TABLE sales(id integer PRIMARY KEY, organization_id integer NOT NULL, crop_id integer NOT NULL, quantity double precision NOT NULL, is_active boolean NOT NULL)",
                    "CREATE TABLE inventory_ledger(id SERIAL PRIMARY KEY, organization_id integer NOT NULL, crop_id integer NOT NULL, transaction_type varchar(10) NOT NULL, quantity double precision NOT NULL, reference_type varchar(20) NOT NULL, reference_id integer, remarks varchar(500), is_active boolean NOT NULL, created_at timestamptz, updated_at timestamptz, CONSTRAINT uq_inventory_reference UNIQUE(organization_id,reference_type,reference_id))",
                ):
                    conn.execute(text(ddl))
                conn.execute(text("INSERT INTO organizations VALUES (1,'Migrate FPO','M-1')"))
                conn.execute(text(
                    "INSERT INTO crop_masters(id,crop_code,crop_name,crop_category,unit,is_active) "
                    "VALUES (1,'AGR-1','Wheat',NULL,'KG',true)"
                ))
                conn.execute(text("INSERT INTO procurements VALUES (7,1,1,12.5,true)"))
                conn.execute(text("INSERT INTO sales VALUES (8,1,1,4.25,true)"))
                conn.execute(text("INSERT INTO inventory_ledger VALUES (41,1,1,'IN',12.5,'PROCUREMENT',7,'old receipt',true,now(),now()), (42,1,1,'OUT',4.25,'SALE',8,'old sale',true,now(),now()), (43,1,1,'IN',2,'MANUAL',NULL,'old manual receipt',true,now(),now()), (44,1,1,'OUT',100,'MANUAL',NULL,'inactive legacy issue',false,now(),now())"))
                conn.execute(text(
                    "SELECT setval(pg_get_serial_sequence('inventory_ledger','id'), "
                    "(SELECT max(id) FROM inventory_ledger), true)"
                ))
                conn.commit()

                versions = Path(__file__).parents[1] / "migrations" / "versions"
                for revision, module_name in (
                    ("0014", "inventory_catalogue_migration_test"),
                    ("0015", "inventory_ledger_migration_test"),
                    ("0016", "inventory_request_keys_migration_test"),
                ):
                    path = next(versions.glob(f"{revision}_*.py"))
                    spec = spec_from_file_location(module_name, path)
                    migration = module_from_spec(spec)
                    spec.loader.exec_module(migration)
                    with Operations.context(MigrationContext.configure(conn)):
                        migration.upgrade()

                crop_defaults = conn.execute(text(
                    "SELECT item_type,base_unit,organization_id FROM crop_masters WHERE id=1"
                )).one()
                self.assertEqual(("AGRICULTURAL_COMMODITY", "KG", None), tuple(crop_defaults))
                rows = conn.execute(text(
                    "SELECT id,crop_id,item_id,quantity,reference_type,reference_id,is_active "
                    "FROM inventory_ledger ORDER BY id"
                )).all()
                balance = conn.execute(text(
                    "SELECT quantity FROM inventory_balances WHERE organization_id=1 AND item_id=1"
                )).scalar_one()
                self.assertEqual([41, 42, 43, 44], [row.id for row in rows])
                self.assertEqual([(1, 1, Decimal("12.500000"), "PROCUREMENT", 7, True),
                                  (1, 1, Decimal("4.250000"), "SALE", 8, True),
                                  (1, 1, Decimal("2.000000"), "MANUAL", None, True),
                                  (1, 1, Decimal("100.000000"), "MANUAL", None, False)],
                                 [(row.crop_id, row.item_id, row.quantity, row.reference_type, row.reference_id, row.is_active) for row in rows])
                self.assertEqual(Decimal("10.250000"), balance)
                self.assertEqual(
                    {"organization_id", "operation", "idempotency_key", "payload_hash", "source_id", "created_at"},
                    {column["name"] for column in inspect(conn).get_columns("inventory_create_requests")},
                )
                # The migrated PostgreSQL trigger enforces crop identity/type
                # even for direct SQL, independently of application validation.
                conn.execute(text(
                    "INSERT INTO crop_masters(id,crop_code,crop_name,item_type,organization_id,base_unit) "
                    "VALUES (2,'RAW-1','Material','RAW_MATERIAL',1,'KG')"
                ))
                with self.assertRaises(DBAPIError):
                    with conn.begin_nested():
                        conn.execute(text(
                            "INSERT INTO inventory_ledger(organization_id,crop_id,item_id,transaction_type,"
                            "quantity,reference_type,reference_id,idempotency_key,source_revision,is_active) "
                            "VALUES (1,2,2,'IN',1,'MANUAL',NULL,'invalid-generic-crop',1,true)"
                        ))
                conn.execute(text(
                    "INSERT INTO inventory_ledger(organization_id,crop_id,item_id,transaction_type,"
                    "quantity,reference_type,reference_id,idempotency_key,source_revision,is_active) "
                    "VALUES (1,NULL,2,'IN',1,'MANUAL',NULL,'valid-generic-item',1,true)"
                ))
                conn.execute(text(
                    "INSERT INTO inventory_ledger(organization_id,crop_id,item_id,transaction_type,"
                    "quantity,reference_type,reference_id,idempotency_key,source_revision,is_active) "
                    "VALUES (1,1,1,'IN',1,'MANUAL',NULL,'valid-agricultural-crop',1,true)"
                ))
                conn.exec_driver_sql(f'DROP SCHEMA "{schema}" CASCADE')
                conn.commit()
        except Exception:
            with self.engine.connect() as conn:
                conn.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
                conn.commit()
            raise

    def test_migration_preflight_rejects_linked_source_mismatches_before_ddl(self):
        scenarios = ("missing_source", "wrong_organization", "wrong_crop", "wrong_quantity", "wrong_status", "unknown_reference", "duplicate_link")
        path = Path(__file__).parents[1] / "migrations" / "versions" / "0015_upgrade_inventory_ledger.py"
        spec = spec_from_file_location("inventory_preflight_test", path)
        migration = module_from_spec(spec)
        spec.loader.exec_module(migration)
        for scenario in scenarios:
            schema = "inventory_preflight_test_" + uuid4().hex
            try:
                with self.engine.connect() as conn:
                    conn.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
                    conn.exec_driver_sql(f'SET search_path TO "{schema}"')
                    ledger_ddl = (
                        "CREATE TABLE inventory_ledger(id integer PRIMARY KEY, organization_id integer NOT NULL, crop_id integer NOT NULL, transaction_type varchar(10) NOT NULL, quantity double precision NOT NULL, reference_type varchar(20) NOT NULL, reference_id integer, remarks varchar(500), is_active boolean NOT NULL, created_at timestamptz, updated_at timestamptz, CONSTRAINT uq_inventory_reference UNIQUE(organization_id,reference_type,reference_id))"
                    )
                    if scenario == "duplicate_link":
                        ledger_ddl = ledger_ddl.replace(
                            ", CONSTRAINT uq_inventory_reference UNIQUE(organization_id,reference_type,reference_id)",
                            "",
                        )
                    for ddl in (
                        "CREATE TABLE organizations(id integer PRIMARY KEY, organization_name varchar(255) NOT NULL, registration_number varchar(100) NOT NULL UNIQUE)",
                        "CREATE TABLE crop_masters(id integer PRIMARY KEY, item_type varchar(40) NOT NULL)",
                        "CREATE TABLE procurements(id integer PRIMARY KEY, organization_id integer NOT NULL, crop_id integer NOT NULL, quantity double precision NOT NULL, is_active boolean NOT NULL)",
                        "CREATE TABLE sales(id integer PRIMARY KEY, organization_id integer NOT NULL, crop_id integer NOT NULL, quantity double precision NOT NULL, is_active boolean NOT NULL)",
                        ledger_ddl,
                    ):
                        conn.execute(text(ddl))
                    conn.execute(text("INSERT INTO organizations VALUES (1,'FPO','P-1'),(2,'Other','P-2')"))
                    conn.execute(text("INSERT INTO crop_masters VALUES (1,'AGRICULTURAL_COMMODITY'),(2,'AGRICULTURAL_COMMODITY')"))
                    p_org, p_crop, p_qty, p_active = 1, 1, 12.5, True
                    ref_type, ref_id, ledger_org, ledger_crop, ledger_qty, ledger_active = "PROCUREMENT", 7, 1, 1, 12.5, True
                    if scenario == "missing_source": ref_id = 999
                    elif scenario == "wrong_organization": ledger_org = 2
                    elif scenario == "wrong_crop": p_crop = 2
                    elif scenario == "wrong_quantity": p_qty = 12
                    elif scenario == "wrong_status": p_active = False
                    elif scenario == "unknown_reference": ref_type, ref_id = "UNKNOWN", 7
                    conn.execute(text("INSERT INTO procurements VALUES (7,:org,:crop,:qty,:active)"), {"org": p_org, "crop": p_crop, "qty": p_qty, "active": p_active})
                    conn.execute(text("INSERT INTO inventory_ledger VALUES (41,:org,:crop,'IN',:qty,:type,:ref,'legacy',:active,now(),now())"), {"org": ledger_org, "crop": ledger_crop, "qty": ledger_qty, "type": ref_type, "ref": ref_id, "active": ledger_active})
                    if scenario == "duplicate_link":
                        conn.execute(text("INSERT INTO inventory_ledger VALUES (42,1,1,'IN',12.5,'PROCUREMENT',7,'duplicate',true,now(),now())"))
                    conn.commit()
                    def schema_snapshot():
                        catalog = inspect(conn)
                        table_names = sorted(catalog.get_table_names(schema=schema))
                        return {
                            "tables": {
                                table_name: {
                                    "columns": tuple(
                                        (column["name"], str(column["type"]), column["nullable"], column["default"])
                                        for column in catalog.get_columns(table_name, schema=schema)
                                    ),
                                    "primary_key": catalog.get_pk_constraint(table_name, schema=schema),
                                    "foreign_keys": catalog.get_foreign_keys(table_name, schema=schema),
                                    "unique_constraints": catalog.get_unique_constraints(table_name, schema=schema),
                                    "check_constraints": catalog.get_check_constraints(table_name, schema=schema),
                                    "indexes": catalog.get_indexes(table_name, schema=schema),
                                }
                                for table_name in table_names
                            },
                            "sequences": tuple(sorted(catalog.get_sequence_names(schema=schema))),
                        }
                    before_schema = schema_snapshot()
                    with self.assertRaises(RuntimeError, msg=scenario):
                        with Operations.context(MigrationContext.configure(conn)):
                            migration.upgrade()
                    self.assertEqual(before_schema, schema_snapshot(), scenario)
                    conn.exec_driver_sql(f'DROP SCHEMA "{schema}" CASCADE')
                    conn.commit()
            except Exception:
                with self.engine.connect() as conn:
                    conn.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
                    conn.commit()
                raise


if __name__ == "__main__":
    unittest.main()
