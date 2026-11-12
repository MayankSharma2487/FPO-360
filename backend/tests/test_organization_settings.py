import unittest
from types import SimpleNamespace

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database.database import Base
from app.models.organization import Organization
from app.schemas.organization_settings import OrganizationSettingsUpdate
from app.services.organization_settings_service import OrganizationSettingsService


class OrganizationSettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import app.main  # noqa: F401 - register all mapped tables
        cls.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        Base.metadata.create_all(cls.engine)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def setUp(self):
        self.connection = self.engine.connect()
        self.db = Session(bind=self.connection)
        for table in reversed(Base.metadata.sorted_tables):
            self.db.execute(table.delete())
        self.db.add_all([
            Organization(id=1, organization_name="First FPO", registration_number="FPO-1"),
            Organization(id=2, organization_name="Second FPO", registration_number="FPO-2"),
        ])
        self.db.commit()
        self.service = OrganizationSettingsService(self.db)
        self.fpo_admin = SimpleNamespace(
            organization_id=1, role=SimpleNamespace(name="FPO Admin")
        )
        self.super_admin = SimpleNamespace(
            organization_id=1, role=SimpleNamespace(name="Super Admin")
        )

    def tearDown(self):
        self.db.close()
        self.connection.close()

    def test_fpo_admin_can_create_and_read_own_settings(self):
        created = self.service.upsert_settings(
            1, OrganizationSettingsUpdate(email="contact@example.org"), self.fpo_admin
        )
        self.assertEqual("contact@example.org", created.email)
        self.assertEqual(created.id, self.service.get_settings(1, self.fpo_admin).id)

    def test_fpo_admin_cannot_read_or_write_another_organization(self):
        with self.assertRaises(HTTPException) as read_error:
            self.service.get_settings(2, self.fpo_admin)
        self.assertEqual(403, read_error.exception.status_code)

        with self.assertRaises(HTTPException) as write_error:
            self.service.upsert_settings(2, OrganizationSettingsUpdate(address="private"), self.fpo_admin)
        self.assertEqual(403, write_error.exception.status_code)
        self.assertIsNone(self.service.repo.get_by_organization_id(2))

    def test_super_admin_access_requires_an_existing_explicit_organization_id(self):
        created = self.service.upsert_settings(
            2, OrganizationSettingsUpdate(website="https://example.org"), self.super_admin
        )
        self.assertEqual(2, created.organization_id)
        with self.assertRaises(HTTPException) as missing_error:
            self.service.upsert_settings(99, OrganizationSettingsUpdate(), self.super_admin)
        self.assertEqual(404, missing_error.exception.status_code)

    def test_missing_settings_returns_not_found_for_frontend_empty_state(self):
        with self.assertRaises(HTTPException) as error:
            self.service.get_settings(1, self.fpo_admin)
        self.assertEqual(404, error.exception.status_code)

    def test_settings_fields_cannot_exceed_database_column_lengths(self):
        with self.assertRaises(ValidationError):
            OrganizationSettingsUpdate(phone="1" * 21)
        with self.assertRaises(ValidationError):
            OrganizationSettingsUpdate(address="x" * 501)
        with self.assertRaises(ValidationError):
            OrganizationSettingsUpdate(website="https://example.org/" + "x" * 240)


if __name__ == "__main__":
    unittest.main()
