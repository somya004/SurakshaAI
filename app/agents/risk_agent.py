from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.schemas import RiskEvent


# Component importance in the final risk calculation.
RISK_WEIGHTS = {
    "sensor": 0.30,
    "machine": 0.20,
    "accident": 0.20,
    "permit": 0.15,
    "worker": 0.15,
}


def normalize_score(value: float | int | None) -> float:
    """
    Converts a risk value into the range 0–100.
    """

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


def get_risk_level(score: float) -> str:
    """
    Converts the final numerical score into a risk level.
    """

    if score >= 80:
        return "critical"

    if score >= 60:
        return "high"

    if score >= 30:
        return "medium"

    return "low"


def get_recommended_action(
    risk_level: str,
) -> str:
    """
    Returns the primary recommended action.
    """

    actions = {
        "critical": (
            "Immediately stop unsafe operations, create an "
            "incident, alert the emergency team and initiate "
            "required emergency response actions."
        ),
        "high": (
            "Notify the safety officer, inspect the affected "
            "zone and control the identified hazards."
        ),
        "medium": (
            "Monitor the zone closely and schedule a safety "
            "inspection."
        ),
        "low": (
            "Continue normal monitoring."
        ),
    }

    return actions[risk_level]


def calculate_compound_risk(
    sensor_risk: float | int | None = None,
    machine_risk: float | int | None = None,
    accident_risk: float | int | None = None,
    permit_risk: float | int | None = None,
    worker_risk: float | int | None = None,
) -> dict[str, Any]:
    """
    Combines all module risk scores into one final score.

    All input scores must use the range 0–100.
    """

    component_scores = {
        "sensor": normalize_score(sensor_risk),
        "machine": normalize_score(machine_risk),
        "accident": normalize_score(accident_risk),
        "permit": normalize_score(permit_risk),
        "worker": normalize_score(worker_risk),
    }

    weighted_score = sum(
        component_scores[name]
        * RISK_WEIGHTS[name]
        for name in RISK_WEIGHTS
    )

    # Increase the final score when several modules report
    # high risk at the same time.
    high_risk_components = sum(
        score >= 60
        for score in component_scores.values()
    )

    critical_components = sum(
        score >= 80
        for score in component_scores.values()
    )

    compound_bonus = 0.0

    if high_risk_components >= 2:
        compound_bonus += 5.0

    if high_risk_components >= 3:
        compound_bonus += 5.0

    if critical_components >= 2:
        compound_bonus += 10.0

    final_score = normalize_score(
        weighted_score + compound_bonus
    )

    risk_level = get_risk_level(
        final_score
    )

    dominant_source = max(
        component_scores,
        key=component_scores.get,
    )

    return {
        "risk_score": final_score,
        "risk_level": risk_level,
        "dominant_risk_source": dominant_source,
        "component_scores": component_scores,
        "high_risk_components": (
            high_risk_components
        ),
        "critical_components": (
            critical_components
        ),
        "compound_bonus": compound_bonus,
        "recommended_action": (
            get_recommended_action(
                risk_level
            )
        ),
    }


def build_risk_reasons(
    component_scores: dict[str, float],
    additional_reasons: list[str] | None = None,
) -> list[str]:
    """
    Creates readable reasons for the risk event.
    """

    names = {
        "sensor": "Sensor condition",
        "machine": "Machine anomaly",
        "accident": "Accident prediction",
        "permit": "Permit compliance",
        "worker": "Worker safety",
    }

    reasons = []

    sorted_components = sorted(
        component_scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    for component, score in sorted_components:
        if score >= 30:
            reasons.append(
                f"{names[component]} risk score is "
                f"{score:.2f}"
            )

    if additional_reasons:
        for reason in additional_reasons:
            clean_reason = str(
                reason
            ).strip()

            if clean_reason:
                reasons.append(
                    clean_reason
                )

    if not reasons:
        reasons.append(
            "No significant safety hazard detected."
        )

    return reasons


def create_supported_risk_event(
    event_values: dict[str, Any],
) -> RiskEvent:
    """
    Creates RiskEvent using only columns that exist in the
    project's current RiskEvent SQLAlchemy model.

    This prevents errors if the exact RiskEvent field names
    differ slightly between project versions.
    """

    available_columns = {
        column.key
        for column in inspect(
            RiskEvent
        ).mapper.column_attrs
    }

    supported_values = {
        key: value
        for key, value in event_values.items()
        if (
            key in available_columns
            and value is not None
        )
    }

    return RiskEvent(
        **supported_values
    )


async def analyse_and_create_risk_event(
    db: AsyncSession,
    plant_id: str,
    zone_id: str,
    equipment_id: str | None = None,
    sensor_risk: float | int | None = None,
    machine_risk: float | int | None = None,
    accident_risk: float | int | None = None,
    permit_risk: float | int | None = None,
    worker_risk: float | int | None = None,
    additional_reasons: list[str] | None = None,
    create_low_risk_event: bool = False,
) -> dict[str, Any]:
    """
    Main Risk Agent function.

    It:
    1. Combines all risk values.
    2. Determines the final risk level.
    3. Identifies the main risk source.
    4. Creates a RiskEvent.
    5. Returns the complete risk analysis.
    """

    analysis = calculate_compound_risk(
        sensor_risk=sensor_risk,
        machine_risk=machine_risk,
        accident_risk=accident_risk,
        permit_risk=permit_risk,
        worker_risk=worker_risk,
    )

    reasons = build_risk_reasons(
        component_scores=(
            analysis["component_scores"]
        ),
        additional_reasons=(
            additional_reasons
        ),
    )

    analysis["risk_reasons"] = reasons

    # Avoid filling the database with normal low-risk events.
    if (
        analysis["risk_level"] == "low"
        and not create_low_risk_event
    ):
        analysis["risk_event_created"] = False
        analysis["risk_event_id"] = None

        return analysis

    current_time = datetime.now(
        timezone.utc
    )

    reason_text = "; ".join(
        reasons
    )

    # Multiple commonly used field names are supplied.
    # The helper keeps only fields that actually exist
    # inside your RiskEvent table.
    event_values = {
        "plant_id": plant_id,
        "zone_id": zone_id,
        "equipment_id": equipment_id,

        "risk_score": analysis["risk_score"],
        "score": analysis["risk_score"],

        "risk_level": analysis["risk_level"],
        "severity": analysis["risk_level"],
        "priority": analysis["risk_level"],

        "risk_type": (
            analysis["dominant_risk_source"]
        ),
        "source_type": (
            analysis["dominant_risk_source"]
        ),

        "title": (
            f"{analysis['risk_level'].title()} "
            f"safety risk detected"
        ),
        "description": reason_text,
        "reason": reason_text,
        "risk_reason": reason_text,

        "recommended_action": (
            analysis["recommended_action"]
        ),

        "status": "active",
        "event_status": "active",

        "detected_at": current_time,
        "created_at": current_time,
        "updated_at": current_time,
    }

    risk_event = create_supported_risk_event(
        event_values
    )

    db.add(
        risk_event
    )

    try:
        await db.commit()
        await db.refresh(
            risk_event
        )

    except Exception:
        await db.rollback()
        raise

    analysis["risk_event_created"] = True
    analysis["risk_event_id"] = getattr(
        risk_event,
        "id",
        None,
    )

    return analysis