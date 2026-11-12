import unittest
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.auth.dependencies import get_current_user
from app.database.database import Base, get_db
from app.models.organization import Organization


class OrganizationSettingsApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app.main import app

        cls.app = app
        cls.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        Base.metadata.create_all(cls.engine)

    @classmethod
    def tearDownClass(cls):
        cls.app.dependency_overrides.clear()
        cls.engine.dispose()

    def setUp(self):
        with Session(self.engine) as db:
            for table in reversed(Base.metadata.sorted_tables):
                db.execute(table.delete())
            db.add_all([
                Organization(id=1, organization_name="First FPO", registration_number="API-FPO-1"),
                Organization(id=2, organization_name="Second FPO", registration_number="API-FPO-2"),
            ])
            db.commit()

        self.user = SimpleNamespace(
            organization_id=1, role=SimpleNamespace(name="FPO Admin")
        )

        def override_db():
            with Session(self.engine) as db:
                yield db

        self.app.dependency_overrides[get_db] = override_db
        self.app.dependency_overrides[get_current_user] = lambda: self.user
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()
        self.app.dependency_overrides.clear()

    def test_put_then_get_settings_persists_without_local_database(self):
        payload = {
            "logo_url": "https://example.test/logo.png",
            "address": "Test-only address",
            "phone": "9000000000",
            "email": "agent-test@example.com",
            "website": "https://example.test",
        }
        saved = self.client.put("/organizations/1/settings", json=payload)
        self.assertEqual(200, saved.status_code)
        self.assertEqual(1, saved.json()["organization_id"])

        loaded = self.client.get("/organizations/1/settings")
        self.assertEqual(200, loaded.status_code)
        self.assertEqual(payload, {key: loaded.json()[key] for key in payload})

    def test_tenant_cannot_read_or_write_another_organizations_settings(self):
        denied_read = self.client.get("/organizations/2/settings")
        denied_write = self.client.put(
            "/organizations/2/settings", json={"address": "must not persist"}
        )
        self.assertEqual(403, denied_read.status_code)
        self.assertEqual(403, denied_write.status_code)

        with Session(self.engine) as db:
            from app.models.organization_settings import OrganizationSettings

            self.assertIsNone(db.query(OrganizationSettings).filter_by(organization_id=2).first())


if __name__ == "__main__":
    unittest.main()
