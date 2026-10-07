from fastapi import HTTPException
from app.repositories.account_repository import AccountRepository
from app.repositories.financial_year_repository import FinancialYearRepository
from app.repositories.journal_repository import JournalRepository
from app.repositories.finance_report_repository import FinanceReportRepository

class FinanceServiceBase:
    def __init__(self, db):
        self.db = db
        self.account_repository = AccountRepository(db)
        self.financial_year_repository = FinancialYearRepository(db)
        self.journal_repository = JournalRepository(db)
        self.report_repository = FinanceReportRepository(db)

    def _org(self, user):
        if user.organization_id is None:
            raise HTTPException(403, "Finance access requires an organization assignment")
        return user.organization_id
