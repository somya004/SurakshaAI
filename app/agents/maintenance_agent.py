from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.schemas import MaintenanceOrder


ACTIVE_MAINTENANCE_STATUSES = {
    "scheduled",
    "in_progress",
    "paused",
}


def normalize_score(
    value: float | int | None,
) -> float:
    """Convert a value into the range 0–100."""

    if value is None:
        return 0.0

    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0

    return round(
        max(0.0, min(score, 100.0)),
        2,
    )


def get_maintenance_priority(
    anomaly_score: float,
) -> str:
    """Convert anomaly score into maintenance priority."""

    if anomaly_score >= 85:
        return "critical"

    if anomaly_score >= 70:
        return "high"

    if anomaly_score >= 40:
        return "medium"

    return "low"


def get_maintenance_type(
    anomaly_score: float,
    equipment_status: str | None,
) -> str:
    """Determine the recommended maintenance type."""

    clean_status = str(
        equipment_status or ""
    ).strip().lower()

    if (
        anomaly_score >= 85
        or clean_status
        in {
            "failed",
            "shutdown",
            "critical",
            "non_operational",
        }
    ):
        return "corrective"

    if anomaly_score >= 60:
        return "predictive"

    return "preventive"


def get_recommended_action(
    priority: str,
) -> str:
    """Return the recommended equipment action."""

    actions = {
        "critical": (
            "Immediately stop the equipment, isolate the energy "
            "source, apply lockout/tagout and begin emergency "
            "maintenance inspection."
        ),
        "high": (
            "Schedule urgent maintenance and restrict equipment "
            "operation until inspection is completed."
        ),
        "medium": (
            "Schedule preventive maintenance and closely monitor "
            "the equipment condition."
        ),
        "low": (
            "Continue normal operation and routine monitoring."
        ),
    }

    return actions[priority]


def calculate_machine_anomaly_score(
    temperature_score: float | int | None = None,
    vibration_score: float | int | None = None,
    pressure_score: float | int | None = None,
    current_score: float | int | None = None,
    runtime_score: float | int | None = None,
    model_anomaly_score: float | int | None = None,
) -> dict[str, Any]:
    """
    Calculate the final machine anomaly score.

    Every input score should be between 0 and 100.
    """

    scores = {
        "temperature": normalize_score(
            temperature_score
        ),
        "vibration": normalize_score(
            vibration_score
        ),
        "pressure": normalize_score(
            pressure_score
        ),
        "current": normalize_score(
            current_score
        ),
        "runtime": normalize_score(
            runtime_score
        ),
        "model": normalize_score(
            model_anomaly_score
        ),
    }

    weights = {
        "temperature": 0.20,
        "vibration": 0.25,
        "pressure": 0.15,
        "current": 0.15,
        "runtime": 0.10,
        "model": 0.15,
    }

    available_scores = {
        name: score
        for name, score in scores.items()
        if score > 0
    }

    if not available_scores:
        final_score = 0.0
    else:
        used_weight = sum(
            weights[name]
            for name in available_scores
        )

        weighted_total = sum(
            available_scores[name] * weights[name]
            for name in available_scores
        )

        final_score = weighted_total / used_weight

    high_components = sum(
        score >= 70
        for score in scores.values()
    )

    critical_components = sum(
        score >= 85
        for score in scores.values()
    )

    compound_bonus = 0.0

    if high_components >= 2:
        compound_bonus += 5.0

    if high_components >= 3:
        compound_bonus += 5.0

    if critical_components >= 2:
        compound_bonus += 10.0

    final_score = normalize_score(
        final_score + compound_bonus
    )

    priority = get_maintenance_priority(
        final_score
    )

    dominant_parameter = max(
        scores,
        key=scores.get,
    )

    return {
        "anomaly_score": final_score,
        "priority": priority,
        "dominant_parameter": dominant_parameter,
        "component_scores": scores,
        "high_components": high_components,
        "critical_components": critical_components,
        "compound_bonus": compound_bonus,
        "maintenance_required": final_score >= 40,
        "recommended_action": get_recommended_action(
            priority
        ),
    }


def build_failure_description(
    analysis: dict[str, Any],
    additional_reasons: list[str] | None = None,
) -> str:
    """Create a readable maintenance failure description."""

    parameter_names = {
        "temperature": "Temperature",
        "vibration": "Vibration",
        "pressure": "Pressure",
        "current": "Electrical current",
        "runtime": "Runtime",
        "model": "Machine-learning anomaly",
    }

    reasons: list[str] = []

    sorted_scores = sorted(
        analysis["component_scores"].items(),
        key=lambda item: item[1],
        reverse=True,
    )

    for parameter, score in sorted_scores:
        if score >= 40:
            reasons.append(
                f"{parameter_names[parameter]} risk score "
                f"is {score:.2f}"
            )

    if additional_reasons:
        for reason in additional_reasons:
            clean_reason = str(reason).strip()

            if clean_reason:
                reasons.append(clean_reason)

    if not reasons:
        reasons.append(
            "Routine preventive maintenance recommended."
        )

    return "; ".join(reasons)


