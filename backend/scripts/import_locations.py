"""
Run: python -m scripts.import_locations data/locations.csv
"""
import sys
import csv
from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.models.master_state import MasterState
from app.models.master_district import MasterDistrict
from app.models.master_block import MasterBlock


def import_locations(csv_path: str):
    db = SessionLocal()
    try:
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                state_name = row['state_name'].strip()
                district_name = row['district_name'].strip()
                block_name = row.get('block_name', '').strip()

                # State
                state = db.query(MasterState).filter(MasterState.state_name == state_name).first()
                if not state:
                    state = MasterState(state_name=state_name)
                    db.add(state)
                    db.commit()
                    db.refresh(state)

                # District
                district = db.query(MasterDistrict).filter(
                    MasterDistrict.district_name == district_name,
                    MasterDistrict.state_id == state.id
                ).first()
                if not district:
                    district = MasterDistrict(district_name=district_name, state_id=state.id)
                    db.add(district)
                    db.commit()
                    db.refresh(district)

                # Block (optional)
                if block_name:
                    block = db.query(MasterBlock).filter(
                        MasterBlock.block_name == block_name,
                        MasterBlock.district_id == district.id
                    ).first()
                    if not block:
                        block = MasterBlock(block_name=block_name, district_id=district.id)
                        db.add(block)
                        db.commit()
        print("✅ Location masters imported successfully")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        import_locations(sys.argv[1])
    else:
        print("Usage: python -m scripts.import_locations <csv_file>")