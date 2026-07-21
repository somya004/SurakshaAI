"""Seed SurakshaAI with 4 zones, 50 workers, locations, PPE and shifts.

Copy this script into your project's scripts/ folder and copy the generated
CSV files into data/mock/. Run from the project root:

    python scripts/seed_mock_industrial_data.py
"""

import asyncio
import csv
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import delete

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.database.connection import AsyncSessionLocal, create_database_tables
from app.database.schemas import (
    PlantZone,
    ShiftRecord,
    Worker,
    WorkerLocation,
    WorkerPPEStatus,
)

DATA_DIR = PROJECT_ROOT / "data" / "mock"


def as_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes", "y"}


def as_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def load_csv(filename: str) -> list[dict[str, str]]:
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing mock data file: {path}")

    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


async def seed() -> None:
    await create_database_tables()

    zone_rows = load_csv("plant_zones.csv")
    worker_rows = load_csv("workers.csv")
    location_rows = load_csv("worker_locations.csv")
    ppe_rows = load_csv("worker_ppe_status.csv")
    shift_rows = load_csv("shift_records.csv")

    async with AsyncSessionLocal() as db:
        # Mock-only reset. Remove these delete calls when mixing with real data.
        await db.execute(delete(WorkerPPEStatus))
        await db.execute(delete(WorkerLocation))
        await db.execute(delete(ShiftRecord))
        await db.execute(delete(Worker))
        await db.execute(delete(PlantZone))

        db.add_all([
            PlantZone(
                plant_id=row["plant_id"],
                zone_id=row["zone_id"],
                zone_name=row["zone_name"],
                zone_type=row["zone_type"] or None,
                latitude=float(row["latitude"]),
                longitude=float(row["longitude"]),
                floor_level=int(row["floor_level"]),
                description=row["description"] or None,
            )
            for row in zone_rows
        ])

        db.add_all([
            Worker(
                worker_id=row["worker_id"],
                worker_name=row["worker_name"],
                employer_name=row["employer_name"] or None,
                job_role=row["job_role"],
                department=row["department"] or None,
                experience_years=float(row["experience_years"]),
                safety_training_completed=as_bool(row["safety_training_completed"]),
                hot_work_authorized=as_bool(row["hot_work_authorized"]),
                confined_space_authorized=as_bool(row["confined_space_authorized"]),
                electrical_work_authorized=as_bool(row["electrical_work_authorized"]),
                work_at_height_authorized=as_bool(row["work_at_height_authorized"]),
                training_expiry_date=as_datetime(row["training_expiry_date"]),
                medical_clearance_valid=as_bool(row["medical_clearance_valid"]),
                active=as_bool(row["active"]),
            )
            for row in worker_rows
        ])

        db.add_all([
            WorkerLocation(
                worker_id=row["worker_id"],
                plant_id=row["plant_id"],
                zone_id=row["zone_id"],
                latitude=float(row["latitude"]),
                longitude=float(row["longitude"]),
                location_source=row["location_source"],
                entry_status=row["entry_status"],
                timestamp=as_datetime(row["timestamp"]),
            )
            for row in location_rows
        ])

        db.add_all([
            WorkerPPEStatus(
                worker_id=row["worker_id"],
                zone_id=row["zone_id"],
                helmet_detected=as_bool(row["helmet_detected"]),
                safety_vest_detected=as_bool(row["safety_vest_detected"]),
                gloves_detected=as_bool(row["gloves_detected"]),
                goggles_detected=as_bool(row["goggles_detected"]),
                safety_shoes_detected=as_bool(row["safety_shoes_detected"]),
                detection_source=row["detection_source"],
                confidence=float(row["confidence"]),
                timestamp=as_datetime(row["timestamp"]),
            )
            for row in ppe_rows
        ])

        db.add_all([
            ShiftRecord(
                shift_id=row["shift_id"],
                worker_id=row["worker_id"],
                plant_id=row["plant_id"],
                zone_id=row["zone_id"] or None,
                shift_name=row["shift_name"],
                shift_start=as_datetime(row["shift_start"]),
                shift_end=as_datetime(row["shift_end"]),
                handover_completed=as_bool(
                    row["handover_completed"]
                ),
            )
            for row in shift_rows
        ])

        await db.commit()

    print(
        "Mock seed complete: "
        f"{len(zone_rows)} zones, "
        f"{len(worker_rows)} workers, "
        f"{len(location_rows)} locations, "
        f"{len(ppe_rows)} PPE records and "
        f"{len(shift_rows)} shifts."
    )


if __name__ == "__main__":
    asyncio.run(seed())
