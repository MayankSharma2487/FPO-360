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
from app.services.inventory_posting_service import InventoryPostingService
from app.services.request_idempotency_service import RequestIdempotencyService


class ProcurementService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ProcurementRepository(db)
        self.farmer_repo = FarmerRepository(db)
        self.crop_repo = CropMasterRepository(db)
        self.inventory_repo = InventoryRepository(db)
        self.inventory_posting = InventoryPostingService(db)
        self.request_idempotency = RequestIdempotencyService(db)

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

    def _convert_to_kg(self, quantity: Decimal, unit: str) -> Decimal:
        """
        Convert user-entered quantity to KG for storage.
        
        Conversions:
        - KG: no conversion
        - QUINTAL: 1 QT = 100 KG
        - TON: 1 MT = 1000 KG
        """
        qty = Decimal(quantity)
        
        if unit == "QUINTAL":
            return qty * Decimal("100")
        elif unit == "TON":
            return qty * Decimal("1000")
        elif unit == "KG":
            return qty
        raise HTTPException(400, "Unit must be KG, QUINTAL or TON")

    def _convert_from_kg(self, quantity: Decimal, unit: str) -> Decimal:
        quantity = Decimal(quantity)
        if unit == "QUINTAL":
            return quantity / Decimal("100")
        if unit == "TON":
            return quantity / Decimal("1000")
        if unit == "KG":
            return quantity
        raise HTTPException(400, "Unit must be KG, QUINTAL or TON")

    def _calculate_total_amount(self, user_entered_quantity: Decimal, rate_per_unit: Decimal) -> Decimal:
        """
        Calculate total amount using USER-ENTERED quantity (NOT KG-converted quantity).
        
        Example:
        - User enters: 5 QT at ₹2500 per QT
        - Total: 5 × ₹2500 = ₹12,500 (NOT 500 × ₹2500)
        """
        return Decimal(user_entered_quantity) * Decimal(rate_per_unit)

    def create_procurement(
        self, payload: ProcurementCreate, current_user, idempotency_key: str | None = None
    ) -> Procurement:
        """
        Create new procurement record.
        
        Key points:
        1. Accept user-entered quantity and unit
        2. Validate inputs
        3. Convert quantity to KG for storage
        4. Calculate total_amount using USER-ENTERED quantity
        """
        if current_user.role.name not in ["Super Admin", "FPO Admin", "Manager"]:
            raise HTTPException(403, "Not authorized")

        org_id = payload.organization_id or current_user.organization_id
        if org_id is None:
            raise HTTPException(403, "Procurement requires an explicit organization context")
        if current_user.role.name != "Super Admin" and org_id != current_user.organization_id:
            raise HTTPException(403, "Cannot create procurement for another organization")

        try:
            payload_hash = self.request_idempotency.payload_hash(payload, org_id)
            existing = self.request_idempotency.find_existing(
                org_id, "PROCUREMENT_CREATE", idempotency_key, payload_hash
            )
            if existing is not None:
                original = self.repo.get_by_id(existing.source_id)
                if original is None or original.organization_id != org_id:
                    raise HTTPException(409, "Idempotent procurement result is no longer available")
                return original

            # Validate farmer and crop only after an idempotent replay is resolved.
            farmer = self.farmer_repo.get_by_id(payload.farmer_id)
            if not farmer or farmer.organization_id != org_id or not farmer.is_active:
                raise HTTPException(400, "Invalid or inactive farmer")
            crop = self.crop_repo.get_active_commodity(payload.crop_id, org_id)
            if not crop:
                raise HTTPException(400, "Invalid or inactive crop")
            if payload.quantity <= 0 or payload.rate_per_unit <= 0:
                raise HTTPException(400, "Quantity and rate must be positive")
            if payload.quality_grade and payload.quality_grade not in ["A", "B", "C", "D"]:
                raise HTTPException(400, "Quality grade must be A, B, C or D")
            if self.repo.exists_duplicate(
                payload.farmer_id, payload.crop_id, payload.procurement_date.date()
            ):
                raise HTTPException(400, "Duplicate procurement record for same farmer+crop+date")
            if payload.unit not in ("KG", "QUINTAL", "TON"):
                raise HTTPException(400, "Unit must be KG, QUINTAL or TON")

            quantity_in_kg = self._convert_to_kg(payload.quantity, payload.unit)
            total_amount = self._calculate_total_amount(payload.quantity, payload.rate_per_unit)
            procurement = Procurement(
                procurement_no=self._generate_procurement_no(org_id),
                procurement_date=payload.procurement_date,
                farmer_id=payload.farmer_id,
                crop_id=payload.crop_id,
                organization_id=org_id,
                quantity=quantity_in_kg,
                unit=payload.unit,
                rate_per_unit=payload.rate_per_unit,
                total_amount=total_amount,
                quality_grade=payload.quality_grade,
                remarks=payload.remarks,
                is_active=True,
            )
            # Create procurement but do not commit yet
            self.repo.create(procurement, commit=False)

            self.inventory_posting.post_events([
                self.inventory_posting.source_event(
                    procurement.organization_id,
                    procurement.crop_id,
                    "IN",
                    Decimal(procurement.quantity),
                    "PROCUREMENT",
                    procurement.id,
                    1,
                    f"Procurement {procurement.procurement_no}",
                )
            ])

            self.request_idempotency.store(
                org_id, "PROCUREMENT_CREATE", idempotency_key, payload_hash, procurement.id
            )

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
        if current_user.role.name not in ["Super Admin", "FPO Admin", "Manager"]:
            raise HTTPException(403, "Not authorized")

        procurement = self.repo.get_by_id_for_update(procurement_id)
        if not procurement:
            raise HTTPException(404, "Procurement not found")

        crop = self.crop_repo.get_active_commodity(procurement.crop_id, procurement.organization_id)
        if not crop:
            raise HTTPException(400, "Invalid, inactive, or non-crop item")

        # Verify authorization
        if current_user.role.name != "Super Admin" and procurement.organization_id != current_user.organization_id:
            raise HTTPException(403, "Not authorized to update this record")

        # Store original values for total_amount calculation
        updated_unit = payload.unit if payload.unit is not None else procurement.unit
        if updated_unit not in ("KG", "QUINTAL", "TON"):
            raise HTTPException(400, "Unit must be KG, QUINTAL or TON")
        updated_quantity = (
            payload.quantity
            if payload.quantity is not None
            else self._convert_from_kg(procurement.quantity, updated_unit)
        )
        updated_rate = Decimal(payload.rate_per_unit) if payload.rate_per_unit is not None else Decimal(procurement.rate_per_unit)

        # If quantity or unit changed, re-validate
        if payload.quantity is not None and payload.quantity <= 0:
            raise HTTPException(400, "Quantity must be positive")

        if payload.rate_per_unit is not None and payload.rate_per_unit <= 0:
            raise HTTPException(400, "Rate must be positive")

        quantity_in_kg = self._convert_to_kg(updated_quantity, updated_unit)
        target_active = payload.is_active if payload.is_active is not None else procurement.is_active
        try:
            stock_changed = (
                target_active != procurement.is_active
                or Decimal(procurement.quantity) != quantity_in_kg
            )
            history = self.inventory_posting.source_history(
                procurement.organization_id, "PROCUREMENT", procurement.id
            )
            current_movement = self.inventory_posting.current_source_movement(
                procurement.organization_id, "PROCUREMENT", procurement.id
            )
            if stock_changed and not history:
                raise HTTPException(
                    409,
                    "Procurement inventory movement is missing; lifecycle change requires reconciliation",
                )
            if procurement.is_active and stock_changed and current_movement is None:
                raise HTTPException(
                    409,
                    "Active procurement has no current inventory movement; reconcile before editing",
                )

            revision = self.inventory_posting.next_source_revision(
                procurement.organization_id, "PROCUREMENT", procurement.id
            )
            events = []
            if current_movement is not None and stock_changed:
                events.append(self.inventory_posting.reversal_event(current_movement, revision))
            if target_active and stock_changed:
                events.append(self.inventory_posting.source_event(
                    procurement.organization_id,
                    procurement.crop_id,
                    "IN",
                    quantity_in_kg,
                    "PROCUREMENT",
                    procurement.id,
                    revision,
                    f"Procurement {procurement.procurement_no}",
                ))
            if events:
                self.inventory_posting.post_events(events)

            # Source and movement events commit together; prior posted movements remain unchanged.
            if payload.procurement_date is not None:
                procurement.procurement_date = payload.procurement_date

            if payload.quality_grade is not None:
                if payload.quality_grade not in ["A", "B", "C", "D"]:
                    raise HTTPException(400, "Quality grade must be A, B, C or D")
                procurement.quality_grade = payload.quality_grade

            if payload.remarks is not None:
                procurement.remarks = payload.remarks

            procurement.is_active = target_active

            procurement.quantity = quantity_in_kg
            procurement.unit = updated_unit

            if payload.rate_per_unit is not None:
                procurement.rate_per_unit = updated_rate

            # Recalculate from user-entered quantity, not KG-converted quantity.
            procurement.total_amount = self._calculate_total_amount(updated_quantity, updated_rate)
            return self.repo.update(procurement)
        except Exception:
            self.db.rollback()
            raise

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
        procurement = self.repo.get_by_id_for_update(procurement_id)
        if not procurement:
            raise HTTPException(404, "Procurement not found")
        if current_user.role.name != "Super Admin" and procurement.organization_id != current_user.organization_id:
            raise HTTPException(403, "Not authorized to update this record")
        if procurement.is_active == is_active:
            return procurement
        try:
            history = self.inventory_posting.source_history(
                procurement.organization_id, "PROCUREMENT", procurement.id
            )
            current_movement = self.inventory_posting.current_source_movement(
                procurement.organization_id, "PROCUREMENT", procurement.id
            )
            if not history:
                raise HTTPException(
                    409, "Procurement inventory movement is missing; reconcile before changing status"
                )
            if procurement.is_active and current_movement is None:
                raise HTTPException(
                    409, "Active procurement has no current inventory movement; reconcile before changing status"
                )
            revision = self.inventory_posting.next_source_revision(
                procurement.organization_id, "PROCUREMENT", procurement.id
            )
            events = []
            if current_movement is not None:
                events.append(self.inventory_posting.reversal_event(current_movement, revision))
            if is_active:
                events.append(self.inventory_posting.source_event(
                    procurement.organization_id,
                    procurement.crop_id,
                    "IN",
                    Decimal(procurement.quantity),
                    "PROCUREMENT",
                    procurement.id,
                    revision,
                    f"Procurement {procurement.procurement_no}",
                ))
            self.inventory_posting.post_events(events)
            procurement.is_active = is_active
            return self.repo.update(procurement)
        except Exception:
            self.db.rollback()
            raise
