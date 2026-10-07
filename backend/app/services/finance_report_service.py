from datetime import datetime, timezone
from decimal import Decimal
from fastapi import HTTPException
from app.models.financial_year import FinancialYear
from app.services.finance_service_base import FinanceServiceBase

class FinanceReportService(FinanceServiceBase):
    def general_ledger(self,user,account_id,start_date,end_date):
        if start_date and end_date and start_date > end_date:
            raise HTTPException(400, "start_date must be on or before end_date")
        org = self._org(user)
        account = self.account_repository.get(org, account_id)
        if not account:
            raise HTTPException(404, "Account not found")
        nominal = account.account_type in ("Income", "Expense")
        years = self.financial_year_repository.list_for_organization(org) if nominal else []
        anchor = start_date or end_date
        starting_year = next((year for year in years if anchor and year.start_date <= anchor <= year.end_date), None)
        if nominal and starting_year is None and anchor is None:
            starting_year = next((year for year in years if year.is_current), None)
        if nominal and start_date is None and starting_year:
            start_date = starting_year.start_date

        normal = -1 if account.account_type in ("Liability", "Equity", "Income") else 1
        opening = Decimal("0.00")
        if start_date:
            if nominal and starting_year:
                sums = self.report_repository.account_totals_between(org, account_id, starting_year.start_date, start_date)
            elif not nominal:
                sums = self.report_repository.account_totals_before(org, account_id, start_date)
            else:
                sums = (0, 0)
            opening = normal * (Decimal(sums[0]) - Decimal(sums[1]))

        rows = self.journal_repository.lines_for_account(org, account_id, start_date, end_date)
        balance = opening
        lines = []
        active_year = starting_year.id if starting_year else None

        def balance_side(value):
            if value == 0:
                return "—"
            return ("Debit" if value > 0 else "Credit") if normal == 1 else ("Credit" if value > 0 else "Debit")

        for entry, line in rows:
            if nominal:
                row_year = next((year for year in years if year.start_date <= entry.entry_date <= year.end_date), None)
                if row_year and active_year is not None and row_year.id != active_year:
                    balance = Decimal(0)
                if row_year:
                    active_year = row_year.id
            balance += normal * (Decimal(line.debit) - Decimal(line.credit))
            lines.append({"date": entry.entry_date, "journal_no": entry.journal_no,
                "narration": line.line_narration or entry.narration, "debit": line.debit,
                "credit": line.credit, "running_balance": abs(balance), "balance_side": balance_side(balance)})

        return {"account_id": account.id, "account_code": account.account_code, "account_name": account.account_name,
            "opening_balance": abs(opening), "opening_balance_side": balance_side(opening), "lines": lines,
            "debit_total": sum((line.debit for _, line in rows), Decimal(0)),
            "credit_total": sum((line.credit for _, line in rows), Decimal(0)),
            "closing_balance": abs(balance), "closing_balance_side": balance_side(balance)}

    def trial_balance(self,user,financial_year_id,as_on_date,include_zero):
      org=self._org(user); fy=self.financial_year_repository.get(org,financial_year_id)
      if not fy: raise HTTPException(404,"Financial year not found")
      if as_on_date < fy.start_date or as_on_date > fy.end_date: raise HTTPException(400,"Report date is outside the financial year")
      agg=self.report_repository.trial_balance_rows(org,as_on_date,fy.start_date)
      historical_profit=self.report_repository.prior_retained_profit(org,fy.start_date)
      retained_transfer=self.report_repository.prior_retained_transfer(org,fy.start_date)
      opening_transfer=self.report_repository.opening_retained_transfer(org,fy.id)
      prior=Decimal(historical_profit or 0)-Decimal(retained_transfer or 0)-Decimal(opening_transfer or 0)
      prior_retained=Decimal(prior or 0); result=[]
      for aid,code,name,typ,key,dr,cr in agg:
       net=Decimal(dr)-Decimal(cr)
       if key=="RETAINED_EARNINGS": net-=prior_retained
       if typ in ("Income","Expense") and as_on_date<fy.start_date: net=Decimal(0)
       if not include_zero and net==0: continue
       result.append({"account_id":aid,"account_code":code,"account_name":name,"debit":net if net>0 else Decimal(0),"credit":-net if net<0 else Decimal(0)})
      return {"financial_year_id":fy.id,"as_on_date":as_on_date,"accounts":result,"debit_total":sum((r["debit"] for r in result),Decimal(0)),"credit_total":sum((r["credit"] for r in result),Decimal(0))}
