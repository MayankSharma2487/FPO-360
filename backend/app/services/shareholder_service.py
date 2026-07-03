from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal

from app.models.shareholder import Shareholder
from app.repositories.shareholder_repository import ShareholderRepository
from app.repositories.farmer_repository import FarmerRepository
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.shareholder import ShareholderCreate, ShareholderUpdate


class ShareholderService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ShareholderRepository(db)
        self.farmer_repo = FarmerRepository(db)
        self.org_repo = OrganizationRepository(db)

    def _check_permission(self, current_user, target_org_id: int):
        if current_user.role.name == "Super Admin":
            return
        if current_user.organization_id != target_org_id:
            raise HTTPException(status_code=403, detail="Access denied to other organization")
        if current_user.role.name not in ["FPO Admin", "Manager"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")

    def create_shareholder(self, payload: ShareholderCreate, current_user) -> Shareholder:
        if current_user.role.name != "Super Admin":
            payload.organization_id = current_user.organization_id

        if not payload.organization_id:
            raise HTTPException(status_code=400, detail="Organization ID required")

        farmer = self.farmer_repo.get_by_id(payload.farmer_id)
        if not farmer or farmer.organization_id != payload.organization_id:
            raise HTTPException(status_code=400, detail="Invalid farmer for this organization")

        existing = self.repo.get_by_farmer(payload.farmer_id)
        if existing:
            raise HTTPException(status_code=400, detail="This farmer is already a shareholder")

        # Auto-generate shareholder_no
        if not getattr(payload, 'shareholder_no', None) or str(payload.shareholder_no).strip() == "":
            existing_max = self.db.query(Shareholder).filter(
                Shareholder.organization_id == payload.organization_id
            ).order_by(Shareholder.shareholder_no.desc()).first()

            num = 1
            if existing_max and existing_max.shareholder_no.startswith("SH-"):
                try:
                    num = int(existing_max.shareholder_no.split("-")[1]) + 1
                except:
                    num = 1
            payload.shareholder_no = f"SH-{num:05d}"

        # Calculate total capital
        total_capital = Decimal(payload.share_count) * Decimal(payload.share_value)

        new_shareholder = Shareholder(
            shareholder_no=payload.shareholder_no,
            share_certificate_no=payload.share_certificate_no,
            share_count=payload.share_count,
            share_value=payload.share_value,
            total_share_capital=total_capital,
            joining_date=payload.joining_date,
            is_active=payload.is_active,
            farmer_id=payload.farmer_id,
            organization_id=payload.organization_id,
        )
        return self.repo.create(new_shareholder)

    def update_shareholder(self, shareholder_id: int, payload: ShareholderUpdate, current_user) -> Shareholder:
        shareholder = self.repo.get_by_id(shareholder_id)
        if not shareholder:
            raise HTTPException(status_code=404, detail="Shareholder not found")

        self._check_permission(current_user, shareholder.organization_id)

        update_data = payload.model_dump(exclude_unset=True)

        if 'share_count' in update_data or 'share_value' in update_data:
            share_count = update_data.get('share_count', shareholder.share_count)
            share_value = update_data.get('share_value', shareholder.share_value)
            update_data['total_share_capital'] = Decimal(share_count) * Decimal(share_value)

        return self.repo.update(shareholder, update_data)

    def toggle_status(self, shareholder_id: int, is_active: bool, current_user) -> Shareholder:
        shareholder = self.repo.get_by_id(shareholder_id)
        if not shareholder:
            raise HTTPException(status_code=404, detail="Shareholder not found")
        self._check_permission(current_user, shareholder.organization_id)
        return self.repo.toggle_active(shareholder, is_active)

    def list_shareholders(self, current_user):
        if current_user.role.name == "Super Admin":
            shareholders = self.repo.list_all()
        else:
            shareholders = self.repo.list_all(current_user.organization_id)

        result = []
        for sh in shareholders:
            data = {
                    "id": sh.id,
                    "shareholder_no": sh.shareholder_no,
                    "share_certificate_no": sh.share_certificate_no,
                    "share_count": sh.share_count,
                    "share_value": sh.share_value,
                    "total_share_capital": sh.total_share_capital,
                    "joining_date": sh.joining_date,
                    "is_active": sh.is_active,
                    "farmer_id": sh.farmer_id,
                    "organization_id": sh.organization_id,

                    "created_at": sh.created_at,
                    "updated_at": sh.updated_at,

                    "farmer_name": sh.farmer.farmer_name if sh.farmer else "—",
                    "farmer_mobile": sh.farmer.mobile_number if sh.farmer else None,
                }

            result.append(data)
        return result