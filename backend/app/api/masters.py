from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.auth.dependencies import get_current_user
from app.services.master_location_service import MasterLocationService
from app.schemas.master_location import (
    MasterStateResponse,
    MasterDistrictResponse,
    MasterBlockResponse
)

router = APIRouter(
    prefix="/masters",
    tags=["Master Locations"]
)


@router.get("/states", response_model=list[MasterStateResponse])
def get_states(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    service = MasterLocationService(db)
    return service.get_all_states()


@router.get("/districts", response_model=list[MasterDistrictResponse])
def get_districts(
    state_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    service = MasterLocationService(db)
    return service.get_districts_by_state(state_id)


@router.get("/blocks", response_model=list[MasterBlockResponse])
def get_blocks(
    district_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    service = MasterLocationService(db)
    return service.get_blocks_by_district(district_id)