"""Compatibility facade for callers migrating to domain services."""
from app.services.account_service import AccountService
from app.services.finance_setup_service import FinanceSetupService
from app.services.financial_year_service import FinancialYearService
from app.services.journal_service import JournalService
from app.services.finance_report_service import FinanceReportService
from app.services.account_service import DEFAULT_ACCOUNTS

class FinanceService:
    def __init__(self, db):
        self._services = (FinanceSetupService(db), AccountService(db), FinancialYearService(db), JournalService(db), FinanceReportService(db))

    def __getattr__(self, name):
        for service in self._services:
            if hasattr(service, name):
                return getattr(service, name)
        raise AttributeError(name)