def create_supported_maintenance_order(
    values: dict[str, Any],
) -> MaintenanceOrder:
    """
    Create MaintenanceOrder using only columns available
    in the current SQLAlchemy model.
    """

    available_columns = {
        column.key
        for column in inspect(
            MaintenanceOrder
        ).mapper.column_attrs
    }

    supported_values = {
        key: value
        for key, value in values.items()
        if (
            key in available_columns
            and value is not None
        )
    }

    return MaintenanceOrder(
        **supported_values
    )


async def find_active_maintenance_order(
    db: AsyncSession,
    equipment_id: str,
) -> MaintenanceOrder | None:
    """
    Check whether the equipment already has an active
    maintenance order.
    """

    result = await db.execute(
        select(MaintenanceOrder)
        .where(
            MaintenanceOrder.equipment_id
            == equipment_id,
            MaintenanceOrder.maintenance_status.in_(
                ACTIVE_MAINTENANCE_STATUSES
            ),
        )
        .order_by(
            MaintenanceOrder.reported_time.desc()
        )
        .limit(1)
    )

    return result.scalar_one_or_none()


async def analyse_and_create_maintenance_order(
    db: AsyncSession,
    plant_id: str,
    zone_id: str,
    equipment_id: str,
    temperature_score: float | int | None = None,
    vibration_score: float | int | None = None,
    pressure_score: float | int | None = None,
    current_score: float | int | None = None,
    runtime_score: float | int | None = None,
    model_anomaly_score: float | int | None = None,
    equipment_status: str | None = None,
    assigned_team: str | None = None,
    additional_reasons: list[str] | None = None,
    automatically_create_order: bool = True,
    avoid_duplicate_order: bool = True,
) -> dict[str, Any]:
    """
    Main Maintenance Agent.

    It:
    1. Calculates the machine anomaly score.
    2. Determines maintenance priority and type.
    3. Checks for an existing active work order.
    4. Creates a new MaintenanceOrder when needed.
    """

    analysis = calculate_machine_anomaly_score(
        temperature_score=temperature_score,
        vibration_score=vibration_score,
        pressure_score=pressure_score,
        current_score=current_score,
        runtime_score=runtime_score,
        model_anomaly_score=model_anomaly_score,
    )

    priority = analysis["priority"]

    maintenance_type = get_maintenance_type(
        anomaly_score=analysis["anomaly_score"],
        equipment_status=equipment_status,
    )

    analysis["maintenance_type"] = (
        maintenance_type
    )

    analysis["failure_description"] = (
        build_failure_description(
            analysis=analysis,
            additional_reasons=additional_reasons,
        )
    )

    analysis["maintenance_order_created"] = False
    analysis["work_order_id"] = None
    analysis["duplicate_order_found"] = False

    if not analysis["maintenance_required"]:
        return analysis

    if not automatically_create_order:
        return analysis

    if avoid_duplicate_order:
        existing_order = (
            await find_active_maintenance_order(
                db=db,
                equipment_id=equipment_id,
            )
        )

        if existing_order is not None:
            analysis["duplicate_order_found"] = True
            analysis["work_order_id"] = getattr(
                existing_order,
                "work_order_id",
                None,
            )
            analysis["existing_order_status"] = getattr(
                existing_order,
                "maintenance_status",
                None,
            )

            return analysis

    now = datetime.now(timezone.utc)

    if priority == "critical":
        scheduled_start = now
        scheduled_end = now + timedelta(hours=4)

    elif priority == "high":
        scheduled_start = now + timedelta(hours=1)
        scheduled_end = now + timedelta(hours=12)

    elif priority == "medium":
        scheduled_start = now + timedelta(days=1)
        scheduled_end = now + timedelta(days=2)

    else:
        scheduled_start = now + timedelta(days=7)
        scheduled_end = now + timedelta(days=8)

    work_order_id = (
        f"WO-{now:%Y%m%d%H%M%S}-"
        f"{uuid4().hex[:6].upper()}"
    )

    lockout_required = priority in {
        "high",
        "critical",
    }

    order_values = {
        "work_order_id": work_order_id,
        "plant_id": plant_id,
        "zone_id": zone_id,
        "equipment_id": equipment_id,
        "maintenance_type": maintenance_type,
        "failure_description": (
            analysis["failure_description"]
        ),
        "maintenance_status": "scheduled",
        "equipment_status": (
            "shutdown"
            if priority == "critical"
            else "under_maintenance"
        ),
        "criticality": priority,
        "assigned_team": assigned_team,
        "lockout_tagout_required": (
            lockout_required
        ),
        "lockout_tagout_confirmed": False,
        "maintenance_overdue_days": 0,
        "reported_time": now,
        "scheduled_start": scheduled_start,
        "scheduled_end": scheduled_end,
    }

    maintenance_order = (
        create_supported_maintenance_order(
            order_values
        )
    )

    db.add(maintenance_order)

    try:
        await db.commit()
        await db.refresh(maintenance_order)

    except Exception:
        await db.rollback()
        raise

    analysis["maintenance_order_created"] = True
    analysis["work_order_id"] = getattr(
        maintenance_order,
        "work_order_id",
        work_order_id,
    )

    return analysis