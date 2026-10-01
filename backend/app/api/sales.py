from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.sale import SaleCreate, SaleUpdate, SaleResponse
from app.services.sale_service import SaleService
from app.auth.dependencies import require_roles
from app.models.user import User

router = APIRouter(
    prefix="/sales",
    tags=["Sales"],
)


@router.post("/", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
def create_sale(
    payload: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin", "Manager")),
):
    service = SaleService(db)
    return service.create_sale(payload, current_user)


@router.get("/", response_model=list[SaleResponse])
def list_sales(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("Super Admin", "FPO Admin", "Manager", "Accountant", "Viewer")
    ),
):
    service = SaleService(db)
    return service.list_sales(current_user)


@router.get("/{sale_id}", response_model=SaleResponse)
def get_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("Super Admin", "FPO Admin", "Manager", "Accountant", "Viewer")
    ),
):
    service = SaleService(db)
    sale = service.get_sale(sale_id, current_user)
    # Enrich for response
    return {
        "id": sale.id,
        "sale_no": sale.sale_no,
        "sale_date": sale.sale_date,
        "customer_id": sale.customer_id,
        "crop_id": sale.crop_id,
        "organization_id": sale.organization_id,
        "quantity": sale.quantity,
        "unit": sale.unit,
        "rate_per_unit": sale.rate_per_unit,
        "total_amount": sale.total_amount,
        "payment_status": sale.payment_status,
        "remarks": sale.remarks,
        "is_active": sale.is_active,
        "created_at": sale.created_at,
        "updated_at": sale.updated_at,
        "customer_name": sale.customer.customer_name if sale.customer else "—",
        "crop_name": sale.crop.crop_name if sale.crop else "—",
    }


@router.put("/{sale_id}", response_model=SaleResponse)
def update_sale(
    sale_id: int,
    payload: SaleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin", "Manager")),
):
    service = SaleService(db)
    return service.update_sale(sale_id, payload, current_user)


@router.patch("/{sale_id}/status", response_model=SaleResponse)
def toggle_sale_status(
    sale_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin", "Manager")),
):
    service = SaleService(db)
    return service.toggle_sale_status(sale_id, is_active, current_user)
