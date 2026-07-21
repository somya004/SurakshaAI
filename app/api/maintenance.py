from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.database.schemas import MaintenanceOrder
from app.models.maintenance_model import (
    MaintenanceOrderCreate,
    MaintenanceOrderResponse,
)


router = APIRouter(
    prefix="/maintenance",
    tags=["Maintenance"]
)


@router.post(
    "",
    response_model=MaintenanceOrderResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_maintenance_order(
    payload: MaintenanceOrderCreate,
    db: AsyncSession = Depends(get_db)
):
    maintenance_order = MaintenanceOrder(
        **payload.model_dump()
    )

    db.add(maintenance_order)

    try:
        await db.commit()
        await db.refresh(maintenance_order)

    except IntegrityError as error:
        await db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "A maintenance order with this "
                "work_order_id already exists."
            )
        ) from error

    return maintenance_order


@router.get(
    "",
    response_model=list[MaintenanceOrderResponse]
)
async def list_maintenance_orders(
    limit: int = 100,
    maintenance_status: str | None = None,
    zone_id: str | None = None,
    equipment_id: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    if limit < 1 or limit > 500:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 500"
        )

    query = select(MaintenanceOrder)

    if maintenance_status is not None:
        query = query.where(
            MaintenanceOrder.maintenance_status
            == maintenance_status
        )

    if zone_id is not None:
        query = query.where(
            MaintenanceOrder.zone_id
            == zone_id
        )

    if equipment_id is not None:
        query = query.where(
            MaintenanceOrder.equipment_id
            == equipment_id
        )

    query = (
        query
        .order_by(
            MaintenanceOrder.reported_time.desc()
        )
        .limit(limit)
    )

    result = await db.execute(query)

    return list(
        result.scalars().all()
    )


@router.get(
    "/active/zone/{zone_id}",
    response_model=list[MaintenanceOrderResponse]
)
async def get_active_maintenance_by_zone(
    zone_id: str,
    db: AsyncSession = Depends(get_db)
):
    active_statuses = [
        "scheduled",
        "in_progress",
        "paused",
    ]

    result = await db.execute(
        select(MaintenanceOrder)
        .where(
            MaintenanceOrder.zone_id == zone_id,
            MaintenanceOrder.maintenance_status.in_(
                active_statuses
            ),
        )
        .order_by(
            MaintenanceOrder.reported_time.desc()
        )
    )

    return list(
        result.scalars().all()
    )


@router.patch(
    "/{work_order_id}/complete",
    response_model=MaintenanceOrderResponse
)
async def complete_maintenance_order(
    work_order_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(MaintenanceOrder).where(
            MaintenanceOrder.work_order_id
            == work_order_id
        )
    )

    maintenance_order = (
        result.scalar_one_or_none()
    )

    if maintenance_order is None:
        raise HTTPException(
            status_code=404,
            detail="Maintenance order not found"
        )

    if (
        maintenance_order.maintenance_status
        == "completed"
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Maintenance order is already completed"
            )
        )

    maintenance_order.maintenance_status = (
        "completed"
    )

    maintenance_order.equipment_status = (
        "operational"
    )

    await db.commit()
    await db.refresh(maintenance_order)

    return maintenance_order