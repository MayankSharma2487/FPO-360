from sqlalchemy.orm import Session
from app.models.account import Account


class AccountRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_for_organization(self, organization_id: int):
        return self.db.query(Account).filter_by(organization_id=organization_id).order_by(Account.account_code).all()

    def all_for_organization(self, organization_id: int):
        return self.db.query(Account).filter_by(organization_id=organization_id).all()

    def get(self, organization_id: int, account_id: int, for_update: bool = False):
        query = self.db.query(Account).filter_by(id=account_id, organization_id=organization_id)
        return (query.with_for_update() if for_update else query).first()

    def by_codes(self, organization_id: int, account_codes):
        return self.db.query(Account).filter(Account.organization_id == organization_id,
                    Account.account_code.in_(account_codes)).all()
