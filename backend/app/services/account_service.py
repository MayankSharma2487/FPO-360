from fastapi import HTTPException
from app.models.account import Account
from app.services.finance_service_base import FinanceServiceBase
from app.services.default_chart import DEFAULT_ACCOUNTS

class AccountService(FinanceServiceBase):
    def accounts(self,user): return self.account_repository.list_for_organization(self._org(user))

    def account(self,user,id):
          a=self.account_repository.get(self._org(user),id)
          if not a: raise HTTPException(404,"Account not found")
          return a

    def save_account(self,user,p,id=None):
          a=self.account(user,id) if id else Account(organization_id=self._org(user))
          if a.system_key and (a.account_code!=p.account_code or a.account_name!=p.account_name or a.account_type!=p.account_type or a.account_group!=p.account_group or a.account_subtype!=p.account_subtype): raise HTTPException(400,"System accounts cannot be changed")
          for k,v in p.model_dump().items(): setattr(a,k,v)
          if not id: self.db.add(a)
          try: self.db.commit(); self.db.refresh(a); return a
          except Exception: self.db.rollback(); raise HTTPException(409,"Account code already exists")

    def set_account_status(self,user,id,active):
          a=self.account_repository.get(self._org(user),id,for_update=True)
          if not a: raise HTTPException(404,"Account not found")
          if a.system_key and not active: raise HTTPException(400,"System accounts cannot be deactivated")
          a.is_active=active; self.db.commit(); return a
