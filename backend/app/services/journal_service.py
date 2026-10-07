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

class JournalService(FinanceServiceBase):
    def journals(self,user): return self.journal_repository.list_for_organization(self._org(user))

    def journal(self,user,id):
      j=self.journal_repository.get(self._org(user),id)
      if not j: raise HTTPException(404,"Journal not found")
      return j

    def create_journal(self,user,p):
        org = self._org(user)
        if len(p.lines) < 2:
            raise HTTPException(400, "Journal must contain at least two lines")
        if any((line.debit > 0) == (line.credit > 0) for line in p.lines):
            raise HTTPException(400, "Each line must have exactly one positive debit or credit")
        if sum((line.debit for line in p.lines), Decimal(0)) != sum((line.credit for line in p.lines), Decimal(0)):
            raise HTTPException(400, "Journal debits and credits must balance")
        try:
            fy = self.financial_year_repository.get(org, p.financial_year_id, for_update=True)
            if not fy:
                raise HTTPException(400, "Invalid financial year")
            if fy.is_locked:
                raise HTTPException(400, "Financial year is locked")
            if not fy.start_date <= p.entry_date <= fy.end_date:
                raise HTTPException(400, "Entry date is outside the financial year")
            ids = {line.account_id for line in p.lines}
            accounts = {account.id: account for account in self.journal_repository.active_accounts(org, ids)}
            if len(accounts) != len(ids) or any(not account.is_active for account in accounts.values()):
                raise HTTPException(400, "Invalid or inactive account")
            for line in p.lines:
                account = accounts[line.account_id]
                if (line.party_type is None) != (line.party_id is None):
                    raise HTTPException(400, "Party type and party id must both be supplied")
                expected = "CUSTOMER" if account.system_key == "ACCOUNTS_RECEIVABLE" else "FARMER" if account.system_key == "ACCOUNTS_PAYABLE_FARMERS" else None
                if expected and line.party_type != expected:
                    raise HTTPException(400, "This account requires a matching party")
                if line.party_type and line.party_type != expected:
                    raise HTTPException(400, "Party information is not allowed on this account")
                if line.party_type:
                    model = Customer if line.party_type == "CUSTOMER" else Farmer
                    if not self.journal_repository.party_exists(model, line.party_id, org):
                        raise HTTPException(400, "Invalid party for organization")
            prefix = f"JV-{fy.start_date.year}-{str(fy.end_date.year)[-2:]}-"
            sequence = self.journal_repository.next_number(org, fy.id, prefix)
            entry = JournalEntry(organization_id=org, journal_no=f"{prefix}{sequence:05d}",
                entry_date=p.entry_date, financial_year_id=fy.id, narration=p.narration,
                source_type=p.source_type, source_id=None, status="Draft", created_by=user.id)
            entry.lines = [JournalLine(organization_id=org, line_no=i, account_id=line.account_id,
                debit=line.debit, credit=line.credit, party_type=line.party_type,
                party_id=line.party_id, line_narration=line.line_narration)
                for i, line in enumerate(p.lines, 1)]
            self.journal_repository.add_draft(entry)
            entry.status = "Posted"
            self.db.commit()
            self.db.refresh(entry)
            return entry
        except Exception as exc:
            self.db.rollback()
            if isinstance(exc, HTTPException):
                raise
            raise HTTPException(409, "Journal could not be posted")

    def void(self,user,id,reason):
      j=self.journal_repository.get(self._org(user),id,for_update=True)
      if not j: raise HTTPException(404,"Journal not found")
      if j.source_type not in ("MANUAL","OPENING"): raise HTTPException(400,"Only manual and opening journals can be voided")
      if j.status=="Void": raise HTTPException(400,"Journal is already void")
      fy=self.financial_year_repository.get(self._org(user),j.financial_year_id,for_update=True)
      if fy.is_locked: raise HTTPException(400,"Financial year is locked")
      if j.status!="Posted": raise HTTPException(400,"Only posted journals can be voided")
      if not reason or not reason.strip(): raise HTTPException(400,"A void reason is required")
      journal_id=j.id
      j.status="Void"; j.voided_by=user.id; j.voided_at=datetime.now(timezone.utc); j.void_reason=reason.strip(); self.db.commit()
      return self.journal_repository.get(self._org(user), journal_id)
