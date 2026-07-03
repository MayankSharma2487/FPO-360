from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.master_state import MasterState
from app.models.master_district import MasterDistrict
from app.models.master_block import MasterBlock


class MasterLocationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_states(self) -> List[MasterState]:
        return self.db.query(MasterState).order_by(MasterState.state_name).all()

    def get_districts_by_state(self, state_id: int) -> List[MasterDistrict]:
        return self.db.query(MasterDistrict).filter(
            MasterDistrict.state_id == state_id
        ).order_by(MasterDistrict.district_name).all()

    def get_blocks_by_district(self, district_id: int) -> List[MasterBlock]:
        return self.db.query(MasterBlock).filter(
            MasterBlock.district_id == district_id
        ).order_by(MasterBlock.block_name).all()