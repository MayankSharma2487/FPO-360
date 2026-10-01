from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal

from app.repositories.sale_repository import SaleRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.crop_master_repository import CropMasterRepository
from app.repositories.inventory_repository import InventoryRepository
from app.models.sale import Sale
from app.models.inventory import InventoryLedger
from app.schemas.sale import SaleCreate, SaleUpdate


class SaleService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SaleRepository(db)
        self.customer_repo = CustomerRepository(db)
        self.crop_repo = CropMasterRepository(db)
        self.inventory_repo = InventoryRepository(db)

    def _generate_sale_no(self, organization_id: int) -> str:
        year = datetime.now().year
        latest = self.repo.get_latest_by_org(organization_id)
        if not latest or not latest.sale_no.startswith(f"SA-{year}"):
            return f"SA-{year}-00001"
        try:
            num = int(latest.sale_no.split("-")[2])
            return f"SA-{year}-{num + 1:05d}"
        except Exception:
            return f"SA-{year}-00001"

    def _convert_to_kg(self, quantity: float, unit: str) -> float:
        qty = float(quantity)
        if unit == "QUINTAL":
            return qty * 100
        elif unit == "TON":
            return qty * 1000
        return qty  # KG

    def _calculate_total_amount(self, user_entered_quantity: float, rate_per_unit: Decimal) -> Decimal:
        return Decimal(str(user_entered_quantity)) * rate_per_unit

    def create_sale(self, payload: SaleCreate, current_user) -> Sale:
        if current_user.role.name not in ["Super Admin", "FPO Admin", "Manager"]:
            raise HTTPException(403, "Not authorized")

        org_id = payload.organization_id or current_user.organization_id
        if current_user.role.name != "Super Admin" and org_id != current_user.organization_id:
            raise HTTPException(403, "Cannot create sale for another organization")

        # Validate customer
        customer = self.customer_repo.get_by_id(payload.customer_id)
        if not customer or customer.organization_id != org_id or not customer.is_active:
            raise HTTPException(400, "Invalid or inactive customer")

        # Validate crop
        crop = self.crop_repo.get_by_id(payload.crop_id)
        if not crop or not crop.is_active:
            raise HTTPException(400, "Invalid or inactive crop")

        if payload.quantity <= 0 or payload.rate_per_unit <= 0:
            raise HTTPException(400, "Quantity and rate must be positive")

        if payload.unit not in ("KG", "QUINTAL", "TON"):
            raise HTTPException(400, "Unit must be KG, QUINTAL or TON")

        if payload.payment_status not in ("Pending", "Paid"):
            raise HTTPException(400, "Payment status must be Pending or Paid")

        quantity_in_kg = self._convert_to_kg(payload.quantity, payload.unit)
        total_amount = self._calculate_total_amount(payload.quantity, payload.rate_per_unit)

        # Stock check (source of truth)
        available = self.inventory_repo.get_balance_for_crop(org_id, payload.crop_id)
        if quantity_in_kg > available:
            raise HTTPException(
                400,
                f"Insufficient stock. Available: {available} KG, requested OUT: {quantity_in_kg} KG",
            )

        sale = Sale(
            sale_no=self._generate_sale_no(org_id),
            sale_date=payload.sale_date,
            customer_id=payload.customer_id,
            crop_id=payload.crop_id,
            organization_id=org_id,
            quantity=quantity_in_kg,
            unit=payload.unit,
            rate_per_unit=payload.rate_per_unit,
            total_amount=total_amount,
            payment_status=payload.payment_status,
            remarks=payload.remarks,
            is_active=True,
        )

        try:
            self.repo.create(sale, commit=False)

            ledger = InventoryLedger(
                organization_id=sale.organization_id,
                crop_id=sale.crop_id,
                transaction_type="OUT",
                quantity=float(sale.quantity),
                reference_type="SALE",
                reference_id=sale.id,
                remarks=f"Sale {sale.sale_no}",
                is_active=True,
            )
            self.inventory_repo.add(ledger)

            self.db.commit()
            self.db.refresh(sale)
            return sale
        except Exception:
            self.db.rollback()
            raise

    def update_sale(self, sale_id: int, payload: SaleUpdate, current_user) -> Sale:
        if current_user.role.name not in ["Super Admin", "FPO Admin", "Manager"]:
            raise HTTPException(403, "Not authorized")

        sale = self.repo.get_by_id(sale_id)
        if not sale:
            raise HTTPException(404, "Sale not found")

        if current_user.role.name != "Super Admin" and sale.organization_id != current_user.organization_id:
            raise HTTPException(403, "Not authorized to update this sale")

        # Require quantity when unit changes (prevents inconsistent KG/unit pairs).
        # Stored quantity is always in KG. Silently treating that KG value as a
        # user-entered quantity in a new unit (e.g. 100 KG → unit=QUINTAL)
        # would be incorrect. Match the safe rule: unit change needs a new quantity.
        if payload.unit is not None and payload.quantity is None:
            if payload.unit != sale.unit:
                raise HTTPException(
                    400,
                    "Quantity is required when changing unit. "
                    "Provide the quantity in the new unit so it can be converted to KG correctly.",
                )

        new_customer_id = payload.customer_id if payload.customer_id is not None else sale.customer_id
        new_crop_id = payload.crop_id if payload.crop_id is not None else sale.crop_id
        new_unit = payload.unit if payload.unit is not None else sale.unit
        new_rate = payload.rate_per_unit if payload.rate_per_unit is not None else sale.rate_per_unit

        if payload.customer_id is not None:
            customer = self.customer_repo.get_by_id(new_customer_id)
            if not customer or customer.organization_id != sale.organization_id or not customer.is_active:
                raise HTTPException(400, "Invalid or inactive customer")

        if payload.crop_id is not None:
            crop = self.crop_repo.get_by_id(new_crop_id)
            if not crop or not crop.is_active:
                raise HTTPException(400, "Invalid or inactive crop")

        if payload.unit is not None and payload.unit not in ("KG", "QUINTAL", "TON"):
            raise HTTPException(400, "Unit must be KG, QUINTAL or TON")

        stock_affecting = (
            payload.quantity is not None
            or payload.unit is not None
            or payload.crop_id is not None
        )

        if stock_affecting and sale.is_active:
            if payload.quantity is not None:
                quantity_in_kg = self._convert_to_kg(payload.quantity, new_unit)
            else:
                # Unit unchanged or crop-only change: keep existing physical KG quantity
                quantity_in_kg = float(sale.quantity)

            current_ledger = self.inventory_repo.get_by_reference(
                sale.organization_id, "SALE", sale.id
            )
            available = self.inventory_repo.get_balance_for_crop(sale.organization_id, new_crop_id)
            if current_ledger and current_ledger.is_active and current_ledger.crop_id == new_crop_id:
                available += float(current_ledger.quantity)

            if quantity_in_kg > available:
                raise HTTPException(
                    400,
                    f"Insufficient stock. Available: {available} KG, requested OUT: {quantity_in_kg} KG",
                )

            if payload.quantity is not None:
                sale.quantity = quantity_in_kg
            if payload.unit is not None:
                sale.unit = payload.unit
            if payload.crop_id is not None:
                sale.crop_id = new_crop_id

            if current_ledger:
                current_ledger.crop_id = sale.crop_id
                current_ledger.quantity = float(sale.quantity)
                current_ledger.remarks = f"Sale {sale.sale_no}"
            else:
                ledger = InventoryLedger(
                    organization_id=sale.organization_id,
                    crop_id=sale.crop_id,
                    transaction_type="OUT",
                    quantity=float(sale.quantity),
                    reference_type="SALE",
                    reference_id=sale.id,
                    remarks=f"Sale {sale.sale_no}",
                    is_active=sale.is_active,
                )
                self.inventory_repo.add(ledger)

        if payload.sale_date is not None:
            sale.sale_date = payload.sale_date
        if payload.customer_id is not None:
            sale.customer_id = new_customer_id
        if payload.rate_per_unit is not None:
            sale.rate_per_unit = new_rate
        if payload.payment_status is not None:
            if payload.payment_status not in ("Pending", "Paid"):
                raise HTTPException(400, "Payment status must be Pending or Paid")
            sale.payment_status = payload.payment_status
        if payload.remarks is not None:
            sale.remarks = payload.remarks

        # Recalculate total amount whenever quantity or rate changes.
        if payload.quantity is not None:
            sale.total_amount = self._calculate_total_amount(payload.quantity, new_rate)
        elif payload.rate_per_unit is not None:
            stored_quantity_kg = float(sale.quantity)

            if sale.unit == "QUINTAL":
                display_quantity = stored_quantity_kg / 100
            elif sale.unit == "TON":
                display_quantity = stored_quantity_kg / 1000
            else:
                display_quantity = stored_quantity_kg

            sale.total_amount = self._calculate_total_amount(
                display_quantity,
                new_rate,
            )

        if payload.is_active is not None and payload.is_active != sale.is_active:
            return self.toggle_sale_status(sale_id, payload.is_active, current_user)

        try:
            self.repo.update(sale, commit=True)
            return sale
        except Exception:
            self.db.rollback()
            raise

    def toggle_sale_status(self, sale_id: int, is_active: bool, current_user) -> Sale:
        if current_user.role.name not in ["Super Admin", "FPO Admin", "Manager"]:
            raise HTTPException(403, "Not authorized")

        sale = self.repo.get_by_id(sale_id)
        if not sale:
            raise HTTPException(404, "Sale not found")

        if current_user.role.name != "Super Admin" and sale.organization_id != current_user.organization_id:
            raise HTTPException(403, "Not authorized")

        if is_active and not sale.is_active:
            # Reactivation: check stock again
            available = self.inventory_repo.get_balance_for_crop(sale.organization_id, sale.crop_id)
            if sale.quantity > available:
                raise HTTPException(
                    400,
                    f"Insufficient stock to reactivate. Available: {available} KG, required: {sale.quantity} KG",
                )

        sale.is_active = is_active

        ledger = self.inventory_repo.get_by_reference(
            sale.organization_id, "SALE", sale.id
        )
        if ledger:
            ledger.is_active = is_active
        elif is_active:
            # recreate missing ledger on reactivate
            ledger = InventoryLedger(
                organization_id=sale.organization_id,
                crop_id=sale.crop_id,
                transaction_type="OUT",
                quantity=float(sale.quantity),
                reference_type="SALE",
                reference_id=sale.id,
                remarks=f"Sale {sale.sale_no}",
                is_active=True,
            )
            self.inventory_repo.add(ledger)

        try:
            self.db.commit()
            self.db.refresh(sale)
            return sale
        except Exception:
            self.db.rollback()
            raise

    def list_sales(self, current_user):
        if current_user.role.name == "Super Admin":
            sales = self.repo.list_all()
        else:
            sales = self.repo.list_all(current_user.organization_id)

        result = []
        for s in sales:
            result.append({
                "id": s.id,
                "sale_no": s.sale_no,
                "sale_date": s.sale_date,
                "customer_id": s.customer_id,
                "crop_id": s.crop_id,
                "organization_id": s.organization_id,
                "quantity": s.quantity,
                "unit": s.unit,
                "rate_per_unit": s.rate_per_unit,
                "total_amount": s.total_amount,
                "payment_status": s.payment_status,
                "remarks": s.remarks,
                "is_active": s.is_active,
                "created_at": s.created_at,
                "updated_at": s.updated_at,
                "customer_name": s.customer.customer_name if s.customer else "—",
                "crop_name": s.crop.crop_name if s.crop else "—",
            })
        return result

    def get_sale(self, sale_id: int, current_user) -> Sale:
        sale = self.repo.get_by_id(sale_id)
        if not sale:
            raise HTTPException(404, "Sale not found")
        if current_user.role.name != "Super Admin" and sale.organization_id != current_user.organization_id:
            raise HTTPException(403, "Not authorized to view this sale")
        return sale