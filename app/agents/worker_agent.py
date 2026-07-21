from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.schemas import (
    ShiftRecord,
    Worker,
    WorkerLocation,
    WorkerPPEStatus,
)
from app.models.worker_model import (
    ExposedWorker,
    WorkerExposureContext,
)


FATIGUE_THRESHOLD_HOURS = 10


def get_required_authorization(
    permit_type: str | None,
    worker: Worker,
) -> bool:
    if permit_type is None:
        return True

    normalized_type = permit_type.lower()

    if normalized_type == "hot_work":
        return worker.hot_work_authorized

    if normalized_type == "confined_space":
        return worker.confined_space_authorized

    if normalized_type == "electrical_work":
        return worker.electrical_work_authorized

    if normalized_type == "work_at_height":
        return worker.work_at_height_authorized

    return worker.safety_training_completed


def get_missing_ppe(
    ppe_status: WorkerPPEStatus | None,
    required_ppe: list[str],
) -> list[str]:
    if not required_ppe:
        return []

    if ppe_status is None:
        return required_ppe

    ppe_mapping = {
        "helmet": ppe_status.helmet_detected,
        "hard_hat": ppe_status.helmet_detected,
        "vest": ppe_status.safety_vest_detected,
        "safety_vest": ppe_status.safety_vest_detected,
        "gloves": ppe_status.gloves_detected,
        "goggles": ppe_status.goggles_detected,
        "safety_shoes": ppe_status.safety_shoes_detected,
        "shoes": ppe_status.safety_shoes_detected,
    }

    missing = []

    for ppe_item in required_ppe:
        normalized_item = (
            ppe_item
            .strip()
            .lower()
            .replace(" ", "_")
        )

        is_detected = ppe_mapping.get(
            normalized_item,
            False,
        )

        if not is_detected:
            missing.append(ppe_item.strip())

    return missing


async def get_latest_zone_locations(
    db: AsyncSession,
    zone_id: str,
) -> list[WorkerLocation]:
    result = await db.execute(
        select(WorkerLocation)
        .where(
            WorkerLocation.zone_id == zone_id,
        )
        .order_by(
            WorkerLocation.timestamp.desc()
        )
    )

    all_locations = list(
        result.scalars().all()
    )

    latest_by_worker = {}

    for location in all_locations:
        if location.worker_id not in latest_by_worker:
            latest_by_worker[location.worker_id] = location

    return [
        location
        for location in latest_by_worker.values()
        if location.entry_status.lower() == "inside"
    ]


async def get_latest_ppe_status(
    db: AsyncSession,
    worker_id: str,
    zone_id: str,
) -> WorkerPPEStatus | None:
    result = await db.execute(
        select(WorkerPPEStatus)
        .where(
            WorkerPPEStatus.worker_id == worker_id,
            WorkerPPEStatus.zone_id == zone_id,
        )
        .order_by(
            WorkerPPEStatus.timestamp.desc()
        )
        .limit(1)
    )

    return result.scalar_one_or_none()


async def get_active_shift(
    db: AsyncSession,
    worker_id: str,
    event_time: datetime,
) -> ShiftRecord | None:
    result = await db.execute(
        select(ShiftRecord)
        .where(
            ShiftRecord.worker_id == worker_id,
            ShiftRecord.shift_start <= event_time,
            ShiftRecord.shift_end >= event_time,
            ShiftRecord.attendance_status == "present",
        )
        .order_by(
            ShiftRecord.shift_start.desc()
        )
        .limit(1)
    )

    return result.scalar_one_or_none()


