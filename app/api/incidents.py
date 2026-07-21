from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.database.schemas import (
    Incident,
    ResponseAction,
)
from app.models.incident_model import (
    IncidentAcknowledgementRequest,
    IncidentAssignmentRequest,
    IncidentResolutionRequest,
    IncidentResponse,
    IncidentStatusNoteRequest,
)


router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"],
)


ALLOWED_FILTER_STATUSES = {
    "open",
    "acknowledged",
    "assigned",
    "investigating",
    "mitigating",
    "resolved",
    "closed",
    "false_alarm",
}


async def get_incident_or_404(
    incident_id: int,
    db: AsyncSession,
) -> Incident:
    incident = await db.get(
        Incident,
        incident_id,
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    return incident


def prevent_closed_incident_update(
    incident: Incident,
) -> None:
    if incident.status in {
        "closed",
        "false_alarm",
    }:
        raise HTTPException(
            status_code=409,
            detail=(
                "Closed or false-alarm incidents "
                "cannot be updated."
            ),
        )


@router.get(
    "",
    response_model=list[IncidentResponse],
)
async def list_incidents(
    limit: int = 100,
    status: str | None = None,
    severity: str | None = None,
    zone_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    if limit < 1 or limit > 500:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 500",
        )

    query = select(Incident)

    if status is not None:
        if status not in ALLOWED_FILTER_STATUSES:
            raise HTTPException(
                status_code=400,
                detail="Invalid incident status",
            )

        query = query.where(
            Incident.status == status
        )

    if severity is not None:
        allowed_severities = {
            "warning",
            "high",
            "critical",
        }

        if severity not in allowed_severities:
            raise HTTPException(
                status_code=400,
                detail=(
                    "severity must be warning, "
                    "high or critical"
                ),
            )

        query = query.where(
            Incident.severity == severity
        )

    if zone_id is not None:
        query = query.where(
            Incident.zone_id == zone_id
        )

    query = (
        query
        .order_by(
            Incident.latest_event_at.desc()
        )
        .limit(limit)
    )

    result = await db.execute(query)

    return list(
        result.scalars().all()
    )


@router.get(
    "/open",
    response_model=list[IncidentResponse],
)
async def list_open_incidents(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    if limit < 1 or limit > 500:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 500",
        )

    result = await db.execute(
        select(Incident)
        .where(
            Incident.status.in_(
                {
                    "open",
                    "acknowledged",
                    "assigned",
                    "investigating",
                    "mitigating",
                }
            )
        )
        .order_by(
            Incident.latest_event_at.desc()
        )
        .limit(limit)
    )

    return list(
        result.scalars().all()
    )


@router.get(
    "/critical",
    response_model=list[IncidentResponse],
)
async def list_critical_incidents(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    if limit < 1 or limit > 500:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 500",
        )

    result = await db.execute(
        select(Incident)
        .where(
            Incident.severity == "critical"
        )
        .order_by(
            Incident.latest_event_at.desc()
        )
        .limit(limit)
    )

    return list(
        result.scalars().all()
    )


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
)
async def get_incident(
    incident_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await get_incident_or_404(
        incident_id,
        db,
    )


@router.patch(
    "/{incident_id}/acknowledge",
    response_model=IncidentResponse,
)
async def acknowledge_incident(
    incident_id: int,
    payload: IncidentAcknowledgementRequest,
    db: AsyncSession = Depends(get_db),
):
    incident = await get_incident_or_404(
        incident_id,
        db,
    )

    prevent_closed_incident_update(
        incident
    )

    if incident.acknowledged_at is not None:
        raise HTTPException(
            status_code=409,
            detail="Incident is already acknowledged",
        )

    incident.status = "acknowledged"
    incident.acknowledged_by = (
        payload.acknowledged_by
    )
    incident.acknowledgement_note = payload.note
    incident.acknowledged_at = datetime.now(
        timezone.utc
    )
    incident.updated_at = datetime.now(
        timezone.utc
    )

    await db.commit()
    await db.refresh(incident)

    return incident


@router.patch(
    "/{incident_id}/assign",
    response_model=IncidentResponse,
)
async def assign_incident(
    incident_id: int,
    payload: IncidentAssignmentRequest,
    db: AsyncSession = Depends(get_db),
):
    incident = await get_incident_or_404(
        incident_id,
        db,
    )

    prevent_closed_incident_update(
        incident
    )

    incident.assigned_to = payload.assigned_to
    incident.status = "assigned"
    incident.updated_at = datetime.now(
        timezone.utc
    )

    await db.commit()
    await db.refresh(incident)

    return incident


@router.patch(
    "/{incident_id}/start-investigation",
    response_model=IncidentResponse,
)
async def start_incident_investigation(
    incident_id: int,
    payload: IncidentStatusNoteRequest,
    db: AsyncSession = Depends(get_db),
):
    incident = await get_incident_or_404(
        incident_id,
        db,
    )

    prevent_closed_incident_update(
        incident
    )

    incident.status = "investigating"

    if payload.note:
        incident.resolution_notes = payload.note

    incident.updated_at = datetime.now(
        timezone.utc
    )

    await db.commit()
    await db.refresh(incident)

    return incident


@router.patch(
    "/{incident_id}/start-mitigation",
    response_model=IncidentResponse,
)
async def start_incident_mitigation(
    incident_id: int,
    payload: IncidentStatusNoteRequest,
    db: AsyncSession = Depends(get_db),
):
    incident = await get_incident_or_404(
        incident_id,
        db,
    )

    prevent_closed_incident_update(
        incident
    )

    incident.status = "mitigating"

    if payload.note:
        incident.corrective_actions = payload.note

    incident.updated_at = datetime.now(
        timezone.utc
    )

    await db.commit()
    await db.refresh(incident)

    return incident


@router.patch(
    "/{incident_id}/resolve",
    response_model=IncidentResponse,
)
async def resolve_incident(
    incident_id: int,
    payload: IncidentResolutionRequest,
    db: AsyncSession = Depends(get_db),
):
    incident = await get_incident_or_404(
        incident_id,
        db,
    )

    prevent_closed_incident_update(
        incident
    )
    
    pending_result = await db.execute(
        select(ResponseAction)
        .where(
            ResponseAction.incident_id == incident.id,
            ResponseAction.mandatory.is_(True),
            ResponseAction.status.notin_(
                {
                    "verified",
                    "cancelled",
                }
            ),
        )
    )

    pending_actions = list(
        pending_result.scalars().all()
    )

    if pending_actions:
        raise HTTPException(
            status_code=409,
            detail=(
                f"{len(pending_actions)} mandatory response "
                "action(s) are not verified."
            ),
        )

    incident.status = "resolved"
    incident.resolution_notes = (
        payload.resolution_notes
    )
    incident.corrective_actions = (
        payload.corrective_actions
    )
    incident.resolved_at = datetime.now(
        timezone.utc
    )
    incident.updated_at = datetime.now(
        timezone.utc
    )

    await db.commit()
    await db.refresh(incident)

    return incident


@router.patch(
    "/{incident_id}/close",
    response_model=IncidentResponse,
)
async def close_incident(
    incident_id: int,
    db: AsyncSession = Depends(get_db),
):
    incident = await get_incident_or_404(
        incident_id,
        db,
    )

    if incident.status != "resolved":
        raise HTTPException(
            status_code=409,
            detail=(
                "Incident must be resolved "
                "before it can be closed."
            ),
        )

    incident.status = "closed"
    incident.closed_at = datetime.now(
        timezone.utc
    )
    incident.updated_at = datetime.now(
        timezone.utc
    )

    await db.commit()
    await db.refresh(incident)

    return incident


@router.patch(
    "/{incident_id}/false-alarm",
    response_model=IncidentResponse,
)
async def mark_incident_as_false_alarm(
    incident_id: int,
    payload: IncidentStatusNoteRequest,
    db: AsyncSession = Depends(get_db),
):
    incident = await get_incident_or_404(
        incident_id,
        db,
    )

    prevent_closed_incident_update(
        incident
    )

    incident.status = "false_alarm"
    incident.resolution_notes = (
        payload.note
        or "Incident reviewed and marked as false alarm."
    )
    incident.closed_at = datetime.now(
        timezone.utc
    )
    incident.updated_at = datetime.now(
        timezone.utc
    )

    await db.commit()
    await db.refresh(incident)

    return incident