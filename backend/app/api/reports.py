import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.database.database import get_db
from app.models.user import User
from app.schemas.reports import ReportPage
from app.services.reports_service import ReportsService

router = APIRouter(prefix="/reports", tags=["Reports"])
READ = ("Super Admin", "FPO Admin", "Manager", "Accountant", "Viewer")


def _output(result, export):
    if export:
        output = io.StringIO()
        rows = result["export_rows"]
        if rows:
            writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()), extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow({key: value.isoformat() if hasattr(value, "isoformat") else value for key, value in row.items()})
        return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=report.csv"})
    return {key: value for key, value in result.items() if key != "export_rows"}


def _filters(from_date, to_date, search, **values):
    result = {"from_date": from_date, "to_date": to_date, "search": search}
    result.update({key: value for key, value in values.items() if value is not None})
    return result


@router.get("/procurement", response_model=ReportPage)
def procurement(from_date: date | None = None, to_date: date | None = None, farmer_id: int | None = None, crop_id: int | None = None, status: str | None = Query(None, pattern="^(Active|Inactive)$"), search: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=500), export: bool = False, db: Session = Depends(get_db), user: User = Depends(require_roles(*READ))):
    return _output(ReportsService(db).get_procurement_report(user, _filters(from_date, to_date, search, farmer_id=farmer_id, crop_id=crop_id, status=status), page, page_size), export)


@router.get("/payments", response_model=ReportPage)
def payments(from_date: date | None = None, to_date: date | None = None, farmer_id: int | None = None, payment_method: str | None = None, status: str | None = None, search: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=500), export: bool = False, db: Session = Depends(get_db), user: User = Depends(require_roles(*READ))):
    return _output(ReportsService(db).get_payment_report(user, _filters(from_date, to_date, search, farmer_id=farmer_id, method=payment_method, status=status), page, page_size), export)


@router.get("/inventory", response_model=ReportPage)
def inventory(from_date: date | None = None, to_date: date | None = None, crop_id: int | None = None, movement_type: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=500), export: bool = False, db: Session = Depends(get_db), user: User = Depends(require_roles(*READ))):
    return _output(ReportsService(db).get_inventory_report(user, _filters(from_date, to_date, None, crop_id=crop_id, movement_type=movement_type), page, page_size), export)


@router.get("/sales", response_model=ReportPage)
def sales(from_date: date | None = None, to_date: date | None = None, customer_id: int | None = None, crop_id: int | None = None, payment_status: str | None = None, sale_status: str | None = Query(None, pattern="^(Active|Inactive)$"), search: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=500), export: bool = False, db: Session = Depends(get_db), user: User = Depends(require_roles(*READ))):
    return _output(ReportsService(db).get_sales_report(user, _filters(from_date, to_date, search, customer_id=customer_id, crop_id=crop_id, payment_status=payment_status, sale_status=sale_status), page, page_size), export)


@router.get("/farmers", response_model=ReportPage)
def farmers(status: str | None = None, search: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=500), export: bool = False, db: Session = Depends(get_db), user: User = Depends(require_roles(*READ))):
    active = None if status is None else status.lower() == "active"
    return _output(ReportsService(db).get_farmer_report(user, {"status": active, "search": search}, page, page_size), export)


@router.get("/finance-summary")
def finance_summary(db: Session = Depends(get_db), user: User = Depends(require_roles(*READ))):
    return ReportsService(db).get_finance_summary(user)


@router.get("/licenses")
def licenses(db: Session = Depends(get_db), user: User = Depends(require_roles(*READ))):
    return ReportsService(db).get_license_summary(user)