async def build_worker_exposure_context(
    db: AsyncSession,
    zone_id: str,
    permit_type: str | None = None,
    required_ppe: list[str] | None = None,
    event_time: datetime | None = None,
) -> WorkerExposureContext:
    effective_time = (
        event_time
        or datetime.now(timezone.utc)
    )

    required_ppe = required_ppe or []

    locations = await get_latest_zone_locations(
        db=db,
        zone_id=zone_id,
    )

    exposed_workers = []

    unauthorized_worker_count = 0
    untrained_worker_count = 0
    ppe_violation_count = 0
    fatigued_worker_count = 0

    context_conflicts = []
    recommended_actions = []

    for location in locations:
        worker_result = await db.execute(
            select(Worker).where(
                Worker.worker_id == location.worker_id,
                Worker.active.is_(True),
            )
        )

        worker = worker_result.scalar_one_or_none()

        if worker is None:
            continue

        shift = await get_active_shift(
            db=db,
            worker_id=worker.worker_id,
            event_time=effective_time,
        )

        ppe_status = await get_latest_ppe_status(
            db=db,
            worker_id=worker.worker_id,
            zone_id=zone_id,
        )

        training_valid = (
            worker.safety_training_completed
            and (
                worker.training_expiry_date is None
                or worker.training_expiry_date
                >= effective_time
            )
        )

        work_authorized = get_required_authorization(
            permit_type=permit_type,
            worker=worker,
        )

        missing_ppe = get_missing_ppe(
            ppe_status=ppe_status,
            required_ppe=required_ppe,
        )

        shift_active = shift is not None

        fatigue_hours = (
            shift.fatigue_hours
            if shift is not None
            else 0
        )

        handover_completed = (
            shift.handover_completed
            if shift is not None
            else False
        )

        issues = []
        worker_score = 0.0

        if not training_valid:
            untrained_worker_count += 1
            worker_score += 30

            issues.append(
                "Safety training is missing or expired."
            )

        if not work_authorized:
            unauthorized_worker_count += 1
            worker_score += 35

            issues.append(
                "Worker is not authorised for the current work."
            )

        if not worker.medical_clearance_valid:
            worker_score += 25

            issues.append(
                "Worker medical clearance is invalid."
            )

        if not shift_active:
            worker_score += 15

            issues.append(
                "No active shift record was found."
            )

        if fatigue_hours >= FATIGUE_THRESHOLD_HOURS:
            fatigued_worker_count += 1
            worker_score += 20

            issues.append(
                "Worker fatigue hours exceed the threshold."
            )

        if shift_active and not handover_completed:
            worker_score += 10

            issues.append(
                "Shift handover is incomplete."
            )

        if missing_ppe:
            ppe_violation_count += 1
            worker_score += min(
                15 + len(missing_ppe) * 5,
                35,
            )

            issues.append(
                "Required PPE is missing: "
                + ", ".join(missing_ppe)
            )

        worker_score = min(
            worker_score,
            100,
        )

        exposed_workers.append(
            ExposedWorker(
                worker_id=worker.worker_id,
                worker_name=worker.worker_name,
                job_role=worker.job_role,
                zone_id=zone_id,
                safety_training_completed=(
                    worker.safety_training_completed
                ),
                training_valid=training_valid,
                medical_clearance_valid=(
                    worker.medical_clearance_valid
                ),
                required_work_authorized=(
                    work_authorized
                ),
                current_shift_active=shift_active,
                fatigue_hours=fatigue_hours,
                handover_completed=handover_completed,
                missing_ppe=missing_ppe,
                worker_risk_score=round(
                    worker_score,
                    2,
                ),
                detected_issues=issues,
            )
        )

    exposed_worker_count = len(exposed_workers)

    worker_context_score = 0.0

    if exposed_worker_count > 0:
        worker_context_score += min(
            exposed_worker_count * 5,
            25,
        )

    worker_context_score += min(
        unauthorized_worker_count * 20,
        40,
    )

    worker_context_score += min(
        untrained_worker_count * 15,
        30,
    )

    worker_context_score += min(
        ppe_violation_count * 15,
        30,
    )

    worker_context_score += min(
        fatigued_worker_count * 10,
        20,
    )

    worker_context_score = min(
        worker_context_score,
        100,
    )

    if exposed_worker_count > 0:
        context_conflicts.append(
            f"{exposed_worker_count} worker(s) are currently "
            f"present in zone {zone_id}."
        )

    if unauthorized_worker_count > 0:
        context_conflicts.append(
            f"{unauthorized_worker_count} worker(s) are not "
            "authorised for the active work."
        )

        recommended_actions.append(
            "Remove unauthorised workers from the controlled zone."
        )

    if untrained_worker_count > 0:
        context_conflicts.append(
            f"{untrained_worker_count} worker(s) have missing "
            "or expired safety training."
        )

        recommended_actions.append(
            "Verify worker training before work continues."
        )

    if ppe_violation_count > 0:
        context_conflicts.append(
            f"{ppe_violation_count} worker(s) have PPE violations."
        )

        recommended_actions.append(
            "Stop affected workers and provide the required PPE."
        )

    if fatigued_worker_count > 0:
        context_conflicts.append(
            f"{fatigued_worker_count} worker(s) exceed the "
            "fatigue threshold."
        )

        recommended_actions.append(
            "Replace or rest fatigued workers."
        )

    if not context_conflicts:
        recommended_actions.append(
            "No worker exposure conflict was detected."
        )

    return WorkerExposureContext(
        zone_id=zone_id,
        exposed_worker_count=exposed_worker_count,
        unauthorized_worker_count=(
            unauthorized_worker_count
        ),
        untrained_worker_count=(
            untrained_worker_count
        ),
        ppe_violation_count=(
            ppe_violation_count
        ),
        fatigued_worker_count=(
            fatigued_worker_count
        ),
        worker_context_score=round(
            worker_context_score,
            2,
        ),
        exposed_workers=exposed_workers,
        detected_conflicts=context_conflicts,
        recommended_actions=list(
            dict.fromkeys(recommended_actions)
        ),
    )