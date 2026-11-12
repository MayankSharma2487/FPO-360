"""Production stock serialization tests; requires a guarded disposable PG URL."""
import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import date
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
from sqlalchemy.orm import Session

from postgres_test_safety import validate_test_database_url
from app.domain.item_catalogue import BaseUnit
from app.models.crop_master import CropMaster
from app.models.inventory import InventoryBalance, InventoryLedger
from app.models.organization import Organization
from app.models.production import ProductionInput, ProductionRecord
from app.models.role import Role
from app.models.user import User
from app.schemas.production import ProductionCreate
from app.services.inventory_posting_service import InventoryPostingService, StockEvent
from app.services.production_service import ProductionService


TEST_URL_ENV = "INVENTORY_TEST_DATABASE_URL"


class PostgreSQLProductionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        url = os.getenv(TEST_URL_ENV)
        if not url:
            raise unittest.SkipTest(f"{TEST_URL_ENV} is not configured")
        cls.test_database_url = validate_test_database_url(url)
        cls.engine = create_engine(cls.test_database_url, pool_size=5, max_overflow=4)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "engine"):
            validate_test_database_url(os.getenv(TEST_URL_ENV))
            cls.engine.dispose()

    def setUp(self):
        validate_test_database_url(os.getenv(TEST_URL_ENV))
        import app.main  # noqa: F401 - register mapped relationships
        self.schema = "production_test_" + uuid4().hex
        with self.engine.connect() as connection:
            connection.exec_driver_sql(f'CREATE SCHEMA "{self.schema}"')
            connection.exec_driver_sql(f'SET search_path TO "{self.schema}"')
            connection.commit()
            try:
                for model in (
                    Organization, Role, User, CropMaster, InventoryBalance, InventoryLedger,
                    ProductionRecord, ProductionInput,
                ):
                    model.__table__.create(connection)
                connection.execute(text(
                    "INSERT INTO organizations(id,organization_name,registration_number) "
                    "VALUES (1,'Production Test FPO','PROD-TEST')"
                ))
                connection.execute(text(
                    "INSERT INTO crop_masters(id,crop_code,crop_name,unit,item_type,organization_id,base_unit,is_active) VALUES "
                    "(1,'RAW-1','Raw Grain','KG','RAW_MATERIAL',1,'KG',true), "
                    "(2,'PKG-1','Pouch','PCS','PACKAGING_MATERIAL',1,'PCS',true), "
                    "(3,'FG-1','Packed Product','PCS','FINISHED_GOOD',1,'PCS',true)"
                ))
                connection.commit()
            except Exception:
                connection.rollback()
                connection.exec_driver_sql("RESET search_path")
                connection.commit()
                validate_test_database_url(os.getenv(TEST_URL_ENV))
                with self.engine.connect() as cleanup:
                    cleanup.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{self.schema}" CASCADE')
                    cleanup.commit()
                raise
            connection.exec_driver_sql("RESET search_path")
            connection.commit()
        self.user = SimpleNamespace(id=None, organization_id=1, role=SimpleNamespace(name="FPO Admin"))
        self._worker(self._seed_stock)

    @staticmethod
    def _seed_stock(db):
        InventoryPostingService(db).post_events([
            StockEvent(1, 1, "IN", Decimal("10"), "MANUAL", None, "fixture-raw", "Fixture stock"),
            StockEvent(1, 2, "IN", Decimal("10"), "MANUAL", None, "fixture-package", "Fixture stock"),
        ])
        db.commit()

    def tearDown(self):
        validate_test_database_url(os.getenv(TEST_URL_ENV))
        with self.engine.connect() as connection:
            connection.exec_driver_sql(f'DROP SCHEMA "{self.schema}" CASCADE')
            connection.commit()

    def _worker(self, action):
        validate_test_database_url(os.getenv(TEST_URL_ENV))
        with self.engine.connect() as connection:
            connection.exec_driver_sql(f'SET search_path TO "{self.schema}"')
            connection.commit()
            try:
                with Session(bind=connection) as db:
                    return action(db)
            finally:
                if connection.in_transaction():
                    connection.rollback()
                connection.exec_driver_sql("RESET search_path")
                connection.commit()

    @staticmethod
    def _payload(raw_quantity="2"):
        return ProductionCreate(
            production_date=date(2026, 10, 30),
            finished_item_id=3,
            output_quantity=Decimal("3"),
            output_unit=BaseUnit.PCS,
            inputs=[
                {"item_id": 1, "quantity": Decimal(raw_quantity), "unit": BaseUnit.KG},
                {"item_id": 2, "quantity": Decimal("2"), "unit": BaseUnit.PCS},
            ],
            wastage_quantity=Decimal("0"),
            wastage_unit=BaseUnit.PCS,
        )

    def _parallel(self, actions):
        barrier = Barrier(len(actions))

        def run(action):
            def wrapped(db):
                barrier.wait(timeout=10)
                try:
                    return ("ok", action(ProductionService(db)))
                except HTTPException as error:
                    return ("http", error.status_code, error.detail)
            return self._worker(wrapped)

        with ThreadPoolExecutor(max_workers=len(actions)) as pool:
            return list(pool.map(run, actions))

    def test_duplicate_concurrent_requests_return_one_production_and_one_event_set(self):
        results = self._parallel([
            lambda service: service.create(self._payload(), self.user, "same-production-key"),
            lambda service: service.create(self._payload(), self.user, "same-production-key"),
        ])
        self.assertEqual(["ok", "ok"], sorted(result[0] for result in results))
        self.assertEqual(1, len({result[1]["id"] for result in results}))
        self.assertEqual(1, self._worker(lambda db: db.query(ProductionRecord).count()))
        self.assertEqual(3, self._worker(lambda db: db.query(InventoryLedger).filter_by(reference_type="PRODUCTION").count()))
        self.assertEqual(Decimal("8.000000"), self._worker(lambda db: db.get(InventoryBalance, (1, 1)).quantity))

    def test_competing_production_requests_cannot_overconsume_shared_inputs(self):
        results = self._parallel([
            lambda service: service.create(self._payload("7"), self.user, "production-consume-a"),
            lambda service: service.create(self._payload("7"), self.user, "production-consume-b"),
        ])
        self.assertEqual(["http", "ok"], sorted(result[0] for result in results))
        failure = next(result for result in results if result[0] == "http")
        self.assertEqual(400, failure[1])
        self.assertEqual(1, self._worker(lambda db: db.query(ProductionRecord).count()))
        self.assertEqual(Decimal("3.000000"), self._worker(lambda db: db.get(InventoryBalance, (1, 1)).quantity))
        self.assertEqual(Decimal("8.000000"), self._worker(lambda db: db.get(InventoryBalance, (1, 2)).quantity))
        self.assertEqual(Decimal("3.000000"), self._worker(lambda db: db.get(InventoryBalance, (1, 3)).quantity))

    def test_migration_0017_upgrade_and_downgrade(self):
        validate_test_database_url(os.getenv(TEST_URL_ENV))
        schema = "production_migration_test_" + uuid4().hex
        try:
            with self.engine.connect() as conn:
                conn.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
                conn.exec_driver_sql(f'SET search_path TO "{schema}"')
                for ddl in (
                    "CREATE TABLE organizations (id integer PRIMARY KEY, organization_name varchar(255) NOT NULL, registration_number varchar(100) NOT NULL UNIQUE)",
                    "CREATE TABLE users (id integer PRIMARY KEY, email varchar(255) NOT NULL UNIQUE, hashed_password varchar(255) NOT NULL, full_name varchar(255) NOT NULL, is_active boolean NOT NULL DEFAULT true)",
                    "CREATE TABLE crop_masters (id integer PRIMARY KEY, crop_code varchar(50) NOT NULL, crop_name varchar(150) NOT NULL, crop_category varchar(100), unit varchar(20) NOT NULL DEFAULT 'KG', item_type varchar(40) NOT NULL DEFAULT 'AGRICULTURAL_COMMODITY', organization_id integer REFERENCES organizations(id), base_unit varchar(20) NOT NULL DEFAULT 'KG', is_active boolean NOT NULL DEFAULT true)",
                    "CREATE TABLE inventory_ledger (id SERIAL PRIMARY KEY, organization_id integer NOT NULL REFERENCES organizations(id), item_id integer NOT NULL REFERENCES crop_masters(id), crop_id integer, transaction_type varchar(10) NOT NULL, quantity numeric(20,6) NOT NULL, reference_type varchar(20) NOT NULL, reference_id integer, idempotency_key varchar(128) NOT NULL, source_revision integer NOT NULL DEFAULT 1, reverses_id integer REFERENCES inventory_ledger(id), remarks varchar(500), is_active boolean NOT NULL DEFAULT true, created_at timestamptz DEFAULT now(), updated_at timestamptz DEFAULT now())",
                ):
                    conn.execute(text(ddl))
                conn.execute(text("INSERT INTO organizations VALUES (1, 'Prod Mig FPO', 'PMG-1')"))
                conn.execute(text("INSERT INTO users VALUES (1, 'admin@example.com', 'hash', 'Admin', true)"))
                conn.execute(text("INSERT INTO crop_masters (id, crop_code, crop_name, item_type, organization_id, base_unit) VALUES (1, 'RAW-1', 'Raw Material', 'RAW_MATERIAL', 1, 'KG'), (2, 'FG-1', 'Finished Good', 'FINISHED_GOOD', 1, 'PCS')"))
                conn.commit()

                path = Path(__file__).parents[1] / "migrations" / "versions" / "0017_create_production_packing.py"
                spec = spec_from_file_location("production_migration_0017_test", path)
                migration = module_from_spec(spec)
                spec.loader.exec_module(migration)

                with Operations.context(MigrationContext.configure(conn)):
                    migration.upgrade()

                inspector = inspect(conn)
                self.assertIn("production_records", inspector.get_table_names(schema=schema))
                self.assertIn("production_inputs", inspector.get_table_names(schema=schema))

                rec_cols = {c["name"]: str(c["type"]) for c in inspector.get_columns("production_records", schema=schema)}
                self.assertIn("reference_no", rec_cols)
                self.assertIn("idempotency_key", rec_cols)
                self.assertIn("finished_item_id", rec_cols)
                self.assertIn("output_quantity", rec_cols)

                inp_cols = {c["name"]: str(c["type"]) for c in inspector.get_columns("production_inputs", schema=schema)}
                self.assertIn("production_id", inp_cols)
                self.assertIn("item_id", inp_cols)
                self.assertIn("quantity", inp_cols)

                conn.execute(text(
                    "INSERT INTO production_records (id, organization_id, reference_no, idempotency_key, payload_hash, production_date, finished_item_id, output_quantity, output_unit, output_base_quantity, wastage_quantity, wastage_unit, wastage_base_quantity, status) "
                    "VALUES (1, 1, 'PR-001', 'key-001', 'hash001', '2026-10-30', 2, 10, 'PCS', 10, 0, 'PCS', 0, 'POSTED')"
                ))
                conn.execute(text(
                    "INSERT INTO production_inputs (id, production_id, organization_id, item_id, input_type, quantity, unit, base_quantity) "
                    "VALUES (1, 1, 1, 1, 'RAW_MATERIAL', 5, 'KG', 5)"
                ))
                conn.commit()

                conn.execute(text(
                    "INSERT INTO inventory_ledger (organization_id, item_id, transaction_type, quantity, reference_type, reference_id, idempotency_key, is_active) "
                    "VALUES (1, 2, 'IN', 10, 'PRODUCTION', 1, 'LEDGER:PR:1', true)"
                ))
                conn.commit()

                with self.assertRaises(RuntimeError):
                    with Operations.context(MigrationContext.configure(conn)):
                        migration.downgrade()

                conn.execute(text("DELETE FROM inventory_ledger WHERE reference_type = 'PRODUCTION'"))
                conn.commit()

                with Operations.context(MigrationContext.configure(conn)):
                    migration.downgrade()

                inspector_after = inspect(conn)
                self.assertNotIn("production_records", inspector_after.get_table_names(schema=schema))
                self.assertNotIn("production_inputs", inspector_after.get_table_names(schema=schema))

                conn.exec_driver_sql(f'DROP SCHEMA "{schema}" CASCADE')
                conn.commit()
        except Exception:
            validate_test_database_url(os.getenv(TEST_URL_ENV))
            with self.engine.connect() as conn:
                conn.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
                conn.commit()
            raise


if __name__ == "__main__":
    unittest.main()
