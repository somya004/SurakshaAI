from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.database.schemas import (
    ShiftRecord,
    Worker,
    WorkerLocation,
    WorkerPPEStatus,
)
from app.models.worker_model import (
    ShiftRecordCreate,
    ShiftRecordResponse,
    WorkerCreate,
    WorkerLocationCreate,
    WorkerLocationResponse,
    WorkerPPEStatusCreate,
    WorkerPPEStatusResponse,
    WorkerResponse,
)


router = APIRouter(
    prefix="/workers",
    tags=["Workers"],
)


# ---------------------------------------------------------
# Common worker validation
# ---------------------------------------------------------

async def get_worker_or_404(
    db: AsyncSession,
    worker_id: str,
) -> Worker:
    """
    Find an active worker using worker_id.

    Raises:
        404: Worker does not exist.
        409: Worker exists but is inactive.
    """

    result = await db.execute(
        select(Worker).where(
            Worker.worker_id == worker_id
        )
    )

    worker = result.scalar_one_or_none()

    if worker is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker not found",
        )

    if not worker.active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Worker is inactive",
        )

    return worker


# ---------------------------------------------------------
# Worker endpoints
# ---------------------------------------------------------

@router.post(
    "",
    response_model=WorkerResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_worker(
    payload: WorkerCreate,
    db: AsyncSession = Depends(get_db),
):
    worker = Worker(
        **payload.model_dump()
    )

    db.add(worker)

    try:
        await db.commit()
        await db.refresh(worker)

    except IntegrityError as error:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A worker with this worker_id "
                "already exists."
            ),
        ) from error

    return worker


@router.get(
    "",
    response_model=list[WorkerResponse],
)
async def list_workers(
    active: bool | None = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    if limit < 1 or limit > 500:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="limit must be between 1 and 500",
        )

    query = select(Worker)

    if active is not None:
        query = query.where(
            Worker.active == active
        )

    query = (
        query
        .order_by(Worker.worker_name)
        .limit(limit)
    )

    result = await db.execute(query)

    return list(result.scalars().all())


@router.get(
    "/{worker_id}",
    response_model=WorkerResponse,
)
async def get_worker(
    worker_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Worker).where(
            Worker.worker_id == worker_id
        )
    )

    worker = result.scalar_one_or_none()

    if worker is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker not found",
        )

    return worker


# ---------------------------------------------------------
# Worker location endpoints
# ---------------------------------------------------------

@router.post(
    "/locations",
    response_model=WorkerLocationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_worker_location(
    payload: WorkerLocationCreate,
    db: AsyncSession = Depends(get_db),
):
    await get_worker_or_404(
        db=db,
        worker_id=payload.worker_id,
    )

    location = WorkerLocation(
        **payload.model_dump()
    )

    db.add(location)

    try:
        await db.commit()
        await db.refresh(location)

    except IntegrityError as error:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to create worker location record.",
        ) from error

    return location


@router.get(
    "/locations/zone/{zone_id}",
    response_model=list[WorkerLocationResponse],
)
async def get_worker_locations_by_zone(
    zone_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Return workers whose latest location record shows that
    they are currently inside the requested zone.

    The latest location is checked across all zones so that
    a worker who moved or exited is not counted incorrectly.
    """

    result = await db.execute(
        select(WorkerLocation)
        .order_by(
            WorkerLocation.worker_id,
            WorkerLocation.timestamp.desc(),
        )
    )

    locations = list(
        result.scalars().all()
    )

    latest_locations: dict[str, WorkerLocation] = {}

    for location in locations:
        if location.worker_id not in latest_locations:
            latest_locations[location.worker_id] = location

    workers_inside_zone = [
        location
        for location in latest_locations.values()
        if (
            location.zone_id == zone_id
            and (
                location.entry_status or ""
            ).strip().lower() == "inside"
        )
    ]

    return workers_inside_zone


@router.get(
    "/locations/worker/{worker_id}",
    response_model=WorkerLocationResponse,
)
async def get_latest_worker_location(
    worker_id: str,
    db: AsyncSession = Depends(get_db),
):
    await get_worker_or_404(
        db=db,
        worker_id=worker_id,
    )

    result = await db.execute(
        select(WorkerLocation)
        .where(
            WorkerLocation.worker_id == worker_id
        )
        .order_by(
            WorkerLocation.timestamp.desc()
        )
        .limit(1)
    )

    location = result.scalar_one_or_none()

    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No location record found for this worker",
        )

    return location


# ---------------------------------------------------------
# Worker PPE endpoints
# ---------------------------------------------------------

@router.post(
    "/ppe-status",
    response_model=WorkerPPEStatusResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_worker_ppe_status(
    payload: WorkerPPEStatusCreate,
    db: AsyncSession = Depends(get_db),
):
    await get_worker_or_404(
        db=db,
        worker_id=payload.worker_id,
    )

    ppe_status = WorkerPPEStatus(
        **payload.model_dump()
    )

    db.add(ppe_status)

    try:
        await db.commit()
        await db.refresh(ppe_status)

    except IntegrityError as error:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to create worker PPE status.",
        ) from error

    return ppe_status


@router.get(
    "/ppe-status/{worker_id}",
    response_model=WorkerPPEStatusResponse,
)
async def get_latest_worker_ppe_status(
    worker_id: str,
    zone_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    await get_worker_or_404(
        db=db,
        worker_id=worker_id,
    )

    query = select(WorkerPPEStatus).where(
        WorkerPPEStatus.worker_id == worker_id
    )

    if zone_id is not None:
        query = query.where(
            WorkerPPEStatus.zone_id == zone_id
        )

    query = (
        query
        .order_by(
            WorkerPPEStatus.timestamp.desc()
        )
        .limit(1)
    )

    result = await db.execute(query)

    ppe_status = result.scalar_one_or_none()

    if ppe_status is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No PPE status found for this worker",
        )

    return ppe_status


# ---------------------------------------------------------
# Worker shift endpoints
# ---------------------------------------------------------

@router.post(
    "/shifts",
    response_model=ShiftRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_shift_record(
    payload: ShiftRecordCreate,
    db: AsyncSession = Depends(get_db),
):
    await get_worker_or_404(
        db=db,
        worker_id=payload.worker_id,
    )

    shift_record = ShiftRecord(
        **payload.model_dump()
    )

    db.add(shift_record)

    try:
        await db.commit()
        await db.refresh(shift_record)

    except IntegrityError as error:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A shift with this shift_id "
                "already exists."
            ),
        ) from error

    return shift_record


@router.get(
    "/shifts/{worker_id}",
    response_model=list[ShiftRecordResponse],
)
async def list_worker_shifts(
    worker_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    await get_worker_or_404(
        db=db,
        worker_id=worker_id,
    )

    if limit < 1 or limit > 500:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="limit must be between 1 and 500",
        )

    result = await db.execute(
        select(ShiftRecord)
        .where(
            ShiftRecord.worker_id == worker_id
        )
        .order_by(
            ShiftRecord.shift_start.desc()
        )
        .limit(limit)
    )

    return list(result.scalars().all())