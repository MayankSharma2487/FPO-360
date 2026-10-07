from sqlalchemy import func, Integer
from sqlalchemy.orm import Session, joinedload
from app.models.journal import JournalEntry, JournalLine
from app.models.account import Account


class JournalRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_for_organization(self, organization_id: int):
        return self.db.query(JournalEntry).options(joinedload(JournalEntry.lines)).filter_by(
            organization_id=organization_id).order_by(JournalEntry.entry_date.desc(), JournalEntry.id.desc()).all()

    def get(self, organization_id: int, journal_id: int, for_update: bool = False):
        query = self.db.query(JournalEntry).filter_by(id=journal_id, organization_id=organization_id)
        if for_update:
            query = query.with_for_update(of=JournalEntry)
        else:
            query = query.options(joinedload(JournalEntry.lines))
        return query.first()

    def active_accounts(self, organization_id: int, account_ids):
        return self.db.query(Account).filter(Account.organization_id == organization_id,
            Account.id.in_(account_ids)).with_for_update(read=True).all()

    def party_exists(self, party_model, party_id: int, organization_id: int):
        return self.db.query(party_model.id).filter_by(id=party_id, organization_id=organization_id).first() is not None

    def add_draft(self, entry: JournalEntry):
        self.db.add(entry)
        self.db.flush()
        return entry

    def next_number(self, organization_id: int, financial_year_id: int, prefix: str):
        return self.db.query(func.coalesce(func.max(func.cast(func.substring(JournalEntry.journal_no, len(prefix) + 1), Integer)), 0) + 1).filter(
            JournalEntry.organization_id == organization_id, JournalEntry.financial_year_id == financial_year_id,
            JournalEntry.journal_no.like(prefix + "%")).scalar()

    def lines_for_account(self, organization_id: int, account_id: int, start_date=None, end_date=None):
        query = self.db.query(JournalEntry, JournalLine).join(JournalLine,
            JournalLine.journal_entry_id == JournalEntry.id).filter(JournalEntry.organization_id == organization_id,
            JournalEntry.status == "Posted", JournalLine.organization_id == organization_id,
            JournalLine.account_id == account_id)
        if start_date is not None:
            query = query.filter(JournalEntry.entry_date >= start_date)
        if end_date is not None:
            query = query.filter(JournalEntry.entry_date <= end_date)
        return query.order_by(JournalEntry.entry_date, JournalEntry.id, JournalLine.line_no).all()
