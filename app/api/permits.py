from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.database.schemas import Permit
from app.models.permit_model import (
    PermitCreate,
    PermitResponse,
)


router = APIRouter(
    prefix="/permits",
    tags=["Permits"]
)


@router.post(
    "",
    response_model=PermitResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_permit(
    payload: PermitCreate,
    db: AsyncSession = Depends(get_db)
):
    permit = Permit(
        **payload.model_dump()
    )

    db.add(permit)

    try:
        await db.commit()
        await db.refresh(permit)

    except IntegrityError as error:
        await db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "A permit with this permit_id "
                "already exists."
            )
        ) from error

    return permit


@router.get(
    "",
    response_model=list[PermitResponse]
)
async def list_permits(
    limit: int = 100,
    permit_status: str | None = None,
    zone_id: str | None = None,
    permit_type: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    if limit < 1 or limit > 500:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 500"
        )

    query = select(Permit)

    if permit_status is not None:
        query = query.where(
            Permit.permit_status == permit_status
        )

    if zone_id is not None:
        query = query.where(
            Permit.zone_id == zone_id
        )

    if permit_type is not None:
        query = query.where(
            Permit.permit_type == permit_type
        )

    query = (
        query
        .order_by(Permit.start_time.desc())
        .limit(limit)
    )

    result = await db.execute(query)

    return list(
        result.scalars().all()
    )


@router.get(
    "/active/{zone_id}",
    response_model=list[PermitResponse]
)
async def get_active_permits_for_zone(
    zone_id: str,
    db: AsyncSession = Depends(get_db)
):
    current_time = datetime.now(
        timezone.utc
    )

    result = await db.execute(
        select(Permit)
        .where(
            and_(
                Permit.zone_id == zone_id,
                Permit.permit_status == "active",
                Permit.start_time <= current_time,
                Permit.expiry_time >= current_time,
            )
        )
        .order_by(Permit.start_time.desc())
    )

    return list(
        result.scalars().all()
    )


@router.patch(
    "/{permit_id}/close",
    response_model=PermitResponse
)
async def close_permit(
    permit_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Permit).where(
            Permit.permit_id == permit_id
        )
    )

    permit = result.scalar_one_or_none()

    if permit is None:
        raise HTTPException(
            status_code=404,
            detail="Permit not found"
        )

    if permit.permit_status in {
        "closed",
        "cancelled",
    }:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Permit is already "
                f"{permit.permit_status}"
            ),
        )

    permit.permit_status = "closed"

    await db.commit()
    await db.refresh(permit)

    return permit