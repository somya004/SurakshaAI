from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.database.schemas import PlantZone
from app.models.plant_zone_schema import (
    PlantZoneCreate,
    PlantZoneResponse,
    PlantZoneUpdate,
)


router = APIRouter(
    prefix="/plant-zones",
    tags=["Plant Zones"],
)


@router.post(
    "",
    response_model=PlantZoneResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_plant_zone(
    payload: PlantZoneCreate,
    db: AsyncSession = Depends(get_db),
):
    plant_zone = PlantZone(
        **payload.model_dump()
    )

    db.add(plant_zone)

    try:
        await db.commit()
        await db.refresh(plant_zone)

    except IntegrityError as error:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A zone with this plant_id and "
                "zone_id already exists."
            ),
        ) from error

    return plant_zone


@router.get(
    "",
    response_model=list[PlantZoneResponse],
)
async def list_plant_zones(
    plant_id: str | None = None,
    zone_type: str | None = None,
    floor_level: int | None = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    if limit < 1 or limit > 500:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="limit must be between 1 and 500",
        )

    query = select(PlantZone)

    if plant_id is not None:
        query = query.where(
            PlantZone.plant_id == plant_id
        )

    if zone_type is not None:
        query = query.where(
            PlantZone.zone_type == zone_type
        )

    if floor_level is not None:
        query = query.where(
            PlantZone.floor_level == floor_level
        )

    query = (
        query
        .order_by(
            PlantZone.plant_id,
            PlantZone.floor_level,
            PlantZone.zone_name,
        )
        .limit(limit)
    )

    result = await db.execute(query)

    return list(result.scalars().all())


@router.get(
    "/{plant_id}/{zone_id}",
    response_model=PlantZoneResponse,
)
async def get_plant_zone(
    plant_id: str,
    zone_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PlantZone).where(
            PlantZone.plant_id == plant_id,
            PlantZone.zone_id == zone_id,
        )
    )

    plant_zone = result.scalar_one_or_none()

    if plant_zone is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant zone not found",
        )

    return plant_zone


@router.put(
    "/{plant_id}/{zone_id}",
    response_model=PlantZoneResponse,
)
async def update_plant_zone(
    plant_id: str,
    zone_id: str,
    payload: PlantZoneUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PlantZone).where(
            PlantZone.plant_id == plant_id,
            PlantZone.zone_id == zone_id,
        )
    )

    plant_zone = result.scalar_one_or_none()

    if plant_zone is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant zone not found",
        )

    update_data = payload.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(
            plant_zone,
            field,
            value,
        )

    await db.commit()
    await db.refresh(plant_zone)

    return plant_zone


@router.delete(
    "/{plant_id}/{zone_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_plant_zone(
    plant_id: str,
    zone_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PlantZone).where(
            PlantZone.plant_id == plant_id,
            PlantZone.zone_id == zone_id,
        )
    )

    plant_zone = result.scalar_one_or_none()

    if plant_zone is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant zone not found",
        )

    await db.delete(plant_zone)
    await db.commit()