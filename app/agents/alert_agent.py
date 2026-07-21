from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.schemas import (
    Alert,
    AlertEscalationLog,
    Incident,
)
from app.models.alert_model import (
    AlertCreationResult,
)
from app.services.notification_service import (
    send_notification,
)


ACTIVE_ALERT_STATUSES = {
    "pending",
    "sent",
    "escalated",
}


def get_alert_configuration(
    severity: str,
    exposed_worker_count: int,
) -> dict:
    """
    Returns the initial alert configuration.

    Escalation delay:
    - warning: 30 minutes
    - high: 10 minutes
    - critical: 5 minutes
    """

    if severity == "critical":
        roles = [
            "zone_supervisor",
            "safety_officer",
        ]

        channels = [
            "dashboard",
            "email",
            "sms",
        ]

        priority = "emergency"

        if exposed_worker_count > 0:
            roles.append("emergency_response_team")
            channels.append("whatsapp")

        return {
            "priority": priority,
            "roles": roles,
            "channels": channels,
            "escalation_minutes": 5,
            "maximum_level": 3,
        }

    if severity == "high":
        return {
            "priority": "urgent",
            "roles": [
                "safety_officer",
                "zone_supervisor",
            ],
            "channels": [
                "dashboard",
                "email",
            ],
            "escalation_minutes": 10,
            "maximum_level": 3,
        }

    return {
        "priority": "high",
        "roles": [
            "zone_supervisor",
        ],
        "channels": [
            "dashboard",
        ],
        "escalation_minutes": 30,
        "maximum_level": 2,
    }


async def find_active_alert(
    db: AsyncSession,
    incident_id: int,
) -> Alert | None:
    query = (
        select(Alert)
        .where(
            and_(
                Alert.incident_id == incident_id,
                Alert.status.in_(
                    ACTIVE_ALERT_STATUSES
                ),
                Alert.acknowledged.is_(False),
            )
        )
        .order_by(
            Alert.created_at.desc()
        )
        .limit(1)
    )

    result = await db.execute(query)

    return result.scalar_one_or_none()


async def deliver_alert(
    db: AsyncSession,
    alert: Alert,
) -> bool:
    """
    Delivers an alert through all configured channels
    and records delivery attempts.
    """

    roles = [
        value.strip()
        for value in alert.recipient_roles.split("|")
        if value.strip()
    ]

    channels = [
        value.strip()
        for value in alert.notification_channels.split("|")
        if value.strip()
    ]

    any_success = False

    for role in roles:
        for channel in channels:
            result = await send_notification(
                channel=channel,
                recipient_role=role,
                title=alert.title,
                message=alert.message,
            )

            if result.success:
                any_success = True

            delivery_log = AlertEscalationLog(
                alert_id=alert.id,
                escalation_level=(
                    alert.current_escalation_level
                ),
                recipient_roles=role,
                notification_channels=channel,
                delivery_status=(
                    "sent"
                    if result.success
                    else "failed"
                ),
                delivery_message=result.message,
                attempted_at=datetime.now(
                    timezone.utc
                ),
            )

            db.add(delivery_log)

    now = datetime.now(timezone.utc)

    if any_success:
        alert.status = (
            "sent"
            if alert.current_escalation_level == 0
            else "escalated"
        )
        alert.sent_at = now
    else:
        alert.status = "pending"

    alert.updated_at = now

    await db.flush()

    return any_success


async def create_alert_for_incident(
    db: AsyncSession,
    incident: Incident,
) -> AlertCreationResult:
    """
    Creates and delivers an alert for an incident.

    Duplicate active alerts for the same incident are not created.
    """

    existing_alert = await find_active_alert(
        db=db,
        incident_id=incident.id,
    )

    if existing_alert is not None:
        return AlertCreationResult(
            created=False,
            reason=(
                "An active unacknowledged alert already "
                "exists for this incident."
            ),
            alert=existing_alert,
        )

    configuration = get_alert_configuration(
        severity=incident.severity,
        exposed_worker_count=(
            incident.exposed_worker_count
        ),
    )

    now = datetime.now(timezone.utc)

    alert = Alert(
        incident_id=incident.id,
        risk_event_id=incident.risk_event_id,
        plant_id=incident.plant_id,
        zone_id=incident.zone_id,
        equipment_id=incident.equipment_id,
        alert_type=incident.incident_type,
        title=f"Safety Alert: {incident.title}"[:250],
        message=(
            f"{incident.description}\n\n"
            f"Recommended actions: "
            f"{incident.recommended_actions}"
        ),
        severity=incident.severity,
        priority=configuration["priority"],
        status="pending",
        recipient_roles=" | ".join(
            configuration["roles"]
        ),
        notification_channels=" | ".join(
            dict.fromkeys(
                configuration["channels"]
            )
        ),
        acknowledged=False,
        current_escalation_level=0,
        maximum_escalation_level=(
            configuration["maximum_level"]
        ),
        next_escalation_at=(
            now
            + timedelta(
                minutes=configuration[
                    "escalation_minutes"
                ]
            )
        ),
        created_at=now,
        updated_at=now,
    )

    db.add(alert)
    await db.flush()

    await deliver_alert(
        db=db,
        alert=alert,
    )

    return AlertCreationResult(
        created=True,
        reason="Alert created and delivery initiated.",
        alert=alert,
    )