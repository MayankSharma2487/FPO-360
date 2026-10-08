from fastapi import HTTPException

from app.repositories.reports_repository import ReportsRepository
from app.services.license_service import LicenseService


class ReportsService:
    def __init__(self, db):
        self.db = db
        self.repo = ReportsRepository(db)

    @staticmethod
    def _validate_dates(filters):
        if filters.get("from_date") and filters.get("to_date") and filters["from_date"] > filters["to_date"]:
            raise HTTPException(400, "from_date must be on or before to_date")

    def _org(self, user):
        org = getattr(user, "organization_id", None)
        if org is None:
            raise HTTPException(403, "Reports access requires an organization assignment")
        return org

    @staticmethod
    def _response(rows, all_rows, total, page, size, summary, export_rows):
        return {"items": rows, "total": total, "page": page, "page_size": size,
                "summary": summary, "export_rows": export_rows}

    def get_procurement_report(self, user, filters, page=1, page_size=25):
        self._validate_dates(filters); org = self._org(user)
        selected, total, all_data = self.repo.procurement(org, filters, page, page_size)
        data = lambda row: {"id": row[0].id, "procurement_no": row[0].procurement_no, "date": row[0].procurement_date, "farmer_id": row[0].farmer_id, "farmer": row[1], "crop_id": row[0].crop_id, "crop": row[2], "quantity": row[0].quantity, "unit": row[0].unit, "rate": float(row[0].rate_per_unit), "total": float(row[0].total_amount), "status": "Active" if row[0].is_active else "Inactive"}
        full = [data(r) for r in all_data]
        if filters.get("status"): full = [r for r in full if r["status"].lower() == filters["status"].lower()]
        total = len(full); start = (page - 1) * page_size
        items = full[start:start + page_size]
        return self._response(items, full, total, page, page_size, {"transactions": total, "quantity": sum(r["quantity"] for r in full), "value": sum(r["total"] for r in full), "average_rate": sum(r["rate"] for r in full) / total if total else 0, "farmers": len({r["farmer_id"] for r in full})}, full)

    def get_payment_report(self, user, filters, page=1, page_size=25):
        self._validate_dates(filters); selected, total, raw = self.repo.payments(self._org(user), filters, page, page_size)
        full = [{"id": r[0].id, "payment_no": r[0].payment_no, "date": r[0].payment_date, "farmer_id": r[0].farmer_id, "farmer": r[1], "procurement_no": r[2], "amount": float(r[0].amount), "payment_method": r[0].payment_method, "reference_no": r[0].reference_no, "status": r[0].status} for r in raw]
        paid_rows = [r for r in full if r["status"].lower() == "paid"]
        methods = {"cash", "bank", "bank transfer", "upi", "neft", "rtgs"}
        summary = {"paid": sum(r["amount"] for r in paid_rows), "payments": len(full), "cash": sum(r["amount"] for r in paid_rows if r["payment_method"].lower() == "cash"), "bank": sum(r["amount"] for r in paid_rows if r["payment_method"].lower() in ("bank", "bank transfer", "upi", "neft", "rtgs")), "other": sum(r["amount"] for r in paid_rows if r["payment_method"].lower() not in methods)}
        return self._response(full[(page - 1) * page_size:page * page_size], full, total, page, page_size, summary, full)

    def get_inventory_report(self, user, filters, page=1, page_size=25):
        self._validate_dates(filters); org = self._org(user)
        _, total, raw = self.repo.inventory(org, filters, page, page_size)
        full = [{"id": r[0].id, "date": r[0].created_at, "reference": f"{r[0].reference_type}-{r[0].reference_id}" if r[0].reference_id else r[0].reference_type, "crop_id": r[0].crop_id, "item": r[1], "movement_type": r[0].transaction_type, "quantity": r[0].quantity, "source": r[0].reference_type, "remarks": r[0].remarks} for r in raw]
        return self._response(full[(page - 1) * page_size:page * page_size], full, total, page, page_size, {"stock_in": sum(r["quantity"] for r in full if r["movement_type"] == "IN"), "stock_out": sum(r["quantity"] for r in full if r["movement_type"] == "OUT"), "current_stock": float(self.repo.inventory_stock_total(org, filters.get("crop_id"))), "movements": total}, full)

    def get_sales_report(self, user, filters, page=1, page_size=25):
        self._validate_dates(filters); _, total, raw = self.repo.sales(self._org(user), filters, page, page_size)
        full = [{"id": r[0].id, "sale_no": r[0].sale_no, "date": r[0].sale_date, "customer_id": r[0].customer_id, "customer": r[1], "crop_id": r[0].crop_id, "product": r[2], "quantity": r[0].quantity, "unit": r[0].unit, "rate": float(r[0].rate_per_unit), "total": float(r[0].total_amount), "payment_status": r[0].payment_status, "status": "Active" if r[0].is_active else "Inactive"} for r in raw]
        if filters.get("sale_status"): full = [r for r in full if r["status"].lower() == filters["sale_status"].lower()]
        total = len(full); paid = sum(r["total"] for r in full if r["payment_status"] == "Paid")
        return self._response(full[(page - 1) * page_size:page * page_size], full, total, page, page_size, {"transactions": total, "value": sum(r["total"] for r in full), "quantity": sum(r["quantity"] for r in full), "paid": paid, "pending": sum(r["total"] for r in full if r["payment_status"] == "Pending")}, full)

    def get_farmer_report(self, user, filters, page=1, page_size=25):
        _, total, raw = self.repo.farmers(self._org(user), filters, page, page_size)
        full = [{"id": r[0].id, "farmer_code": r[0].farmer_code, "farmer_name": r[0].farmer_name, "mobile": r[0].mobile_number, "village": r[1], "registration_date": r[0].created_at, "status": "Active" if r[0].is_active else "Inactive", "is_shareholder": r[0].is_shareholder, "procurement_count": int(r[2] or 0), "procurement_quantity": float(r[3] or 0), "procurement_value": float(r[4] or 0), "payment_total": float(r[5] or 0)} for r in raw]
        return self._response(full[(page - 1) * page_size:page * page_size], full, total, page, page_size, {"farmers": total, "active": sum(r["status"] == "Active" for r in full), "procurement_value": sum(r["procurement_value"] for r in full), "payment_total": sum(r["payment_total"] for r in full)}, full)

    def get_finance_summary(self, user):
        rows = ReportsRepository(self.db).finance_balances(self._org(user))
        result = {"revenue": 0.0, "expenses": 0.0, "net_position": 0.0, "cash": 0.0, "bank": 0.0, "receivables": 0.0, "payables": 0.0}
        for typ, subtype, key, debit, credit in rows:
            net = float(debit or 0) - float(credit or 0)
            if typ == "Income": result["revenue"] += -net
            elif typ == "Expense": result["expenses"] += net
            elif key == "CASH_IN_HAND": result["cash"] += net
            elif key == "BANK_DEFAULT": result["bank"] += net
            elif key == "ACCOUNTS_RECEIVABLE": result["receivables"] += net
            elif key == "ACCOUNTS_PAYABLE_FARMERS": result["payables"] += -net
        result["net_position"] = result["revenue"] - result["expenses"]
        return result

    def get_license_summary(self, user):
        records = LicenseService(self.db).list_licenses(user)
        return {"total": len(records), "active": sum(r.display_status == "Active" for r in records), "expiring_soon": sum(r.expiring_soon for r in records), "expired": sum(r.display_status == "Expired" for r in records)}
