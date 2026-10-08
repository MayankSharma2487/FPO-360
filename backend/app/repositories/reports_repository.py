from datetime import date, timedelta

from sqlalchemy import case, func, or_

from app.models.account import Account
from app.models.customer import Customer
from app.models.farmer import Farmer
from app.models.inventory import InventoryLedger
from app.models.journal import JournalEntry, JournalLine
from app.models.payment import Payment
from app.models.procurement import Procurement
from app.models.sale import Sale
from app.models.crop_master import CropMaster
from app.models.village import Village
from app.models.financial_year import FinancialYear


class ReportsRepository:
    """Read-only report queries. Every source query is constrained by organization."""

    def __init__(self, db):
        self.db = db

    @staticmethod
    def _page(query, page, page_size):
        rows = query.all()
        total = len(rows)
        return rows[(page - 1) * page_size:page * page_size], total, rows

    def procurement(self, org, filters, page, size):
        q = self.db.query(Procurement, Farmer.farmer_name, CropMaster.crop_name).join(Farmer, Farmer.id == Procurement.farmer_id).join(CropMaster, CropMaster.id == Procurement.crop_id).filter(Procurement.organization_id == org, Farmer.organization_id == org)
        if filters.get("status"):
            q = q.filter(Procurement.is_active.is_(filters["status"].lower() == "active"))
        else:
            q = q.filter(Procurement.is_active.is_(True))
        if filters.get("from_date"): q = q.filter(func.date(Procurement.procurement_date) >= filters["from_date"])
        if filters.get("to_date"): q = q.filter(func.date(Procurement.procurement_date) <= filters["to_date"])
        if filters.get("farmer_id"): q = q.filter(Procurement.farmer_id == filters["farmer_id"])
        if filters.get("crop_id"): q = q.filter(Procurement.crop_id == filters["crop_id"])
        if filters.get("search"): 
            term = f"%{filters['search']}%"
            q = q.filter(or_(Procurement.procurement_no.ilike(term), Farmer.farmer_name.ilike(term), CropMaster.crop_name.ilike(term)))
        q = q.order_by(Procurement.procurement_date.desc(), Procurement.id.desc())
        return self._page(q, page, size)

    def payments(self, org, filters, page, size):
        q = self.db.query(Payment, Farmer.farmer_name, Procurement.procurement_no).join(Farmer, Farmer.id == Payment.farmer_id).outerjoin(Procurement, (Procurement.id == Payment.procurement_id) & (Procurement.organization_id == org)).filter(Payment.organization_id == org, Farmer.organization_id == org, Payment.is_active.is_(True))
        if filters.get("from_date"): q = q.filter(func.date(Payment.payment_date) >= filters["from_date"])
        if filters.get("to_date"): q = q.filter(func.date(Payment.payment_date) <= filters["to_date"])
        if filters.get("farmer_id"): q = q.filter(Payment.farmer_id == filters["farmer_id"])
        if filters.get("method"): q = q.filter(Payment.payment_method == filters["method"])
        if filters.get("status"): q = q.filter(Payment.status == filters["status"])
        if filters.get("search"):
            term = f"%{filters['search']}%"
            q = q.filter(or_(Payment.payment_no.ilike(term), Farmer.farmer_name.ilike(term), Procurement.procurement_no.ilike(term), Payment.reference_no.ilike(term)))
        q = q.order_by(Payment.payment_date.desc(), Payment.id.desc())
        return self._page(q, page, size)

    def inventory(self, org, filters, page, size):
        q = self.db.query(InventoryLedger, CropMaster.crop_name).join(CropMaster, CropMaster.id == InventoryLedger.crop_id).filter(InventoryLedger.organization_id == org, InventoryLedger.is_active.is_(True))
        if filters.get("from_date"): q = q.filter(func.date(InventoryLedger.created_at) >= filters["from_date"])
        if filters.get("to_date"): q = q.filter(func.date(InventoryLedger.created_at) <= filters["to_date"])
        if filters.get("crop_id"): q = q.filter(InventoryLedger.crop_id == filters["crop_id"])
        if filters.get("movement_type"): q = q.filter(InventoryLedger.transaction_type == filters["movement_type"])
        q = q.order_by(InventoryLedger.created_at.desc(), InventoryLedger.id.desc())
        return self._page(q, page, size)

    def sales(self, org, filters, page, size):
        q = self.db.query(Sale, Customer.customer_name, CropMaster.crop_name).join(Customer, Customer.id == Sale.customer_id).join(CropMaster, CropMaster.id == Sale.crop_id).filter(Sale.organization_id == org, Customer.organization_id == org)
        if filters.get("sale_status"):
            q = q.filter(Sale.is_active.is_(filters["sale_status"].lower() == "active"))
        else:
            q = q.filter(Sale.is_active.is_(True))
        if filters.get("from_date"): q = q.filter(func.date(Sale.sale_date) >= filters["from_date"])
        if filters.get("to_date"): q = q.filter(func.date(Sale.sale_date) <= filters["to_date"])
        if filters.get("customer_id"): q = q.filter(Sale.customer_id == filters["customer_id"])
        if filters.get("crop_id"): q = q.filter(Sale.crop_id == filters["crop_id"])
        if filters.get("payment_status"): q = q.filter(Sale.payment_status == filters["payment_status"])
        if filters.get("search"):
            term = f"%{filters['search']}%"
            q = q.filter(or_(Sale.sale_no.ilike(term), Customer.customer_name.ilike(term), CropMaster.crop_name.ilike(term)))
        q = q.order_by(Sale.sale_date.desc(), Sale.id.desc())
        return self._page(q, page, size)

    def farmers(self, org, filters, page, size):
        proc = self.db.query(Procurement.farmer_id.label("fid"), func.count(Procurement.id).label("count"), func.coalesce(func.sum(Procurement.quantity), 0).label("quantity"), func.coalesce(func.sum(Procurement.total_amount), 0).label("value")).filter(Procurement.organization_id == org, Procurement.is_active.is_(True)).group_by(Procurement.farmer_id).subquery()
        pays = self.db.query(Payment.farmer_id.label("fid"), func.coalesce(func.sum(Payment.amount), 0).label("paid")).filter(Payment.organization_id == org, Payment.is_active.is_(True)).group_by(Payment.farmer_id).subquery()
        q = self.db.query(Farmer, Village.village_name, proc.c.count, proc.c.quantity, proc.c.value, pays.c.paid).outerjoin(Village, (Village.id == Farmer.village_id) & (Village.organization_id == org)).outerjoin(proc, proc.c.fid == Farmer.id).outerjoin(pays, pays.c.fid == Farmer.id).filter(Farmer.organization_id == org)
        if filters.get("status") is not None: q = q.filter(Farmer.is_active.is_(filters["status"]))
        if filters.get("search"):
            term = f"%{filters['search']}%"
            q = q.filter(or_(Farmer.farmer_code.ilike(term), Farmer.farmer_name.ilike(term), Farmer.mobile_number.ilike(term), Village.village_name.ilike(term)))
        return self._page(q.order_by(Farmer.farmer_name), page, size)

    def finance_balances(self, org):
        fy = self.db.query(FinancialYear).filter(FinancialYear.organization_id == org, FinancialYear.is_current.is_(True)).first()
        nominal_date_filter = ((Account.account_type.notin_(("Income", "Expense"))) | (JournalEntry.entry_date >= fy.start_date if fy else False))
        if fy:
            nominal_date_filter = (Account.account_type.notin_(("Income", "Expense")) | ((JournalEntry.entry_date >= fy.start_date) & (JournalEntry.entry_date <= fy.end_date)))
        return self.db.query(Account.account_type, Account.account_subtype, Account.system_key, func.coalesce(func.sum(JournalLine.debit), 0), func.coalesce(func.sum(JournalLine.credit), 0)).join(JournalLine, (JournalLine.account_id == Account.id) & (JournalLine.organization_id == org)).join(JournalEntry, (JournalEntry.id == JournalLine.journal_entry_id) & (JournalEntry.organization_id == org)).filter(Account.organization_id == org, JournalEntry.status == "Posted", nominal_date_filter).group_by(Account.account_type, Account.account_subtype, Account.system_key).all()

    def inventory_stock_total(self, org, crop_id=None):
        q = self.db.query(func.coalesce(func.sum(case((InventoryLedger.transaction_type == "IN", InventoryLedger.quantity), else_=-InventoryLedger.quantity)), 0)).filter(InventoryLedger.organization_id == org, InventoryLedger.is_active.is_(True))
        if crop_id: q = q.filter(InventoryLedger.crop_id == crop_id)
        return q.scalar() or 0
