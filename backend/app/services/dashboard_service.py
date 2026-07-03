from sqlalchemy.orm import Session
from datetime import datetime

from app.repositories.user_repository import UserRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.village_repository import VillageRepository
from app.repositories.farmer_repository import FarmerRepository
from app.repositories.shareholder_repository import ShareholderRepository
from app.repositories.crop_master_repository import CropMasterRepository
from app.repositories.farmer_crop_repository import FarmerCropRepository
from app.repositories.procurement_repository import ProcurementRepository

from app.schemas.dashboard import (
    DashboardSummary,
    SuperAdminDashboard,
    FPOAdminDashboard,
    ManagerDashboard,
    AccountantDashboard,
    ViewerDashboard
)


class DashboardService:

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.organization_repo = OrganizationRepository(db)
        self.role_repo = RoleRepository(db)
        self.village_repo = VillageRepository(db)
        self.farmer_repo = FarmerRepository(db)
        self.shareholder_repo = ShareholderRepository(db)
        self.crop_repo = CropMasterRepository(db)
        self.farmer_crop_repo = FarmerCropRepository(db)
        self.procurement_repo = ProcurementRepository(db)
        

    def get_summary(self) -> DashboardSummary:
        return DashboardSummary(
            total_organizations=self.organization_repo.count_all(),
            total_users=self.user_repo.count_all(),
            active_users=self.user_repo.count_active(),
            total_roles=self.role_repo.count_all()
        )

    def get_super_admin_dashboard(self) -> SuperAdminDashboard:
        return SuperAdminDashboard(
            total_organizations=self.organization_repo.count_all(),
            total_users=self.user_repo.count_all(),
            active_users=self.user_repo.count_active(),
            total_roles=self.role_repo.count_all(),
            total_farmers=self.farmer_repo.count_all(),
            total_villages=self.village_repo.count_all(),
            total_shareholders=self.shareholder_repo.count_all(),
            total_procurement=self.procurement_repo.count_all(),
            total_procurement_quantity=self.procurement_repo.total_quantity(),
            total_procurement_value=self.procurement_repo.total_value(),
            total_crops=self.crop_repo.count_all(),
            total_farmer_crops=self.farmer_crop_repo.count_all(),
            total_acreage=self.farmer_crop_repo.total_acreage() or 0.0,
            expected_production=self.farmer_crop_repo.total_expected_yield() or 0.0,
            actual_production=self.farmer_crop_repo.total_actual_yield() or 0.0,
        )

    def get_fpo_admin_dashboard(self, organization_id: int) -> FPOAdminDashboard:
        return FPOAdminDashboard(
            total_farmers=self.farmer_repo.count_by_organization(organization_id),
            active_villages=self.village_repo.count_active_by_organization(organization_id),
            total_shareholders=self.shareholder_repo.count_by_organization(organization_id),
            total_procurement_quantity=self.procurement_repo.total_quantity_by_org(organization_id),
            total_procurement_value=self.procurement_repo.total_value_by_org(organization_id),
            sales_this_month=0,
            license_alerts=0,
            total_crops=self.crop_repo.count_all(),
            total_farmer_crops=self.farmer_crop_repo.count_by_organization(organization_id),
            total_acreage=self.farmer_crop_repo.total_acreage_by_org(organization_id) or 0.0,
        )

    def get_manager_dashboard(self, organization_id: int) -> ManagerDashboard:
        return ManagerDashboard(
            farmer_registrations=self.farmer_repo.count_by_organization(organization_id),
            village_coverage=self.village_repo.count_by_organization(organization_id),
            procurement_activities=0,
            pending_tasks=0
        )

    def get_accountant_dashboard(self, organization_id: int) -> AccountantDashboard:
        return AccountantDashboard(
            revenue=0.0,
            expenses=0.0,
            outstanding_payments=0.0,
            loans=0.0
        )

    def get_viewer_dashboard(self) -> ViewerDashboard:
        return ViewerDashboard(
            last_updated=datetime.now().isoformat()
        )