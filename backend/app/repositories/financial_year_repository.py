from sqlalchemy.orm import Session
from app.models.financial_year import FinancialYear
from app.models.organization import Organization
from app.models.journal import JournalEntry


class FinancialYearRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_for_organization(self, organization_id: int):
        return self.db.query(FinancialYear).filter_by(organization_id=organization_id).order_by(FinancialYear.start_date.desc()).all()

    def clear_current(self, organization_id: int):
        return self.db.query(FinancialYear).filter_by(organization_id=organization_id).update({"is_current": False})

    def get(self, organization_id: int, year_id: int, for_update: bool = False):
        query = self.db.query(FinancialYear).filter_by(id=year_id, organization_id=organization_id)
        return (query.with_for_update() if for_update else query).first()

    def lock_organization(self, organization_id: int):
        return self.db.query(Organization).filter(Organization.id == organization_id).with_for_update().one()

    def overlapping(self, organization_id: int, start_date, end_date, exclude_id=None):
        query = self.db.query(FinancialYear).filter(FinancialYear.organization_id == organization_id,
                    FinancialYear.start_date <= end_date, FinancialYear.end_date >= start_date)
        if exclude_id is not None:
            query = query.filter(FinancialYear.id != exclude_id)
        return query.first()

    def has_entries_outside(self, organization_id: int, year_id: int, start_date, end_date):
        return self.db.query(JournalEntry.id).filter(JournalEntry.organization_id == organization_id,
            JournalEntry.financial_year_id == year_id,
            ((JournalEntry.entry_date < start_date) | (JournalEntry.entry_date > end_date))).first() is not None
