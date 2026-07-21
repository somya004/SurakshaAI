from datetime import datetime, timezone

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.schemas import (
    MaintenanceOrder,
    Permit,
)
from app.models.permit_intelligence_model import (
    PermitMaintenanceContext,
)


ACTIVE_MAINTENANCE_STATUSES = {
    "scheduled",
    "in_progress",
    "paused",
}


async def get_active_permits(
    db: AsyncSession,
    zone_id: str,
    event_time: datetime,
) -> list[Permit]:
    """
    Returns permits active in the supplied zone and time.
    """

    result = await db.execute(
        select(Permit).where(
            and_(
                Permit.zone_id == zone_id,
                Permit.permit_status == "active",
                Permit.start_time <= event_time,
                Permit.expiry_time >= event_time,
            )
        )
    )

    return list(result.scalars().all())


async def get_active_maintenance_orders(
    db: AsyncSession,
    zone_id: str,
    event_time: datetime,
) -> list[MaintenanceOrder]:
    """
    Returns maintenance activity that can influence
    current safety conditions in the zone.
    """

    result = await db.execute(
        select(MaintenanceOrder).where(
            MaintenanceOrder.zone_id == zone_id,
            MaintenanceOrder.maintenance_status.in_(
                ACTIVE_MAINTENANCE_STATUSES
            ),
            MaintenanceOrder.scheduled_start <= event_time,
            MaintenanceOrder.scheduled_end >= event_time,
        )
    )

    return list(result.scalars().all())


