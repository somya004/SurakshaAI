from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.schemas import (
    Incident,
    RiskEvent,
)
from app.models.incident_model import (
    IncidentDecisionResponse,
)
from app.models.risk_model import (
    CompoundRiskAssessment,
    RiskLevel,
    SensorReadingCreate,
)
from app.agents.alert_agent import (
    create_alert_for_incident,
)
from app.agents.response_action_agent import (
    create_actions_for_incident,
)


ACTIVE_INCIDENT_STATUSES = {
    "open",
    "acknowledged",
    "assigned",
    "investigating",
    "mitigating",
}


SEVERITY_RANK = {
    "normal": 0,
    "advisory": 1,
    "warning": 2,
    "high": 3,
    "critical": 4,
}


def should_create_incident(
    assessment: CompoundRiskAssessment,
) -> tuple[bool, str]:
    """
    Decides whether a compound-risk assessment should
    become an industrial safety incident.

    Warning events remain stored as RiskEvents, while
    high and critical events become incidents.
    """

    if assessment.risk_level == RiskLevel.critical:
        return (
            True,
            "Critical compound-risk condition detected.",
        )

    if assessment.risk_level == RiskLevel.high:
        return (
            True,
            "High compound-risk condition detected.",
        )

    if assessment.final_risk_score >= 61:
        return (
            True,
            "The final compound-risk score is 61 or above.",
        )

    return (
        False,
        "The assessment does not meet the incident threshold.",
    )


def normalize_incident_type(
    predicted_event: str,
) -> str:
    """
    Creates a stable incident type used for deduplication.
    """

    value = predicted_event.strip().lower()

    if not value:
        return "industrial safety hazard"

    return value[:100]


def build_incident_title(
    severity: str,
    incident_type: str,
    zone_id: str,
) -> str:
    formatted_type = incident_type.replace(
        "_",
        " ",
    ).title()

    return (
        f"{severity.title()} Incident: "
        f"{formatted_type} in Zone {zone_id}"
    )[:250]


def merge_pipe_text(
    existing_text: str | None,
    new_values: list[str],
) -> str:
    """
    Combines existing and new values without duplicates.
    """

    combined: list[str] = []

    if existing_text:
        combined.extend(
            value.strip()
            for value in existing_text.split("|")
            if value.strip()
        )

    combined.extend(
        value.strip()
        for value in new_values
        if value and value.strip()
    )

    return " | ".join(
        dict.fromkeys(combined)
    )


async def find_duplicate_incident(
    db: AsyncSession,
    reading: SensorReadingCreate,
    incident_type: str,
    event_time: datetime,
    duplicate_window_minutes: int = 30,
) -> Incident | None:
    """
    Finds an active incident representing the same hazard.

    The same plant, zone, equipment and incident type within
    the configured time window are treated as one incident.
    """

    window_start = (
        event_time
        - timedelta(
            minutes=duplicate_window_minutes
        )
    )

    query = (
        select(Incident)
        .where(
            and_(
                Incident.plant_id == reading.plant_id,
                Incident.zone_id == reading.zone_id,
                Incident.equipment_id == reading.equipment_id,
                Incident.incident_type == incident_type,
                Incident.status.in_(
                    ACTIVE_INCIDENT_STATUSES
                ),
                Incident.latest_event_at >= window_start,
            )
        )
        .order_by(
            Incident.latest_event_at.desc()
        )
        .limit(1)
    )

    result = await db.execute(query)

    return result.scalar_one_or_none()


async def create_or_update_incident(
    db: AsyncSession,
    risk_event: RiskEvent,
    reading: SensorReadingCreate,
    assessment: CompoundRiskAssessment,
) -> IncidentDecisionResponse:
    """
    Creates a new incident or updates an active duplicate.
    """

    required, reason = should_create_incident(
        assessment
    )

    if not required:
        return IncidentDecisionResponse(
            required=False,
            created=False,
            updated_existing=False,
            reason=reason,
            incident=None,
        )

    incident_type = normalize_incident_type(
        assessment.predicted_event
    )

    event_time = (
        reading.timestamp
        if reading.timestamp is not None
        else datetime.now(timezone.utc)
    )

    existing_incident = await find_duplicate_incident(
        db=db,
        reading=reading,
        incident_type=incident_type,
        event_time=event_time,
    )

    severity = assessment.risk_level.value

    if existing_incident is not None:
        existing_incident.risk_event_id = risk_event.id
        existing_incident.latest_event_at = event_time
        existing_incident.updated_at = datetime.now(
            timezone.utc
        )

        existing_incident.event_count += 1

        existing_incident.final_risk_score = max(
            existing_incident.final_risk_score,
            assessment.final_risk_score,
        )

        current_rank = SEVERITY_RANK.get(
            existing_incident.severity,
            0,
        )

        new_rank = SEVERITY_RANK.get(
            severity,
            0,
        )

        if new_rank > current_rank:
            existing_incident.severity = severity

        existing_incident.description = (
            assessment.explanation
        )

        existing_incident.contributing_factors = (
            merge_pipe_text(
                existing_incident.contributing_factors,
                assessment.contributing_factors,
            )
        )

        existing_incident.recommended_actions = (
            merge_pipe_text(
                existing_incident.recommended_actions,
                [assessment.recommended_action],
            )
        )

        existing_incident.exposed_worker_count = max(
            existing_incident.exposed_worker_count,
            (
                assessment
                .worker_exposure_context
                .exposed_worker_count
            ),
        )

        await db.flush()

        return IncidentDecisionResponse(
            required=True,
            created=False,
            updated_existing=True,
            reason=(
                "A matching active incident already existed, "
                "so it was updated."
            ),
            incident=existing_incident,
        )

    incident = Incident(
        risk_event_id=risk_event.id,
        plant_id=reading.plant_id,
        zone_id=reading.zone_id,
        equipment_id=reading.equipment_id,
        sensor_id=reading.sensor_id,
        incident_type=incident_type,
        title=build_incident_title(
            severity=severity,
            incident_type=incident_type,
            zone_id=reading.zone_id,
        ),
        description=assessment.explanation,
        severity=severity,
        status="open",
        final_risk_score=(
            assessment.final_risk_score
        ),
        contributing_factors=" | ".join(
            assessment.contributing_factors
        ),
        recommended_actions=(
            assessment.recommended_action
        ),
        exposed_worker_count=(
            assessment
            .worker_exposure_context
            .exposed_worker_count
        ),
        event_count=1,
        escalation_level=0,
        created_at=event_time,
        latest_event_at=event_time,
        updated_at=datetime.now(timezone.utc),
    )

    db.add(incident)

    await db.flush()

    # Automatically create and deliver an alert.
    await create_alert_for_incident(
        db=db,
        incident=incident,
    )

    # Automatically create emergency and corrective actions.
    await create_actions_for_incident(
        db=db,
        incident=incident,
    )


    return IncidentDecisionResponse(
        required=True,
        created=True,
        updated_existing=False,
        reason=reason,
        incident=incident,
    )