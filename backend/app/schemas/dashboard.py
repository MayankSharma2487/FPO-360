from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_organizations: int
    total_users: int
    active_users: int
    total_roles: int


class SuperAdminDashboard(BaseModel):
    total_organizations: int
    total_users: int
    active_users: int
    total_roles: int
    total_farmers: int
    total_villages: int
    total_shareholders: int
    total_procurement: int
    total_procurement_quantity: float
    total_procurement_value: float
    total_crops: int
    total_farmer_crops: int
    total_acreage: float
    expected_production: float
    actual_production: float


class FPOAdminDashboard(BaseModel):
    total_farmers: int
    active_villages: int
    total_shareholders: int
    total_procurement_quantity: float
    total_procurement_value: float
    sales_this_month: int
    license_alerts: int
    total_crops: int
    total_farmer_crops: int
    total_acreage: float


class ManagerDashboard(BaseModel):
    farmer_registrations: int
    village_coverage: int
    procurement_activities: int
    pending_tasks: int


class AccountantDashboard(BaseModel):
    revenue: float
    expenses: float
    outstanding_payments: float
    loans: float


class ViewerDashboard(BaseModel):
    last_updated: str