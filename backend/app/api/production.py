from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.database.database import get_db
from app.models.user import User
from app.schemas.production import ProductionCreate, ProductionResponse
from app.services.production_service import ProductionService


router = APIRouter(prefix="/production", tags=["Production & Packing"])


@router.post("/", response_model=ProductionResponse, status_code=status.HTTP_201_CREATED)
def create_production(
    payload: ProductionCreate,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key", min_length=1, max_length=128),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("FPO Admin", "Manager")),
):
    return ProductionService(db).create(payload, current_user, idempotency_key)


@router.get("/", response_model=list[ProductionResponse])
def list_production(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("FPO Admin", "Manager", "Accountant", "Viewer")),
):
    return ProductionService(db).list(current_user)


@router.get("/{production_id}", response_model=ProductionResponse)
def get_production(
    production_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("FPO Admin", "Manager", "Accountant", "Viewer")),
):
    return ProductionService(db).get(production_id, current_user)
