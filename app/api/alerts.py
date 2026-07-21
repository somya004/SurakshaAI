from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.escalation_agent import (
    process_due_escalations,
)
from app.database.connection import get_db
from app.database.schemas import Alert
from app.models.alert_model import (
    AlertAcknowledgementRequest,
    AlertResolutionRequest,
    AlertResponse,
    EscalationProcessingResult,
)


router = APIRouter(
    prefix="/alerts",
    tags=["Alerts and Escalation"],
)


async def get_alert_or_404(
    alert_id: int,
    db: AsyncSession,
) -> Alert:
    alert = await db.get(
        Alert,
        alert_id,
    )

    if alert is None:
        raise HTTPException(
            status_code=404,
            detail="Alert not found",
        )

    return alert


@router.get(
    "",
    response_model=list[AlertResponse],
)
async def list_alerts(
    limit: int = 100,
    status: str | None = None,
    severity: str | None = None,
    acknowledged: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    if limit < 1 or limit > 500:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 500",
        )

    query = select(Alert)

    if status is not None:
        query = query.where(
            Alert.status == status
        )

    if severity is not None:
        query = query.where(
            Alert.severity == severity
        )

    if acknowledged is not None:
        query = query.where(
            Alert.acknowledged == acknowledged
        )

    query = (
        query
        .order_by(
            Alert.created_at.desc()
        )
        .limit(limit)
    )

    result = await db.execute(query)

    return list(
        result.scalars().all()
    )


@router.get(
    "/active",
    response_model=list[AlertResponse],
)
async def list_active_alerts(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Alert)
        .where(
            Alert.acknowledged.is_(False),
            Alert.status.in_(
                {
                    "pending",
                    "sent",
                    "escalated",
                }
            ),
        )
        .order_by(
            Alert.created_at.desc()
        )
        .limit(limit)
    )

    return list(
        result.scalars().all()
    )


@router.post(
    "/process-escalations",
    response_model=EscalationProcessingResult,
)
async def process_alert_escalations(
    db: AsyncSession = Depends(get_db),
):
    result = await process_due_escalations(
        db=db
    )

    await db.commit()

    return result


@router.get(
    "/{alert_id}",
    response_model=AlertResponse,
)
async def get_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await get_alert_or_404(
        alert_id,
        db,
    )


@router.patch(
    "/{alert_id}/acknowledge",
    response_model=AlertResponse,
)
async def acknowledge_alert(
    alert_id: int,
    payload: AlertAcknowledgementRequest,
    db: AsyncSession = Depends(get_db),
):
    alert = await get_alert_or_404(
        alert_id,
        db,
    )

    if alert.acknowledged:
        raise HTTPException(
            status_code=409,
            detail="Alert is already acknowledged",
        )

    now = datetime.now(timezone.utc)

    alert.acknowledged = True
    alert.acknowledged_by = (
        payload.acknowledged_by
    )
    alert.acknowledgement_note = payload.note
    alert.acknowledged_at = now
    alert.status = "acknowledged"
    alert.next_escalation_at = None
    alert.updated_at = now

    await db.commit()
    await db.refresh(alert)

    return alert


@router.patch(
    "/{alert_id}/resolve",
    response_model=AlertResponse,
)
async def resolve_alert(
    alert_id: int,
    payload: AlertResolutionRequest,
    db: AsyncSession = Depends(get_db),
):
    alert = await get_alert_or_404(
        alert_id,
        db,
    )

    if alert.status == "resolved":
        raise HTTPException(
            status_code=409,
            detail="Alert is already resolved",
        )

    now = datetime.now(timezone.utc)

    alert.status = "resolved"
    alert.resolved_at = now
    alert.next_escalation_at = None
    alert.updated_at = now

    if not alert.acknowledged:
        alert.acknowledged = True
        alert.acknowledged_by = (
            payload.resolved_by
        )
        alert.acknowledged_at = now

    alert.acknowledgement_note = (
        f"Resolved by {payload.resolved_by}: "
        f"{payload.note}"
    )

    await db.commit()
    await db.refresh(alert)

    return alert