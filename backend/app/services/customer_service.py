from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.customer_repository import CustomerRepository
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate


class CustomerService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CustomerRepository(db)

    def _generate_customer_code(self) -> str:
        latest = (
            self.db.query(Customer)
            .order_by(Customer.id.desc())
            .first()
        )

        if not latest or not latest.customer_code.startswith("CUS-"):
            return "CUS-00001"

        try:
            num = int(latest.customer_code.split("-")[1])
            return f"CUS-{num + 1:05d}"
        except Exception:
            return "CUS-00001"

    def create_customer(self, payload: CustomerCreate, current_user) -> Customer:
        if current_user.role.name not in ["Super Admin", "FPO Admin", "Manager"]:
            raise HTTPException(403, "Not authorized")

        org_id = payload.organization_id or current_user.organization_id
        if current_user.role.name != "Super Admin" and org_id != current_user.organization_id:
            raise HTTPException(403, "Cannot create customer for another organization")

        if not payload.customer_name or not payload.customer_name.strip():
            raise HTTPException(400, "Customer name is required")

        customer = Customer(
            customer_code=self._generate_customer_code(),
            customer_name=payload.customer_name.strip(),
            mobile_number=payload.mobile_number,
            email=payload.email,
            address=payload.address,
            organization_id=org_id,
            is_active=True,
        )
        return self.repo.create(customer)

    def list_customers(self, current_user):
        if current_user.role.name == "Super Admin":
            return self.repo.list_all()
        return self.repo.list_all(current_user.organization_id)

    def list_active_customers(self, current_user):
        """
        Always returns ONLY active customers.
        Super Admin: active customers across all organizations.
        Other roles: active customers of their own organization.
        """
        if current_user.role.name == "Super Admin":
            return self.repo.list_active(organization_id=None)
        return self.repo.list_active(organization_id=current_user.organization_id)

    def update_customer(self, customer_id: int, payload: CustomerUpdate, current_user) -> Customer:
        if current_user.role.name not in ["Super Admin", "FPO Admin", "Manager"]:
            raise HTTPException(403, "Not authorized")

        customer = self.repo.get_by_id(customer_id)
        if not customer:
            raise HTTPException(404, "Customer not found")

        if current_user.role.name != "Super Admin" and customer.organization_id != current_user.organization_id:
            raise HTTPException(403, "Not authorized")

        if payload.customer_name is not None:
            customer.customer_name = payload.customer_name.strip()
        if payload.mobile_number is not None:
            customer.mobile_number = payload.mobile_number
        if payload.email is not None:
            customer.email = payload.email
        if payload.address is not None:
            customer.address = payload.address
        if payload.is_active is not None:
            customer.is_active = payload.is_active

        return self.repo.update(customer)
