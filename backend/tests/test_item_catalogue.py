import unittest
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database.database import Base
from app.domain.item_catalogue import BaseUnit, ItemType
from app.models.crop_master import CropMaster
from app.models.farmer import Farmer
from app.models.customer import Customer
from app.models.inventory import InventoryBalance, InventoryLedger
from app.models.organization import Organization
from app.schemas.farmer_crop import FarmerCropCreate
from app.schemas.item import ItemCreate, ItemUpdate
from app.schemas.crop_master import CropMasterCreate, CropMasterUpdate
from app.schemas.inventory import InventoryAdjustRequest
from app.schemas.procurement import ProcurementCreate
from app.schemas.sale import SaleCreate
from app.services.farmer_crop_service import FarmerCropService
from app.services.inventory_service import InventoryService
from app.services.item_service import ItemService
from app.services.crop_master_service import CropMasterService
from app.services.procurement_service import ProcurementService
from app.services.sale_service import SaleService


class ItemCatalogueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import app.main  # noqa: F401, register ORM tables and relationships
        cls.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(cls.engine)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def setUp(self):
        self.connection = self.engine.connect()
        self.db = Session(bind=self.connection)
        for table in reversed(Base.metadata.sorted_tables):
            self.db.execute(table.delete())
        self.db.execute(text("INSERT INTO organizations(id, organization_name, registration_number) VALUES (1,'First','R1'),(2,'Other','R2')"))
        self.db.add_all([
            Farmer(id=1, organization_id=1, farmer_code="F1", farmer_name="Farmer One", mobile_number="9000000001", is_active=True),
            Customer(id=1, organization_id=1, customer_code="CU1", customer_name="Buyer One", is_active=True),
            CropMaster(id=1, crop_code="CROP-1", crop_name="Tea leaves", crop_category="Tea", item_type=ItemType.AGRICULTURAL_COMMODITY.value, organization_id=None, base_unit=BaseUnit.KG.value, unit="Kg", is_active=True),
            CropMaster(id=2, crop_code="PRIVATE-2", crop_name="Other FPO fertilizer", item_type=ItemType.PURCHASED_PRODUCT.value, organization_id=2, base_unit=BaseUnit.PCS.value, unit="Kg", is_active=True),
        ])
        self.db.flush()
        self.db.commit()
        self.service = ItemService(self.db)
        self.admin = SimpleNamespace(organization_id=1, role=SimpleNamespace(name="FPO Admin"))
        self.reader = SimpleNamespace(organization_id=1, role=SimpleNamespace(name="Manager"))
        self.super_admin = SimpleNamespace(organization_id=1, role=SimpleNamespace(name="Super Admin"))

    def tearDown(self):
        self.db.close()
        self.connection.close()

    def create(self, code="BAG-1", name="Biofertilizer", kind=ItemType.FINISHED_GOOD, unit=BaseUnit.L):
        return self.service.create_item(ItemCreate(item_code=code, item_name=name, item_type=kind, category="Farm inputs", base_unit=unit), self.admin)

    def test_all_item_types_and_units_are_canonical(self):
        self.assertEqual(5, len(ItemType))
        self.assertEqual({"KG", "G", "QUINTAL", "TON", "L", "ML", "PCS"}, {unit.value for unit in BaseUnit})
        for idx, kind in enumerate(ItemType):
            unit = BaseUnit.KG if kind == ItemType.AGRICULTURAL_COMMODITY else BaseUnit.PCS
            item = self.create(f"TYPE-{idx}", f"Item {idx}", kind, unit)
            self.assertEqual(kind.value, item["item_type"])
            self.assertEqual(unit.value, item["base_unit"])
            prefix = {ItemType.AGRICULTURAL_COMMODITY: "AGR", ItemType.PURCHASED_PRODUCT: "PUR", ItemType.RAW_MATERIAL: "RAW", ItemType.PACKAGING_MATERIAL: "PKG", ItemType.FINISHED_GOOD: "FG"}[kind]
            self.assertRegex(item["item_code"], rf"^{prefix}-\d{{5,}}$")
            self.assertNotEqual(f"TYPE-{idx}", item["item_code"])

    def test_create_list_search_type_and_status_filters(self):
        finished = self.create()
        self.create("RAW-1", "Tea bag", ItemType.PACKAGING_MATERIAL, BaseUnit.PCS)
        self.assertEqual(["Tea bag"], [x["item_name"] for x in self.service.list_items(self.admin, search="Tea b")])
        self.assertEqual(1, len(self.service.list_items(self.admin, item_type=ItemType.FINISHED_GOOD.value)))
        self.service.set_active(finished["id"], False, self.admin)
        self.assertEqual(1, len(self.service.list_items(self.admin, is_active=False)))

    def test_update_and_activation_lifecycle(self):
        item = self.create()
        changed = self.service.update_item(item["id"], ItemUpdate(item_name="Biofertilizer liquid", description="Concentrate", item_code="EDITED"), self.admin)
        self.assertEqual("Biofertilizer liquid", changed["item_name"])
        self.assertEqual("Concentrate", changed["description"])
        self.assertEqual(item["item_code"], changed["item_code"])
        with self.assertRaises(HTTPException):
            self.service.update_item(item["id"], ItemUpdate(item_type=ItemType.RAW_MATERIAL), self.admin)
        self.assertFalse(self.service.set_active(item["id"], False, self.admin)["is_active"])
        self.assertTrue(self.service.set_active(item["id"], True, self.admin)["is_active"])

    def test_base_unit_can_change_only_before_any_stock_state_exists(self):
        empty = self.create("RAW-EMPTY", "Empty material", ItemType.RAW_MATERIAL, BaseUnit.KG)
        changed = self.service.update_item(empty["id"], ItemUpdate(base_unit=BaseUnit.G), self.admin)
        self.assertEqual("G", changed["base_unit"])
        metadata = self.service.update_item(
            empty["id"], ItemUpdate(item_name="Renamed material"), self.admin
        )
        self.assertEqual("G", metadata["base_unit"])

        movement_item = self.create("RAW-MOVE", "Moved material", ItemType.RAW_MATERIAL, BaseUnit.KG)
        self.db.add(InventoryLedger(
            organization_id=1, item_id=movement_item["id"], transaction_type="IN",
            quantity=Decimal("1"), reference_type="MANUAL", reference_id=None,
            idempotency_key="legacy-movement-unit-guard", is_active=True,
        ))
        self.db.commit()
        with self.assertRaises(HTTPException) as movement_error:
            self.service.update_item(movement_item["id"], ItemUpdate(base_unit=BaseUnit.G), self.admin)
        self.assertEqual(409, movement_error.exception.status_code)
        self.assertEqual("KG", self.service.get_item(movement_item["id"], self.admin)["base_unit"])

        balance_item = self.create("RAW-BAL", "Balanced material", ItemType.RAW_MATERIAL, BaseUnit.KG)
        self.db.add(InventoryBalance(organization_id=1, item_id=balance_item["id"], quantity=0))
        self.db.commit()
        with self.assertRaises(HTTPException) as balance_error:
            self.service.update_item(balance_item["id"], ItemUpdate(base_unit=BaseUnit.G), self.admin)
        self.assertEqual(409, balance_error.exception.status_code)
        self.assertEqual("KG", self.service.get_item(balance_item["id"], self.admin)["base_unit"])

    def test_shared_crop_visible_private_item_isolated(self):
        listed = self.service.list_items(self.admin)
        self.assertEqual({1}, {item["id"] for item in listed})
        self.assertIn(1, {item["id"] for item in self.service.list_items(self.super_admin)})
        self.assertIn(2, {item["id"] for item in self.service.list_items(self.super_admin)})
        with self.assertRaises(HTTPException) as error:
            self.service.get_item(2, self.admin)
        self.assertEqual(404, error.exception.status_code)
        with self.assertRaises(HTTPException):
            self.service.update_item(2, ItemUpdate(item_name="Hijack"), self.admin)
        with self.assertRaises(HTTPException):
            self.service.set_active(2, False, self.admin)

    def test_commercial_items_are_owned_and_manager_is_read_only(self):
        item = self.create()
        self.assertEqual(1, item["organization_id"])
        with self.assertRaises(HTTPException) as error:
            self.service.create_item(ItemCreate(item_code="NO", item_name="No", item_type=ItemType.RAW_MATERIAL, base_unit=BaseUnit.KG), self.reader)
        self.assertEqual(403, error.exception.status_code)

    def test_bad_type_code_unit_and_crop_base_unit_rejected(self):
        for data in (
            dict(item_code="BAD", item_name="Bad", item_type="MADE_UP", base_unit="PCS"),
            dict(item_code="BAD", item_name=" ", item_type="RAW_MATERIAL", base_unit="KG"),
            dict(item_code="BAD", item_name="Bad", item_type="RAW_MATERIAL", base_unit="GALLON"),
        ):
            with self.assertRaises(ValidationError):
                ItemCreate(**data)
        with self.assertRaises(HTTPException):
            self.create("CROP-NEW", "Barley", ItemType.AGRICULTURAL_COMMODITY, BaseUnit.QUINTAL)
        with self.assertRaises(ValidationError):
            ItemUpdate(item_name=" ")
        with self.assertRaises(ValidationError):
            ItemUpdate(item_type=None)

    def test_generated_codes_are_unique_and_inactive_codes_are_not_reused(self):
        first = self.create("CLIENT-CODE", "First")
        second = self.create("CLIENT-CODE", "Second")
        self.assertNotEqual(first["item_code"], second["item_code"])
        self.assertFalse(self.service.set_active(first["id"], False, self.admin)["is_active"])
        third = self.create("CLIENT-CODE", "Third")
        self.assertNotEqual(first["item_code"], third["item_code"])
        self.assertEqual(3, self.db.query(CropMaster).filter(CropMaster.item_type == ItemType.FINISHED_GOOD.value).count())

    def test_generated_codes_are_global_across_organizations(self):
        first = self.create("SAME-CLIENT-CODE", "FPO One Product", ItemType.PURCHASED_PRODUCT, BaseUnit.PCS)
        other_user = SimpleNamespace(organization_id=2, role=SimpleNamespace(name="FPO Admin"))
        second = self.service.create_item(ItemCreate(
            item_code="SAME-CLIENT-CODE", item_name="FPO Two Product",
            item_type=ItemType.PURCHASED_PRODUCT, base_unit=BaseUnit.PCS,
        ), other_user)
        self.assertNotEqual(first["item_code"], second["item_code"])
        self.assertEqual((1, 2), (first["organization_id"], second["organization_id"]))

    def test_code_preview_and_legacy_crop_api_use_server_generated_code(self):
        preview = self.service.get_next_code(ItemType.AGRICULTURAL_COMMODITY, self.admin)["item_code"]
        crop = CropMasterService(self.db).create_crop_master(
            CropMasterCreate(crop_code="CLIENT-SUPPLIED", crop_name="Millet"), self.admin
        )
        self.assertEqual(preview, crop.crop_code)
        self.assertNotEqual("CLIENT-SUPPLIED", crop.crop_code)
        updated = CropMasterService(self.db).update_crop_master(
            crop.id, CropMasterUpdate(crop_code="LEGACY-EDIT"), self.admin
        )
        self.assertEqual(crop.crop_code, updated.crop_code)

    def test_farmer_crop_accepts_only_active_shared_commodities(self):
        service = FarmerCropService(self.db)
        payload = FarmerCropCreate(farmer_id=1, crop_id=1, year=2026)
        row = service.create_farmer_crop(payload, self.admin)
        self.assertEqual(1, row.crop_id)
        private = self.create("RAW-ORG", "Packaging", ItemType.PACKAGING_MATERIAL, BaseUnit.PCS)
        with self.assertRaises(HTTPException):
            service.create_farmer_crop(FarmerCropCreate(farmer_id=1, crop_id=private["id"], year=2026), self.admin)
        self.service.set_active(1, False, self.admin)
        with self.assertRaises(HTTPException):
            service.create_farmer_crop(FarmerCropCreate(farmer_id=1, crop_id=1, year=2026), self.admin)

    def test_crop_transaction_entry_points_reject_non_crop_items(self):
        item = self.create("PACK-1", "Pouch", ItemType.PACKAGING_MATERIAL, BaseUnit.PCS)
        with self.assertRaises(HTTPException):
            ProcurementService(self.db).create_procurement(ProcurementCreate(
                procurement_date=datetime(2026, 1, 1), farmer_id=1, crop_id=item["id"],
                quantity=1, rate_per_unit=1,
            ), self.admin)
        inventory_movement = InventoryService(self.db).adjust_stock(InventoryAdjustRequest(
            item_id=item["id"], transaction_type="IN", quantity=1, unit=BaseUnit.PCS,
        ), self.admin, "test-item-catalogue-generic-stock")
        self.assertEqual(item["id"], inventory_movement["item_id"])
        with self.assertRaises(HTTPException):
            SaleService(self.db).create_sale(SaleCreate(
                sale_date=datetime(2026, 1, 1), customer_id=1, crop_id=item["id"],
                quantity=1, rate_per_unit=1,
            ), self.admin)

    def test_legacy_crop_procurement_inventory_and_sale_remain_compatible(self):
        now = datetime(2026, 1, 1)
        procurement = ProcurementService(self.db).create_procurement(ProcurementCreate(
            procurement_date=now, farmer_id=1, crop_id=1, quantity=10,
            rate_per_unit=2,
        ), self.admin)
        inventory = InventoryService(self.db)
        self.assertEqual(10, inventory.repo.get_balance_for_crop(1, 1))
        sale = SaleService(self.db).create_sale(SaleCreate(
            sale_date=now, customer_id=1, crop_id=1, quantity=4,
            rate_per_unit=3,
        ), self.admin)
        self.assertEqual(10, procurement.quantity)
        self.assertEqual(4, sale.quantity)
        self.assertEqual(6, inventory.repo.get_balance_for_crop(1, 1))

    def test_migration_revisions_and_model_constraints_match_catalogue(self):
        self.assertIn("ck_crop_masters_item_type", {c["name"] for c in inspect(self.engine).get_check_constraints("crop_masters")})
        self.assertIn("ck_crop_masters_base_unit", {c["name"] for c in inspect(self.engine).get_check_constraints("crop_masters")})
        columns = {c["name"] for c in inspect(self.engine).get_columns("crop_masters")}
        self.assertTrue({"item_type", "organization_id", "base_unit", "description"}.issubset(columns))
        from importlib.util import spec_from_file_location, module_from_spec
        path = "migrations/versions/0014_evolve_crop_masters_to_item_catalogue.py"
        spec = spec_from_file_location("item_catalogue_migration", path)
        module = module_from_spec(spec); spec.loader.exec_module(module)
        self.assertEqual("0014", module.revision)
        self.assertEqual("0013", module.down_revision)


if __name__ == "__main__":
    unittest.main()
