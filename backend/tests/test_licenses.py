import unittest
from datetime import date, timedelta
from types import SimpleNamespace

from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.licenses import create_license, delete_license, list_licenses, router, update_license
from app.models.license import License
from app.models.organization import Organization
from app.schemas.license import LicenseCreate, LicenseUpdate
from app.services.license_service import LicenseService


class LicenseModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import app.main  # register all existing ORM relationship targets
        cls.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        with cls.engine.begin() as connection:
            Organization.__table__.create(connection)
            License.__table__.create(connection)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def setUp(self):
        self.connection = self.engine.connect()
        self.transaction = self.connection.begin()
        self.session = Session(bind=self.connection, join_transaction_mode="create_savepoint")
        self.connection.execute(text("INSERT INTO organizations(id, organization_name, registration_number) VALUES (1, 'FPO One', 'REG-1'), (2, 'FPO Two', 'REG-2')"))
        self.service = LicenseService(self.session)

    def tearDown(self):
        self.session.close()
        self.transaction.rollback()
        self.connection.close()

    @staticmethod
    def user(role="FPO Admin", organization_id=1):
        return SimpleNamespace(id=50, organization_id=organization_id, role=SimpleNamespace(name=role))

    @staticmethod
    def payload(**overrides):
        values = {
            "license_type": "FSSAI",
            "license_number": "FSSAI-001",
            "issuing_authority": "Food Safety Department",
            "issue_date": date.today() - timedelta(days=100),
            "expiry_date": date.today() + timedelta(days=10),
            "status": "Active",
        }
        values.update(overrides)
        return LicenseCreate(**values)

    def test_create_read_update_and_deactivate(self):
        created = self.service.create_license(self.user(), self.payload())
        self.assertEqual(1, created.organization_id)
        self.assertEqual(50, created.created_by)
        self.assertEqual("FSSAI", created.license_type)
        self.assertTrue(created.expiring_soon)
        self.assertEqual("Active", created.status)
        self.assertEqual("Active", self.service.get_license(self.user(), created.id).display_status)

        updated = self.service.update_license(self.user(), created.id, LicenseUpdate(
            license_type="GST", license_number="GST-991", status="Pending", remarks="Awaiting renewal",
        ))
        self.assertEqual("GST", updated.license_type)
        self.assertEqual("Pending", updated.status)
        self.assertEqual("Pending", updated.display_status)
        self.assertEqual("Awaiting renewal", updated.remarks)

        deactivated = self.service.delete_license(self.user(), created.id)
        self.assertFalse(deactivated.is_active)
        self.assertTrue(self.service.set_active(self.user(), created.id, True).is_active)

    def test_super_admin_is_still_scoped_to_assigned_organization(self):
        first = self.service.create_license(self.user("Super Admin", 1), self.payload())
        second = self.service.create_license(self.user("FPO Admin", 2), self.payload(license_number="FSSAI-002"))
        self.assertEqual([first.id], [item.id for item in self.service.list_licenses(self.user("Super Admin", 1))])
        with self.assertRaises(HTTPException) as error:
            self.service.get_license(self.user("Super Admin", 1), second.id)
        self.assertEqual(404, error.exception.status_code)
        with self.assertRaises(HTTPException) as error:
            self.service.update_license(self.user("Super Admin", 1), second.id, LicenseUpdate(remarks="cross org"))
        self.assertEqual(404, error.exception.status_code)

    def test_create_and_update_date_validation(self):
        with self.assertRaises(ValueError):
            self.payload(issue_date=date.today(), expiry_date=date.today() - timedelta(days=1))
        with self.assertRaises(ValueError):
            self.payload(issue_date=date.today(), renewal_date=date.today() - timedelta(days=1))
        record = self.service.create_license(self.user(), self.payload())
        with self.assertRaises(HTTPException) as error:
            self.service.update_license(self.user(), record.id, LicenseUpdate(expiry_date=date.today() - timedelta(days=200)))
        self.assertEqual(422, error.exception.status_code)
        with self.assertRaises(ValueError):
            self.payload(license_type="   ")
        with self.assertRaises(ValueError):
            self.payload(issuing_authority="  ")

    def test_status_and_expiry_are_displayed_without_overwriting_stored_status(self):
        expired_record = self.service.create_license(self.user(), self.payload(
            license_type="GST", expiry_date=date.today() - timedelta(days=1), status="Active",
        ))
        pending_record = self.service.create_license(self.user(), self.payload(
            license_type="Pending permit", status="Pending", expiry_date=date.today() - timedelta(days=1),
        ))
        self.assertEqual("Expired", expired_record.display_status)
        self.assertEqual("Active", expired_record.status)
        self.assertEqual("Pending", pending_record.display_status)
        self.assertEqual("Pending", pending_record.status)
        self.assertTrue(expired_record.expiring_soon is False)

    def test_all_requested_status_display_cases(self):
        today = date.today()
        cases = [
            ("Pending", today + timedelta(days=10), "Pending", False),
            ("Not Applicable", today - timedelta(days=1), "Not Applicable", False),
            ("Active", today + timedelta(days=60), "Active", False),
            ("Active", today + timedelta(days=30), "Active", True),
            ("Active", today - timedelta(days=1), "Expired", False),
            ("Expired", today + timedelta(days=60), "Expired", False),
        ]
        for index, (stored, expiry, displayed, soon) in enumerate(cases):
            with self.subTest(status=stored, expiry=expiry):
                result = self.service.create_license(self.user(), self.payload(
                    license_type=f"Case {index}", status=stored, expiry_date=expiry,
                ))
                self.assertEqual(stored, result.status)
                self.assertEqual(displayed, result.display_status)
                self.assertEqual(soon, result.expiring_soon)

    def test_filters_by_type_status_expiry_range_and_expiring_soon(self):
        today = date.today()
        soon = self.service.create_license(self.user(), self.payload(license_type="FSSAI", expiry_date=today + timedelta(days=10)))
        self.service.create_license(self.user(), self.payload(license_type="GST", license_number="GST-1", expiry_date=today + timedelta(days=100)))
        self.service.create_license(self.user(), self.payload(license_type="Trade", license_number="TR-1", status="Pending", expiry_date=None))

        self.assertEqual([soon.id], [item.id for item in self.service.list_licenses(self.user(), status_filter="Expiring Soon")])
        active = self.service.list_licenses(self.user(), status_filter="Active")
        self.assertIn(soon.id, [item.id for item in active])
        self.assertEqual([soon.id], [item.id for item in self.service.list_licenses(self.user(), license_type="FSSAI")])
        self.assertEqual([soon.id], [item.id for item in self.service.list_licenses(self.user(), expiry_from=today, expiry_to=today + timedelta(days=30))])
        self.assertEqual([soon.id], [item.id for item in self.service.list_licenses(self.user(), expiring_soon=True)])
        with self.assertRaises(HTTPException):
            self.service.list_licenses(self.user(), expiry_from=today + timedelta(days=4), expiry_to=today)

    def test_api_rbac_allows_read_roles_and_rejects_viewer_writes(self):
        read_route = next(route for route in router.routes if route.endpoint is list_licenses)
        create_route = next(route for route in router.routes if route.endpoint is create_license)
        delete_route = next(route for route in router.routes if route.endpoint is delete_license)
        update_route = next(route for route in router.routes if route.endpoint is update_license)
        read_dependency = next(dependency for dependency in read_route.dependant.dependencies if dependency.name == "user")
        create_dependency = next(dependency for dependency in create_route.dependant.dependencies if dependency.name == "user")
        delete_dependency = next(dependency for dependency in delete_route.dependant.dependencies if dependency.name == "user")
        update_dependency = next(dependency for dependency in update_route.dependant.dependencies if dependency.name == "user")

        viewer = self.user("Viewer")
        self.assertIs(viewer, read_dependency.call(viewer))
        with self.assertRaises(HTTPException) as error:
            create_dependency.call(viewer)
        self.assertEqual(403, error.exception.status_code)
        with self.assertRaises(HTTPException) as error:
            delete_dependency.call(viewer)
        self.assertEqual(403, error.exception.status_code)
        with self.assertRaises(HTTPException) as error:
            update_dependency.call(viewer)
        self.assertEqual(403, error.exception.status_code)


if __name__ == "__main__":
    unittest.main()
