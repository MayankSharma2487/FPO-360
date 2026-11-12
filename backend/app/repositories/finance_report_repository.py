from sqlalchemy import case, func, exists, select
from sqlalchemy.orm import Session, aliased
from app.models.account import Account
from app.models.journal import JournalEntry, JournalLine


class FinanceReportRepository:
    def __init__(self, db: Session):
        self.db = db

    def account_totals_before(self, organization_id: int, account_id: int, before_date):
        return self.db.query(func.coalesce(func.sum(JournalLine.debit), 0),
            func.coalesce(func.sum(JournalLine.credit), 0)).join(JournalEntry,
            JournalEntry.id == JournalLine.journal_entry_id).filter(JournalEntry.organization_id == organization_id,
            JournalEntry.status == "Posted", JournalLine.organization_id == organization_id,
            JournalLine.account_id == account_id, JournalEntry.entry_date < before_date).one()

    def account_totals_between(self, organization_id: int, account_id: int, start_date, before_date):
        return self.db.query(func.coalesce(func.sum(JournalLine.debit), 0),
            func.coalesce(func.sum(JournalLine.credit), 0)).join(JournalEntry,
            JournalEntry.id == JournalLine.journal_entry_id).filter(JournalEntry.organization_id == organization_id,
            JournalEntry.status == "Posted", JournalLine.organization_id == organization_id,
            JournalLine.account_id == account_id, JournalEntry.entry_date >= start_date,
            JournalEntry.entry_date < before_date).one()

    def trial_balance_rows(self, organization_id: int, as_on_date, financial_year_start):
        is_nominal = Account.account_type.in_(["Income", "Expense"])
        start_filter = case((is_nominal, JournalEntry.entry_date >= financial_year_start), else_=True)
        return (self.db.query(Account.id, Account.account_code, Account.account_name, Account.account_type,
            Account.system_key,
            func.coalesce(func.sum(case((JournalEntry.id.is_not(None), JournalLine.debit), else_=0)), 0).label("dr"),
            func.coalesce(func.sum(case((JournalEntry.id.is_not(None), JournalLine.credit), else_=0)), 0).label("cr"))
            .outerjoin(JournalLine, (JournalLine.account_id == Account.id) & (JournalLine.organization_id == organization_id))
            .outerjoin(JournalEntry, (JournalEntry.id == JournalLine.journal_entry_id) &
                (JournalEntry.organization_id == organization_id) & (JournalEntry.status == "Posted") &
                (JournalEntry.entry_date <= as_on_date) & start_filter)
            .filter(Account.organization_id == organization_id)
            .group_by(Account.id, Account.account_code, Account.account_name, Account.account_type, Account.system_key).all())

    def prior_retained_profit(self, organization_id: int, before_date):
        # Closing/rollover journals remove P&L from nominal accounts. Exclude
        # their nominal counterpart lines here; the net retained transfer is
        # reconciled separately by prior_retained_transfer().
        retained_line = JournalLine.__table__.alias("retained_line")
        retained_account = aliased(Account)
        closing_journal = exists(select(1).select_from(retained_line).where(
            retained_line.c.journal_entry_id == JournalEntry.id,
            retained_line.c.organization_id == organization_id,
        ).join(retained_account, retained_account.id == retained_line.c.account_id).where(
            retained_account.system_key == "RETAINED_EARNINGS"))
        return (self.db.query(func.coalesce(func.sum(case(
            (Account.account_type == "Income", JournalLine.credit - JournalLine.debit),
            (Account.account_type == "Expense", JournalLine.credit - JournalLine.debit), else_=0)), 0))
            .join(JournalEntry, JournalEntry.id == JournalLine.journal_entry_id)
            .join(Account, Account.id == JournalLine.account_id)
            .filter(JournalLine.organization_id == organization_id, JournalEntry.organization_id == organization_id,
                JournalEntry.status == "Posted", JournalEntry.entry_date < before_date,
                Account.organization_id == organization_id, ~closing_journal).scalar())

    def prior_retained_transfer(self, organization_id: int, before_date):
        return (self.db.query(func.coalesce(func.sum(JournalLine.credit - JournalLine.debit), 0))
            .join(JournalEntry, JournalEntry.id == JournalLine.journal_entry_id)
            .join(Account, Account.id == JournalLine.account_id)
            .filter(JournalLine.organization_id == organization_id, JournalEntry.organization_id == organization_id,
                JournalEntry.status == "Posted", JournalEntry.entry_date < before_date,
                Account.organization_id == organization_id, Account.system_key == "RETAINED_EARNINGS").scalar())

    def opening_retained_transfer(self, organization_id: int, financial_year_id: int):
        return (self.db.query(func.coalesce(func.sum(JournalLine.credit - JournalLine.debit), 0))
            .join(JournalEntry, JournalEntry.id == JournalLine.journal_entry_id)
            .join(Account, Account.id == JournalLine.account_id)
            .filter(JournalLine.organization_id == organization_id, JournalEntry.organization_id == organization_id,
                JournalEntry.financial_year_id == financial_year_id, JournalEntry.status == "Posted",
                JournalEntry.source_type == "OPENING", Account.organization_id == organization_id,
                Account.system_key == "RETAINED_EARNINGS").scalar())

    def has_opening_retained_balance(self, organization_id: int, financial_year_id: int, account_id: int):
        return (self.db.query(JournalLine.id).join(JournalEntry, JournalEntry.id == JournalLine.journal_entry_id)
            .filter(JournalLine.organization_id == organization_id, JournalLine.account_id == account_id,
                JournalEntry.organization_id == organization_id, JournalEntry.financial_year_id == financial_year_id,
                JournalEntry.status == "Posted", JournalEntry.source_type == "OPENING").first() is not None)
