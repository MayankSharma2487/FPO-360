from datetime import datetime, timezone
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import func, Integer, case
from sqlalchemy.orm import joinedload
from app.models.financial_year import FinancialYear
from app.models.account import Account
from app.models.journal import JournalEntry, JournalLine
from app.models.organization import Organization
from app.models.customer import Customer
from app.models.farmer import Farmer
from app.services.finance_service_base import FinanceServiceBase

class FinancialYearService(FinanceServiceBase):
    def list_years(self,user): return self.financial_year_repository.list_for_organization(self._org(user))

    def save_year(self,user,payload,year_id=None):
        org = self._org(user)
        try:
            self.financial_year_repository.lock_organization(org)
            year = self.financial_year_repository.get(org, year_id) if year_id else None
            if year_id and not year:
                raise HTTPException(404, "Financial year not found")
            if year and year.is_locked:
                raise HTTPException(400, "Locked financial year cannot be changed")
            if self.financial_year_repository.overlapping(org, payload.start_date, payload.end_date, year.id if year else None):
                raise HTTPException(400, "Financial years cannot overlap")
            if year and self.financial_year_repository.has_entries_outside(org, year.id, payload.start_date, payload.end_date):
                raise HTTPException(400, "Financial year dates cannot exclude existing journal entries")
            if year is None:
                year = FinancialYear(organization_id=org)
                self.db.add(year)
            year.name = payload.name
            year.start_date = payload.start_date
            year.end_date = payload.end_date
            self.db.commit()
            self.db.refresh(year)
            return year
        except Exception:
            self.db.rollback()
            raise

    def set_current(self,user,id):
      org=self._org(user); self.financial_year_repository.lock_organization(org)
      y=self.financial_year_repository.get(org,id,for_update=True)
      if not y: raise HTTPException(404,"Financial year not found")
      if y.is_locked: raise HTTPException(400,"Locked financial year cannot be current")
      self.financial_year_repository.clear_current(org); y.is_current=True; self.db.commit(); self.db.refresh(y); return y

    def lock_year(self,user,id,locked):
      org=self._org(user); self.financial_year_repository.lock_organization(org)
      y=self.financial_year_repository.get(org,id,for_update=True)
      if not y: raise HTTPException(404,"Financial year not found")
      if locked and y.is_current: raise HTTPException(400,"Set another financial year as current before locking this one")
      y.is_locked=locked; y.locked_by=user.id if locked else None; y.locked_at=datetime.now(timezone.utc) if locked else None; self.db.commit(); return y
