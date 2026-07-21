from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.database.schemas import RiskEvent
from app.models.risk_model import (
    RiskAcknowledgementRequest,
    RiskEventResponse,
)


router = APIRouter(
    prefix="/risks",
    tags=["Risks"]
)


@router.get(
    "",
    response_model=list[RiskEventResponse]
)
async def list_risk_events(
    limit: int = 100,
    risk_level: str | None = None,
    acknowledged: bool | None = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns stored warning, high and critical risk events.
    """

    if limit < 1 or limit > 500:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 500"
        )

    query = select(RiskEvent)

    if risk_level is not None:
        allowed_levels = {
            "warning",
            "high",
            "critical",
        }

        if risk_level not in allowed_levels:
            raise HTTPException(
                status_code=400,
                detail=(
                    "risk_level must be warning, high or critical"
                )
            )

        query = query.where(
            RiskEvent.risk_level == risk_level
        )

    if acknowledged is not None:
        query = query.where(
            RiskEvent.acknowledged == acknowledged
        )

    query = (
        query
        .order_by(RiskEvent.created_at.desc())
        .limit(limit)
    )

    result = await db.execute(query)

    return list(
        result.scalars().all()
    )


@router.get(
    "/{risk_event_id}",
    response_model=RiskEventResponse
)
async def get_risk_event(
    risk_event_id: int,
    db: AsyncSession = Depends(get_db)
):
    risk_event = await db.get(
        RiskEvent,
        risk_event_id
    )

    if risk_event is None:
        raise HTTPException(
            status_code=404,
            detail="Risk event not found"
        )

    return risk_event


@router.patch(
    "/{risk_event_id}/acknowledge",
    response_model=RiskEventResponse
)
async def acknowledge_risk_event(
    risk_event_id: int,
    payload: RiskAcknowledgementRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Allows a safety supervisor to acknowledge a risk event.
    """

    risk_event = await db.get(
        RiskEvent,
        risk_event_id
    )

    if risk_event is None:
        raise HTTPException(
            status_code=404,
            detail="Risk event not found"
        )

    if risk_event.acknowledged:
        raise HTTPException(
            status_code=409,
            detail="Risk event is already acknowledged"
        )

    risk_event.acknowledged = True
    risk_event.acknowledged_by = payload.acknowledged_by
    risk_event.acknowledged_at = datetime.now(
        timezone.utc
    )

    await db.commit()
    await db.refresh(risk_event)

    return risk_event