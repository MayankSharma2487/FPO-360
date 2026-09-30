from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, date
from decimal import Decimal

from app.repositories.procurement_repository import ProcurementRepository
from app.repositories.farmer_repository import FarmerRepository
from app.repositories.crop_master_repository import CropMasterRepository
from app.models.procurement import Procurement
from app.schemas.procurement import ProcurementCreate, ProcurementUpdate
from app.repositories.inventory_repository import InventoryRepository
from app.models.inventory import InventoryLedger


class ProcurementService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ProcurementRepository(db)
        self.farmer_repo = FarmerRepository(db)
        self.crop_repo = CropMasterRepository(db)
        self.inventory_repo = InventoryRepository(db)

    def _generate_procurement_no(self, organization_id: int) -> str:
        """Generate unique procurement number in format PR-YYYY-00001"""
        year = datetime.now().year
        latest = self.repo.get_latest_by_org(organization_id)
        if not latest or not latest.procurement_no.startswith(f"PR-{year}"):
            return f"PR-{year}-00001"
        
        last_no = latest.procurement_no
        try:
            num = int(last_no.split('-')[2])
            return f"PR-{year}-{num + 1:05d}"
        except:
            return f"PR-{year}-00001"

    def _convert_to_kg(self, quantity: float, unit: str) -> float:
        """
        Convert user-entered quantity to KG for storage.
        
        Conversions:
        - KG: no conversion
        - QUINTAL: 1 QT = 100 KG
        - TON: 1 MT = 1000 KG
        """
        qty = float(quantity)
        
        if unit == "QUINTAL":
            return qty * 100
        elif unit == "TON":
            return qty * 1000
        else:  # KG
            return qty

    def _calculate_total_amount(self, user_entered_quantity: float, rate_per_unit: Decimal) -> Decimal:
        """
        Calculate total amount using USER-ENTERED quantity (NOT KG-converted quantity).
        
        Example:
        - User enters: 5 QT at ₹2500 per QT
        - Total: 5 × ₹2500 = ₹12,500 (NOT 500 × ₹2500)
        """
        return Decimal(str(user_entered_quantity)) * rate_per_unit

    def create_procurement(self, payload: ProcurementCreate, current_user) -> Procurement:
        """
        Create new procurement record.
        
        Key points:
        1. Accept user-entered quantity and unit
        2. Validate inputs
        3. Convert quantity to KG for storage
        4. Calculate total_amount using USER-ENTERED quantity
        """
        if current_user.role.name not in ["FPO Admin", "Manager"]:
            raise HTTPException(403, "Not authorized")

        org_id = payload.organization_id or current_user.organization_id

        # Validate farmer
        farmer = self.farmer_repo.get_by_id(payload.farmer_id)
        if not farmer or farmer.organization_id != org_id or not farmer.is_active:
            raise HTTPException(400, "Invalid or inactive farmer")

        # Validate crop
        crop = self.crop_repo.get_by_id(payload.crop_id)
        if not crop or not crop.is_active:
            raise HTTPException(400, "Invalid or inactive crop")

        # Validate quantities
        if payload.quantity <= 0 or payload.rate_per_unit <= 0:
            raise HTTPException(400, "Quantity and rate must be positive")

        # Validate quality grade
        if payload.quality_grade and payload.quality_grade not in ["A", "B", "C", "D"]:
            raise HTTPException(400, "Quality grade must be A, B, C or D")

        # Check for duplicates
        if self.repo.exists_duplicate(payload.farmer_id, payload.crop_id, payload.procurement_date.date()):
            raise HTTPException(400, "Duplicate procurement record for same farmer+crop+date")

        # IMPORTANT: Convert user-entered quantity to KG for storage
        quantity_in_kg = self._convert_to_kg(payload.quantity, payload.unit)

        # IMPORTANT: Calculate total using USER-ENTERED quantity (NOT KG)
        total_amount = self._calculate_total_amount(payload.quantity, payload.rate_per_unit)

        procurement = Procurement(
            procurement_no=self._generate_procurement_no(org_id),
            procurement_date=payload.procurement_date,
            farmer_id=payload.farmer_id,
            crop_id=payload.crop_id,
            organization_id=org_id,
            quantity=quantity_in_kg,  # Stored in KG
            unit=payload.unit,  # Store original unit for reverse conversion
            rate_per_unit=payload.rate_per_unit,
            total_amount=total_amount,  # Based on user-entered quantity
            quality_grade=payload.quality_grade,
            remarks=payload.remarks,
            is_active=True
        )

        try:
            # Create procurement but do not commit yet
            self.repo.create(procurement, commit=False)

            # Create corresponding Inventory IN entry
            inventory_entry = InventoryLedger(
                organization_id=procurement.organization_id,
                crop_id=procurement.crop_id,
                transaction_type="IN",
                quantity=float(procurement.quantity),
                reference_type="PROCUREMENT",
                reference_id=procurement.id,
                remarks=f"Procurement {procurement.procurement_no}",
                is_active=True,
            )

            self.inventory_repo.add(inventory_entry)

            # Commit procurement + inventory together
            self.db.commit()

            self.db.refresh(procurement)

            return procurement

        except Exception:
            self.db.rollback()
            raise

    def update_procurement(self, procurement_id: int, payload: ProcurementUpdate, current_user) -> Procurement:
        """
        Update procurement record.
        
        Key points:
        1. If quantity/unit provided, convert to KG
        2. Recalculate total_amount if quantity or rate changed
        3. User-entered quantity must be used for total_amount calculation
        """
        if current_user.role.name not in ["FPO Admin", "Manager"]:
            raise HTTPException(403, "Not authorized")

        procurement = self.repo.get_by_id(procurement_id)
        if not procurement:
            raise HTTPException(404, "Procurement not found")

        # Verify authorization
        if current_user.role.name == "Manager" and procurement.organization_id != current_user.organization_id:
            raise HTTPException(403, "Not authorized to update this record")

        # Store original values for total_amount calculation
        updated_quantity = payload.quantity if payload.quantity is not None else procurement.quantity
        updated_unit = payload.unit if payload.unit is not None else procurement.unit
        updated_rate = payload.rate_per_unit if payload.rate_per_unit is not None else procurement.rate_per_unit

        # If quantity or unit changed, re-validate
        if payload.quantity is not None and payload.quantity <= 0:
            raise HTTPException(400, "Quantity must be positive")

        if payload.rate_per_unit is not None and payload.rate_per_unit <= 0:
            raise HTTPException(400, "Rate must be positive")

        # Update fields
        if payload.procurement_date is not None:
            procurement.procurement_date = payload.procurement_date

        if payload.quality_grade is not None:
            if payload.quality_grade not in ["A", "B", "C", "D"]:
                raise HTTPException(400, "Quality grade must be A, B, C or D")
            procurement.quality_grade = payload.quality_grade

        if payload.remarks is not None:
            procurement.remarks = payload.remarks

        if payload.is_active is not None:
            procurement.is_active = payload.is_active

        # Handle quantity update with unit conversion
        if payload.quantity is not None or payload.unit is not None:
            # Convert new quantity to KG for storage
            quantity_in_kg = self._convert_to_kg(updated_quantity, updated_unit)
            procurement.quantity = quantity_in_kg
            
            if payload.unit is not None:
                procurement.unit = payload.unit

        # Handle rate update
        if payload.rate_per_unit is not None:
            procurement.rate_per_unit = payload.rate_per_unit

        # Recalculate total_amount using updated (user-entered) quantity and rate
        # IMPORTANT: Use the USER-ENTERED quantity, not KG-converted
        procurement.total_amount = self._calculate_total_amount(updated_quantity, updated_rate)

        return self.repo.update(procurement)

    def list_procurements(self, current_user, filters=None):
        """
        List procurements with farmer and crop names populated.
        
        Note: Database stores quantity in KG. Frontend handles reverse conversion for display.
        """
        if current_user.role.name == "Super Admin":
            procurements = self.repo.list_all(filters=filters)
        else:
            procurements = self.repo.list_all(current_user.organization_id, filters)

        result = []
        for proc in procurements:
            data = {
                "id": proc.id,
                "procurement_no": proc.procurement_no,
                "procurement_date": proc.procurement_date,
                "farmer_id": proc.farmer_id,
                "crop_id": proc.crop_id,
                "organization_id": proc.organization_id,
                "quantity": proc.quantity,
                "unit": proc.unit,
                "rate_per_unit": proc.rate_per_unit,
                "total_amount": proc.total_amount,
                "quality_grade": proc.quality_grade,
                "remarks": proc.remarks,
                "is_active": proc.is_active,
                "created_at": proc.created_at,
                "updated_at": proc.updated_at,
                
                # Populate farmer and crop names
                "farmer_name": proc.farmer.farmer_name if proc.farmer else "—",
                "crop_name": proc.crop.crop_name if proc.crop else "—",
            }
            result.append(data)
        return result

    def get_procurement(self, procurement_id: int, current_user):
        """
        Get single procurement record.
        
        Note: Returns KG-stored quantity. Frontend handles reverse conversion.
        """
        procurement = self.repo.get_by_id(procurement_id)
        if not procurement:
            raise HTTPException(404, "Procurement not found")

        if current_user.role.name != "Super Admin" and procurement.organization_id != current_user.organization_id:
            raise HTTPException(403, "Not authorized to view this record")

        return procurement

    def toggle_procurement_status(self, procurement_id: int, is_active: bool, current_user):
        """Toggle procurement active/inactive status"""
        procurement = self.get_procurement(procurement_id, current_user)
        procurement.is_active = is_active
        return self.repo.update(procurement)