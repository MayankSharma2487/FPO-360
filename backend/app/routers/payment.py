from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.database import get_db
from app.models.crop_master import CropMaster
from app.models.farmer import Farmer
from app.models.payment import Payment
from app.models.procurement import Procurement
from app.schemas.payment import PaymentCreate, PaymentResponse, PaymentUpdate


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


def validate_and_get_relations(
    db: Session,
    payment_data: PaymentCreate,
    current_user,
):
    procurement = (
        db.query(Procurement)
        .filter(
            Procurement.id == payment_data.procurement_id,
            Procurement.organization_id == current_user.organization_id,
        )
        .first()
    )

    if not procurement:
        raise HTTPException(
            status_code=404,
            detail="Procurement not found or unauthorized.",
        )

    farmer = (
        db.query(Farmer)
        .filter(
            Farmer.id == payment_data.farmer_id,
            Farmer.organization_id == current_user.organization_id,
        )
        .first()
    )

    if not farmer:
        raise HTTPException(
            status_code=404,
            detail="Farmer not found or unauthorized.",
        )

    if procurement.farmer_id != farmer.id:
        raise HTTPException(
            status_code=400,
            detail="Procurement does not belong to the selected farmer.",
        )

    if payment_data.amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Payment amount must be greater than zero.",
        )

    if payment_data.amount > procurement.total_amount:
        raise HTTPException(
            status_code=400,
            detail="Payment amount cannot exceed the procurement total amount.",
        )

    return procurement, farmer


def attach_details(db: Session, payment_obj: Payment):
    procurement = (
        db.query(Procurement)
        .filter(Procurement.id == payment_obj.procurement_id)
        .first()
    )

    farmer = (
        db.query(Farmer)
        .filter(Farmer.id == payment_obj.farmer_id)
        .first()
    )

    if procurement:
        payment_obj.procurement_no = procurement.procurement_no
        payment_obj.procurement_total = procurement.total_amount
        payment_obj.procurement_qty = procurement.quantity

        crop = (
            db.query(CropMaster)
            .filter(CropMaster.id == procurement.crop_id)
            .first()
        )

        payment_obj.crop_name = crop.crop_name if crop else "Unknown"

    if farmer:
        payment_obj.farmer_name = farmer.farmer_name

    return payment_obj


@router.get("/", response_model=list[PaymentResponse])
def get_payments(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    payments = (
        db.query(Payment)
        .filter(
            Payment.organization_id == current_user.organization_id,
        )
        .order_by(Payment.created_at.desc())
        .all()
    )

    return [attach_details(db, payment) for payment in payments]


@router.get("/{id}", response_model=PaymentResponse)
def get_payment(
    id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    payment = (
        db.query(Payment)
        .filter(
            Payment.id == id,
            Payment.organization_id == current_user.organization_id,
        )
        .first()
    )

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    return attach_details(db, payment)


@router.post("/", response_model=PaymentResponse)
def create_payment(
    payment: PaymentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    validate_and_get_relations(
        db,
        payment,
        current_user,
    )

    existing = (
        db.query(Payment)
        .filter(
            Payment.procurement_id == payment.procurement_id,
            Payment.organization_id == current_user.organization_id,
            Payment.is_active.is_(True),
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="An active payment already exists for this procurement.",
        )

    db_payment = Payment(
        **payment.model_dump(),
        organization_id=current_user.organization_id,
    )

    db.add(db_payment)
    db.flush()

    db_payment.payment_no = f"PAY-{db_payment.id:06d}"

    db.commit()
    db.refresh(db_payment)

    return get_payment(
        db_payment.id,
        db,
        current_user,
    )


@router.put("/{id}", response_model=PaymentResponse)
def update_payment(
    id: int,
    payment: PaymentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    db_payment = (
        db.query(Payment)
        .filter(
            Payment.id == id,
            Payment.organization_id == current_user.organization_id,
        )
        .first()
    )

    if not db_payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    if payment.amount is not None:
        procurement = (
            db.query(Procurement)
            .filter(
                Procurement.id == db_payment.procurement_id,
                Procurement.organization_id == current_user.organization_id,
            )
            .first()
        )

        if not procurement:
            raise HTTPException(
                status_code=404,
                detail="Procurement not found.",
            )

        if payment.amount <= 0:
            raise HTTPException(
                status_code=400,
                detail="Payment amount must be greater than zero.",
            )

        if payment.amount > procurement.total_amount:
            raise HTTPException(
                status_code=400,
                detail="Payment amount cannot exceed the procurement total amount.",
            )

    update_data = payment.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_payment, key, value)

    db.commit()
    db.refresh(db_payment)

    return get_payment(
        id,
        db,
        current_user,
    )


@router.patch("/{id}/status", response_model=PaymentResponse)
def toggle_payment_status(
    id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    db_payment = (
        db.query(Payment)
        .filter(
            Payment.id == id,
            Payment.organization_id == current_user.organization_id,
        )
        .first()
    )

    if not db_payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    db_payment.is_active = is_active

    db.commit()
    db.refresh(db_payment)

    return attach_details(
        db,
        db_payment,
    )