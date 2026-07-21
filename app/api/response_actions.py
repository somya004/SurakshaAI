from datetime import datetime, timedelta, timezone

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
from app.models.response_action_model import (
    ResponseActionAssignmentRequest,
    ResponseActionCompletionRequest,
    ResponseActionCreateRequest,
    ResponseActionResponse,
    ResponseActionVerificationRequest,
)


router = APIRouter(
    prefix="/response-actions",
    tags=["Emergency Response Actions"],
)


async def get_action_or_404(
    action_id: int,
    db: AsyncSession,
) -> ResponseAction:
    action = await db.get(
        ResponseAction,
        action_id,
    )

    if action is None:
        raise HTTPException(
            status_code=404,
            detail="Response action not found",
        )

    return action


@router.get(
    "",
    response_model=list[ResponseActionResponse],
)
async def list_response_actions(
    incident_id: int | None = None,
    status: str | None = None,
    priority: str | None = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    if limit < 1 or limit > 500:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 500",
        )

    query = select(ResponseAction)

    if incident_id is not None:
        query = query.where(
            ResponseAction.incident_id == incident_id
        )

    if status is not None:
        query = query.where(
            ResponseAction.status == status
        )

    if priority is not None:
        query = query.where(
            ResponseAction.priority == priority
        )

    result = await db.execute(
        query
        .order_by(
            ResponseAction.due_at.asc()
        )
        .limit(limit)
    )

    return list(
        result.scalars().all()
    )


@router.get(
    "/overdue",
    response_model=list[ResponseActionResponse],
)
async def list_overdue_actions(
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(ResponseAction)
        .where(
            ResponseAction.due_at < now,
            ResponseAction.status.in_(
                {
                    "pending",
                    "assigned",
                    "in_progress",
                }
            ),
        )
        .order_by(
            ResponseAction.due_at.asc()
        )
    )

    return list(
        result.scalars().all()
    )


@router.post(
    "",
    response_model=ResponseActionResponse,
)
async def create_manual_response_action(
    payload: ResponseActionCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    incident = await db.get(
        Incident,
        payload.incident_id,
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    now = datetime.now(timezone.utc)

    action = ResponseAction(
        incident_id=incident.id,
        alert_id=None,
        plant_id=incident.plant_id,
        zone_id=incident.zone_id,
        equipment_id=incident.equipment_id,
        action_type=payload.action_type,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        status=(
            "assigned"
            if payload.assigned_to
            else "pending"
        ),
        assigned_role=payload.assigned_role,
        assigned_to=payload.assigned_to,
        created_automatically=False,
        mandatory=payload.mandatory,
        verification_required=(
            payload.verification_required
        ),
        created_at=now,
        due_at=(
            now
            + timedelta(
                minutes=payload.due_minutes
            )
        ),
        updated_at=now,
    )

    db.add(action)

    await db.commit()
    await db.refresh(action)

    return action


@router.get(
    "/{action_id}",
    response_model=ResponseActionResponse,
)
async def get_response_action(
    action_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await get_action_or_404(
        action_id,
        db,
    )


@router.patch(
    "/{action_id}/assign",
    response_model=ResponseActionResponse,
)
async def assign_response_action(
    action_id: int,
    payload: ResponseActionAssignmentRequest,
    db: AsyncSession = Depends(get_db),
):
    action = await get_action_or_404(
        action_id,
        db,
    )

    if action.status in {
        "completed",
        "verified",
        "cancelled",
    }:
        raise HTTPException(
            status_code=409,
            detail="This action can no longer be assigned",
        )

    action.assigned_to = payload.assigned_to
    action.status = "assigned"
    action.updated_at = datetime.now(
        timezone.utc
    )

    await db.commit()
    await db.refresh(action)

    return action


@router.patch(
    "/{action_id}/start",
    response_model=ResponseActionResponse,
)
async def start_response_action(
    action_id: int,
    db: AsyncSession = Depends(get_db),
):
    action = await get_action_or_404(
        action_id,
        db,
    )

    if action.status not in {
        "pending",
        "assigned",
    }:
        raise HTTPException(
            status_code=409,
            detail="Only pending or assigned actions can be started",
        )

    now = datetime.now(timezone.utc)

    action.status = "in_progress"
    action.started_at = now
    action.updated_at = now

    await db.commit()
    await db.refresh(action)

    return action


@router.patch(
    "/{action_id}/complete",
    response_model=ResponseActionResponse,
)
async def complete_response_action(
    action_id: int,
    payload: ResponseActionCompletionRequest,
    db: AsyncSession = Depends(get_db),
):
    action = await get_action_or_404(
        action_id,
        db,
    )

    if action.status not in {
        "assigned",
        "in_progress",
    }:
        raise HTTPException(
            status_code=409,
            detail=(
                "Only assigned or in-progress actions "
                "can be completed"
            ),
        )

    now = datetime.now(timezone.utc)

    action.completed_by = payload.completed_by
    action.completion_note = payload.completion_note
    action.completed_at = now
    action.updated_at = now

    if action.verification_required:
        action.status = "completed"
    else:
        action.status = "verified"
        action.verified_by = payload.completed_by
        action.verified_at = now
        action.verification_note = (
            "Verification was not required."
        )

    await db.commit()
    await db.refresh(action)

    return action


@router.patch(
    "/{action_id}/verify",
    response_model=ResponseActionResponse,
)
async def verify_response_action(
    action_id: int,
    payload: ResponseActionVerificationRequest,
    db: AsyncSession = Depends(get_db),
):
    action = await get_action_or_404(
        action_id,
        db,
    )

    if action.status != "completed":
        raise HTTPException(
            status_code=409,
            detail="Only completed actions can be verified",
        )

    now = datetime.now(timezone.utc)

    action.verified_by = payload.verified_by
    action.verification_note = (
        payload.verification_note
    )
    action.updated_at = now

    if payload.approved:
        action.status = "verified"
        action.verified_at = now
    else:
        action.status = "in_progress"
        action.completed_at = None
        action.completed_by = None

    await db.commit()
    await db.refresh(action)

    return action