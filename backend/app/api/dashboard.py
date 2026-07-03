from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.auth.dependencies import require_roles
from app.models.user import User

from app.schemas.dashboard import (
    DashboardSummary,
    SuperAdminDashboard,
    FPOAdminDashboard,
    ManagerDashboard,
    AccountantDashboard,
    ViewerDashboard
)

from app.services.dashboard_service import DashboardService

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get(
    "/summary",
    response_model=DashboardSummary
)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "Super Admin",
            "FPO Admin"
        )
    )
):
    service = DashboardService(db)

    return service.get_summary()


@router.get(
    "/super-admin",
    response_model=SuperAdminDashboard
)
def get_super_admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("Super Admin")
    )
):
    service = DashboardService(db)

    return service.get_super_admin_dashboard()


@router.get(
    "/fpo-admin",
    response_model=FPOAdminDashboard
)
def get_fpo_admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("FPO Admin")
    )
):
    service = DashboardService(db)

    return service.get_fpo_admin_dashboard(
        current_user.organization_id
    )


@router.get(
    "/manager",
    response_model=ManagerDashboard
)
def get_manager_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("Manager")
    )
):
    service = DashboardService(db)

    return service.get_manager_dashboard(
        current_user.organization_id
    )


@router.get(
    "/accountant",
    response_model=AccountantDashboard
)
def get_accountant_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("Accountant")
    )
):
    service = DashboardService(db)

    return service.get_accountant_dashboard(
        current_user.organization_id
    )


@router.get(
    "/viewer",
    response_model=ViewerDashboard
)
def get_viewer_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("Viewer")
    )
):
    service = DashboardService(db)

    return service.get_viewer_dashboard()