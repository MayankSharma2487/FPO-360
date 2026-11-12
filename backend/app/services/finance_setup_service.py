from fastapi import HTTPException
from app.models.account import Account
from app.models.organization import Organization
from app.services.default_chart import DEFAULT_ACCOUNTS
from app.services.finance_service_base import FinanceServiceBase

class FinanceSetupService(FinanceServiceBase):
    def setup_status(self,user):
          existing={a.account_code:a for a in self.account_repository.by_codes(self._org(user),[a[0] for a in DEFAULT_ACCOUNTS])}
          n=sum(1 for code,name,typ,group,sub,key in DEFAULT_ACCOUNTS if code in existing and (existing[code].account_name,existing[code].account_type,existing[code].account_group,existing[code].account_subtype,existing[code].system_key)==(name,typ,group,sub,key))
          return {"configured": n==len(DEFAULT_ACCOUNTS),"system_accounts":n,"expected_system_accounts":len(DEFAULT_ACCOUNTS)}

    def setup(self,user):
          org=self._org(user)
          try:
           self.financial_year_repository.lock_organization(org)
           existing={a.account_code:a for a in self.account_repository.all_for_organization(org)}
           for code,name,typ,group,sub,key in DEFAULT_ACCOUNTS:
            account=existing.get(code)
            if account is None: self.db.add(Account(organization_id=org,account_code=code,account_name=name,account_type=typ,account_group=group,account_subtype=sub,system_key=key,is_active=True))
            elif (account.account_name,account.account_type,account.account_group,account.account_subtype,account.system_key)!=(name,typ,group,sub,key):
             raise HTTPException(409,f"Default account {code} conflicts with an existing account; resolve it before setup")
           self.db.commit()
          except Exception: self.db.rollback(); raise
          return self.setup_status(user)
