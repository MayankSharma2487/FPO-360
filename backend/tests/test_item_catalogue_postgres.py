"""PostgreSQL concurrency test; requires ITEM_CATALOGUE_TEST_DATABASE_URL."""
import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.models.crop_master import CropMaster
from app.schemas.item import ItemCreate
from app.services.item_service import ItemService
from app.domain.item_catalogue import BaseUnit, ItemType
from postgres_test_safety import validate_test_database_url


class PostgreSQLItemCodeConcurrencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import app.main  # noqa: F401, register ORM relationship targets
        url = os.getenv("ITEM_CATALOGUE_TEST_DATABASE_URL")
        if not url:
            raise unittest.SkipTest("ITEM_CATALOGUE_TEST_DATABASE_URL is not configured")
        cls.test_database_url = validate_test_database_url(url)
        cls.engine = create_engine(cls.test_database_url)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "engine"):
            validate_test_database_url(os.getenv("ITEM_CATALOGUE_TEST_DATABASE_URL"))
            cls.engine.dispose()

    def test_parallel_creates_receive_distinct_codes(self):
        validate_test_database_url(os.getenv("ITEM_CATALOGUE_TEST_DATABASE_URL"))
        schema = "item_code_test_" + uuid4().hex
        try:
            with self.engine.connect() as connection:
                connection.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
                connection.exec_driver_sql(f'SET search_path TO "{schema}"')
                connection.execute(text(
                    "CREATE TABLE organizations (id integer PRIMARY KEY, organization_name varchar(255) NOT NULL, "
                    "registration_number varchar(100) NOT NULL UNIQUE)"
                ))
                connection.execute(text("INSERT INTO organizations VALUES (1, 'Test FPO', 'ITEM-CODE-TEST')"))
                CropMaster.__table__.create(connection)
                connection.commit()
                connection.exec_driver_sql("RESET search_path")
                connection.commit()
        except Exception:
            # The locally generated name keeps partial-setup cleanup within
            # this fixture's schema namespace.
            validate_test_database_url(os.getenv("ITEM_CATALOGUE_TEST_DATABASE_URL"))
            with self.engine.connect() as connection:
                connection.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
                connection.commit()
            raise

        def create_one(index):
            with self.engine.connect() as connection:
                connection.exec_driver_sql(f'SET search_path TO "{schema}"')
                connection.commit()
                try:
                    with Session(bind=connection) as db:
                        user = SimpleNamespace(organization_id=1, role=SimpleNamespace(name="FPO Admin"))
                        item = ItemService(db).create_item(ItemCreate(
                            item_name=f"Concurrent item {index}",
                            item_type=ItemType.PURCHASED_PRODUCT,
                            base_unit=BaseUnit.PCS,
                        ), user)
                        return item["item_code"]
                finally:
                    if connection.in_transaction():
                        connection.rollback()
                    connection.exec_driver_sql("RESET search_path")
                    connection.commit()

        try:
            with ThreadPoolExecutor(max_workers=4) as executor:
                codes = list(executor.map(create_one, range(4)))
            self.assertEqual(4, len(set(codes)))
            self.assertTrue(all(code.startswith("PUR-") for code in codes))
        finally:
            validate_test_database_url(os.getenv("ITEM_CATALOGUE_TEST_DATABASE_URL"))
            with self.engine.connect() as connection:
                connection.exec_driver_sql(f'DROP SCHEMA "{schema}" CASCADE')
                connection.commit()


if __name__ == "__main__":
    unittest.main()
