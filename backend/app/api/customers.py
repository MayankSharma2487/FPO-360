from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from app.services.customer_service import CustomerService
from app.auth.dependencies import require_roles
from app.models.user import User

router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin", "Manager")),
):
    service = CustomerService(db)
    return service.create_customer(payload, current_user)


@router.get("/", response_model=list[CustomerResponse])
def list_customers(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("Super Admin", "FPO Admin", "Manager", "Accountant", "Viewer")
    ),
):
    service = CustomerService(db)
    return service.list_customers(current_user)


@router.get("/active", response_model=list[CustomerResponse])
def list_active_customers(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("Super Admin", "FPO Admin", "Manager", "Accountant", "Viewer")
    ),
):
    service = CustomerService(db)
    return service.list_active_customers(current_user)


@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Super Admin", "FPO Admin", "Manager")),
):
    service = CustomerService(db)
    return service.update_customer(customer_id, payload, current_user)
