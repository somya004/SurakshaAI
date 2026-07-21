"""Idempotent demo seed: one plant, four zones and fifty workers."""

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select

from app.database.connection import AsyncSessionLocal, create_database_tables
from app.database.schemas import PlantZone, Worker, WorkerLocation, WorkerPPEStatus

PLANT_ID = "PLANT_01"
ZONES = [
    ("ZONE_01", "Coke Oven", "process", 17.6868, 83.2185),
    ("ZONE_02", "Blast Furnace", "high_heat", 17.6872, 83.2191),
    ("ZONE_03", "Rolling Mill", "machinery", 17.6878, 83.2197),
    ("ZONE_04", "Maintenance Bay", "maintenance", 17.6883, 83.2202),
]


async def seed() -> None:
    await create_database_tables()
    now = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as db:
        for index, (zone_id, name, zone_type, lat, lon) in enumerate(ZONES):
            existing = await db.scalar(
                select(PlantZone).where(
                    PlantZone.plant_id == PLANT_ID,
                    PlantZone.zone_id == zone_id,
                )
            )
            if existing is None:
                db.add(
                    PlantZone(
                        plant_id=PLANT_ID,
                        zone_id=zone_id,
                        zone_name=name,
                        zone_type=zone_type,
                        latitude=lat,
                        longitude=lon,
                        floor_level=0,
                        description=f"Demo operational zone {index + 1}",
                    )
                )

        for number in range(1, 51):
            worker_id = f"WKR-{number:03d}"
            zone_id = ZONES[(number - 1) % len(ZONES)][0]
            trained = number % 7 != 0
            ppe_ok = number % 9 != 0

            worker = await db.scalar(
                select(Worker).where(Worker.worker_id == worker_id)
            )
            if worker is None:
                db.add(
                    Worker(
                        worker_id=worker_id,
                        worker_name=f"Demo Worker {number:03d}",
                        employer_name="Suraksha Steel Ltd.",
                        job_role=("Technician" if number % 3 else "Operator"),
                        department=zone_id,
                        experience_years=float((number % 12) + 1),
                        safety_training_completed=trained,
                        hot_work_authorized=number % 4 == 0,
                        confined_space_authorized=number % 5 == 0,
                        electrical_work_authorized=number % 6 == 0,
                        work_at_height_authorized=number % 8 == 0,
                        training_expiry_date=now + timedelta(days=180),
                        medical_clearance_valid=True,
                        active=True,
                    )
                )

            latest_location = await db.scalar(
                select(WorkerLocation)
                .where(WorkerLocation.worker_id == worker_id)
                .order_by(WorkerLocation.timestamp.desc())
                .limit(1)
            )
            if latest_location is None:
                zone = ZONES[(number - 1) % len(ZONES)]
                db.add(
                    WorkerLocation(
                        worker_id=worker_id,
                        plant_id=PLANT_ID,
                        zone_id=zone_id,
                        latitude=zone[3] + number * 0.000001,
                        longitude=zone[4] + number * 0.000001,
                        location_source="demo_seed",
                        entry_status="inside",
                        timestamp=now,
                    )
                )

            latest_ppe = await db.scalar(
                select(WorkerPPEStatus)
                .where(WorkerPPEStatus.worker_id == worker_id)
                .order_by(WorkerPPEStatus.timestamp.desc())
                .limit(1)
            )
            if latest_ppe is None:
                db.add(
                    WorkerPPEStatus(
                        worker_id=worker_id,
                        zone_id=zone_id,
                        helmet_detected=ppe_ok,
                        safety_vest_detected=True,
                        gloves_detected=ppe_ok or number % 2 == 0,
                        goggles_detected=ppe_ok,
                        safety_shoes_detected=True,
                        detection_source="demo_seed",
                        confidence=0.96 if ppe_ok else 0.78,
                        timestamp=now,
                    )
                )

        await db.commit()

    print("Seed complete: 4 zones and 50 workers are available.")


if __name__ == "__main__":
    asyncio.run(seed())
