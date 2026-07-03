from sqlalchemy.orm import Session

from app.repositories.master_location_repository import MasterLocationRepository


class MasterLocationService:
    def __init__(self, db: Session):
        self.repo = MasterLocationRepository(db)

    def get_all_states(self):
        return self.repo.get_all_states()

    def get_districts_by_state(self, state_id: int):
        return self.repo.get_districts_by_state(state_id)

    def get_blocks_by_district(self, district_id: int):
        return self.repo.get_blocks_by_district(district_id)