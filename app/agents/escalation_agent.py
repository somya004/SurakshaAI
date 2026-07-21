from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.alert_agent import deliver_alert
from app.database.schemas import Alert
from app.models.alert_model import (
    EscalationProcessingResult,
)


ESCALATION_RECIPIENTS = {
    "warning": {
        1: ["safety_officer"],
        2: ["plant_manager"],
    },
    "high": {
        1: ["plant_manager"],
        2: ["plant_head"],
        3: ["emergency_response_team"],
    },
    "critical": {
        1: [
            "plant_manager",
            "emergency_response_team",
        ],
        2: [
            "plant_head",
            "emergency_response_team",
        ],
        3: [
            "corporate_safety_head",
            "emergency_response_team",
        ],
    },
}


ESCALATION_DELAYS = {
    "warning": 30,
    "high": 10,
    "critical": 5,
}


def merge_pipe_values(
    existing: str,
    new_values: list[str],
) -> str:
    values = [
        value.strip()
        for value in existing.split("|")
        if value.strip()
    ]

    values.extend(new_values)

    return " | ".join(
        dict.fromkeys(values)
    )


async def process_due_escalations(
    db: AsyncSession,
) -> EscalationProcessingResult:
    """
    Escalates every due, active and unacknowledged alert.
    """

    now = datetime.now(timezone.utc)

    query = (
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
            Alert.next_escalation_at.is_not(None),
            Alert.next_escalation_at <= now,
        )
        .order_by(
            Alert.next_escalation_at.asc()
        )
    )

    result = await db.execute(query)

    due_alerts = list(
        result.scalars().all()
    )

    processed_alerts = 0
    escalated_alerts = 0
    skipped_alerts = 0
    failed_alerts = 0

    for alert in due_alerts:
        processed_alerts += 1

        if (
            alert.current_escalation_level
            >= alert.maximum_escalation_level
        ):
            alert.next_escalation_at = None
            alert.updated_at = now
            skipped_alerts += 1
            continue

        next_level = (
            alert.current_escalation_level + 1
        )

        severity_rules = ESCALATION_RECIPIENTS.get(
            alert.severity,
            {},
        )

        new_roles = severity_rules.get(
            next_level,
            [],
        )

        if not new_roles:
            alert.next_escalation_at = None
            alert.updated_at = now
            skipped_alerts += 1
            continue

        alert.current_escalation_level = (
            next_level
        )

        alert.recipient_roles = merge_pipe_values(
            alert.recipient_roles,
            new_roles,
        )

        if alert.severity in {
            "high",
            "critical",
        }:
            alert.notification_channels = (
                merge_pipe_values(
                    alert.notification_channels,
                    [
                        "email",
                        "sms",
                        "whatsapp",
                    ],
                )
            )

        success = await deliver_alert(
            db=db,
            alert=alert,
        )

        if success:
            escalated_alerts += 1
        else:
            failed_alerts += 1

        if (
            next_level
            >= alert.maximum_escalation_level
        ):
            alert.next_escalation_at = None
        else:
            delay_minutes = (
                ESCALATION_DELAYS.get(
                    alert.severity,
                    15,
                )
            )

            alert.next_escalation_at = (
                now
                + timedelta(
                    minutes=delay_minutes
                )
            )

        alert.updated_at = now

    await db.flush()

    return EscalationProcessingResult(
        processed_alerts=processed_alerts,
        escalated_alerts=escalated_alerts,
        skipped_alerts=skipped_alerts,
        failed_alerts=failed_alerts,
    )