def analyse_permit_and_maintenance_context(
    permits: list[Permit],
    maintenance_orders: list[MaintenanceOrder],
    gas_value: float | None,
    sparks: int | None,
    equipment_status: str | None,
) -> PermitMaintenanceContext:
    """
    Detects dangerous combinations involving permits,
    maintenance activity and current sensor conditions.
    """

    score = 0.0
    conflicts: list[str] = []
    actions: list[str] = []

    hot_work_permits = [
        permit
        for permit in permits
        if (
            permit.hot_work_flag
            or permit.permit_type.lower() == "hot_work"
        )
    ]

    confined_space_permits = [
        permit
        for permit in permits
        if (
            permit.confined_space_flag
            or permit.permit_type.lower()
            == "confined_space"
        )
    ]

    hot_work_active = len(hot_work_permits) > 0
    confined_space_active = (
        len(confined_space_permits) > 0
    )

    ventilation_unavailable = any(
    (
        "ventilation"
        in (order.equipment_id or "").lower()
        or "fan"
        in (order.equipment_id or "").lower()
    )
    and (
        order.equipment_status or ""
    ).lower()
    in {
        "unavailable",
        "failed",
        "fault",
        "offline",
    }
    for order in maintenance_orders
)

    equipment_under_maintenance = (
        len(maintenance_orders) > 0
    )

    isolation_missing = any(
        permit.isolation_required
        and not permit.isolation_confirmed
        for permit in permits
    )

    lockout_tagout_missing = any(
        order.lockout_tagout_required
        and not order.lockout_tagout_confirmed
        for order in maintenance_orders
    )

    simultaneous_operations = (
        len(permits) > 1
        or (
            len(permits) > 0
            and len(maintenance_orders) > 0
        )
    )

    # -----------------------------------------------------
    # Hot work with gas
    # -----------------------------------------------------

    if (
        hot_work_active
        and gas_value is not None
        and gas_value >= 12
    ):
        score += 40

        conflicts.append(
            "Active hot-work permit overlaps with "
            "an elevated gas condition."
        )

        actions.append(
            "Suspend hot work, remove ignition sources "
            "and repeat atmospheric testing."
        )

    # -----------------------------------------------------
    # Hot work with sparks
    # -----------------------------------------------------

    if (
        hot_work_active
        and sparks is not None
        and sparks >= 1
    ):
        score += 25

        conflicts.append(
            "Hot work is active while spark activity "
            "is being detected."
        )

        actions.append(
            "Verify fire-watch controls and stop work "
            "if ignition risk cannot be controlled."
        )

    # -----------------------------------------------------
    # Confined-space atmosphere risk
    # -----------------------------------------------------

    if (
        confined_space_active
        and gas_value is not None
        and gas_value >= 12
    ):
        score += 40

        conflicts.append(
            "A confined-space permit is active during "
            "an elevated gas condition."
        )

        actions.append(
            "Suspend confined-space entry and evacuate "
            "workers until atmospheric safety is verified."
        )

    # -----------------------------------------------------
    # Ventilation unavailable with gas
    # -----------------------------------------------------

    if (
        ventilation_unavailable
        and gas_value is not None
        and gas_value >= 12
    ):
        score += 35

        conflicts.append(
            "Ventilation equipment is unavailable while "
            "gas levels are elevated."
        )

        actions.append(
            "Restore ventilation or isolate and evacuate "
            "the affected zone."
        )

    # -----------------------------------------------------
    # Missing permit isolation
    # -----------------------------------------------------

    if isolation_missing:
        score += 30

        conflicts.append(
            "One or more active permits require isolation, "
            "but isolation is not confirmed."
        )

        actions.append(
            "Pause the related work until isolation is "
            "verified and documented."
        )

    # -----------------------------------------------------
    # Missing lockout/tagout
    # -----------------------------------------------------

    if lockout_tagout_missing:
        score += 35

        conflicts.append(
            "Maintenance requires lockout/tagout, but "
            "confirmation is missing."
        )

        actions.append(
            "Stop maintenance and confirm lockout/tagout "
            "before work continues."
        )

    # -----------------------------------------------------
    # Machine operating during maintenance
    # -----------------------------------------------------

    if (
        equipment_under_maintenance
        and equipment_status is not None
        and equipment_status.lower()
        in {
            "running",
            "operational",
            "active",
        }
    ):
        score += 25

        conflicts.append(
            "Equipment appears operational while maintenance "
            "activity is active in the zone."
        )

        actions.append(
            "Verify equipment isolation and maintenance "
            "authorization."
        )

    # -----------------------------------------------------
    # Simultaneous operations
    # -----------------------------------------------------

    if simultaneous_operations:
        score += 15

        conflicts.append(
            "Multiple operations or maintenance activities "
            "overlap in the same zone."
        )

        actions.append(
            "Perform a simultaneous-operations conflict review."
        )

    score = min(score, 100.0)

    if not conflicts:
        actions.append(
            "No current permit or maintenance conflict "
            "was detected."
        )

    return PermitMaintenanceContext(
        active_permit_count=len(permits),
        active_maintenance_count=(
            len(maintenance_orders)
        ),
        hot_work_active=hot_work_active,
        confined_space_active=(
            confined_space_active
        ),
        ventilation_unavailable=(
            ventilation_unavailable
        ),
        equipment_under_maintenance=(
            equipment_under_maintenance
        ),
        isolation_missing=isolation_missing,
        lockout_tagout_missing=(
            lockout_tagout_missing
        ),
        simultaneous_operations=(
            simultaneous_operations
        ),
        context_risk_score=score,
        detected_conflicts=conflicts,
        recommended_actions=list(
            dict.fromkeys(actions)
        ),
    )


async def build_permit_maintenance_context(
    db: AsyncSession,
    zone_id: str,
    event_time: datetime | None,
    gas_value: float | None,
    sparks: int | None,
    equipment_status: str | None,
) -> PermitMaintenanceContext:
    """
    Main function called by the compound-risk endpoint.
    """

    effective_time = (
        event_time
        or datetime.now(timezone.utc)
    )

    permits = await get_active_permits(
        db=db,
        zone_id=zone_id,
        event_time=effective_time,
    )

    maintenance_orders = (
        await get_active_maintenance_orders(
            db=db,
            zone_id=zone_id,
            event_time=effective_time,
        )
    )

    return analyse_permit_and_maintenance_context(
        permits=permits,
        maintenance_orders=maintenance_orders,
        gas_value=gas_value,
        sparks=sparks,
        equipment_status=equipment_status,
    )