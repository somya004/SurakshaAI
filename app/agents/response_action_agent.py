from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.schemas import (
    Alert,
    Incident,
    ResponseAction,
)


def get_action_priority(
    severity: str,
) -> tuple[str, int]:
    """
    Returns action priority and completion time.
    """

    if severity == "critical":
        return "emergency", 5

    if severity == "high":
        return "urgent", 15

    return "high", 30


def normalize_text(value: str) -> str:
    return " ".join(
        value.lower().replace("_", " ").split()
    )


def determine_response_actions(
    incident: Incident,
) -> list[dict]:
    """
    Converts incident hazards into practical response actions.
    """

    combined_text = normalize_text(
        f"{incident.incident_type} "
        f"{incident.title} "
        f"{incident.description} "
        f"{incident.contributing_factors} "
        f"{incident.recommended_actions}"
    )

    priority, due_minutes = get_action_priority(
        incident.severity
    )

    actions: list[dict] = []

    def add_action(
        action_type: str,
        title: str,
        description: str,
        assigned_role: str,
        minutes: int | None = None,
    ) -> None:
        actions.append(
            {
                "action_type": action_type,
                "title": title,
                "description": description,
                "assigned_role": assigned_role,
                "priority": priority,
                "due_minutes": (
                    minutes
                    if minutes is not None
                    else due_minutes
                ),
            }
        )

    if any(
        term in combined_text
        for term in [
            "gas",
            "toxic",
            "leak",
            "flammable",
        ]
    ):
        add_action(
            action_type="isolation",
            title="Isolate the affected gas source",
            description=(
                "Stop the source when it is safe, isolate the "
                "affected line or equipment and restrict entry."
            ),
            assigned_role="maintenance_team",
        )

        add_action(
            action_type="ventilation",
            title="Activate emergency ventilation",
            description=(
                "Increase ventilation and continuously monitor "
                "gas concentration before allowing re-entry."
            ),
            assigned_role="safety_officer",
        )

    if any(
        term in combined_text
        for term in [
            "fire",
            "spark",
            "explosion",
            "hot work",
        ]
    ):
        add_action(
            action_type="ignition_control",
            title="Stop ignition and hot-work sources",
            description=(
                "Stop hot work, electrical ignition sources and "
                "other activities that may start a fire."
            ),
            assigned_role="zone_supervisor",
            minutes=5,
        )

        add_action(
            action_type="fire_response",
            title="Prepare fire-response equipment",
            description=(
                "Keep the emergency response team and suitable "
                "fire suppression equipment ready."
            ),
            assigned_role="emergency_response_team",
            minutes=5,
        )

    if any(
        term in combined_text
        for term in [
            "confined space",
            "oxygen",
            "asphyxiation",
        ]
    ):
        add_action(
            action_type="evacuation",
            title="Evacuate confined-space workers",
            description=(
                "Stop confined-space entry and safely evacuate "
                "workers using the approved rescue procedure."
            ),
            assigned_role="emergency_response_team",
            minutes=5,
        )

    if any(
        term in combined_text
        for term in [
            "vibration",
            "machine anomaly",
            "motor current",
            "overheating",
            "equipment failure",
        ]
    ):
        add_action(
            action_type="equipment_shutdown",
            title="Safely shut down affected equipment",
            description=(
                "Stop the equipment using the approved shutdown "
                "procedure and prevent unintended restart."
            ),
            assigned_role="maintenance_team",
        )

        add_action(
            action_type="inspection",
            title="Inspect equipment condition",
            description=(
                "Inspect mechanical, electrical and lubrication "
                "conditions before restoring operation."
            ),
            assigned_role="maintenance_engineer",
        )

    if any(
        term in combined_text
        for term in [
            "isolation missing",
            "lockout",
            "tagout",
            "loto",
        ]
    ):
        add_action(
            action_type="loto",
            title="Apply lockout and tagout",
            description=(
                "Isolate all hazardous energy sources and verify "
                "zero-energy state before work continues."
            ),
            assigned_role="authorized_maintenance_person",
            minutes=5,
        )

    if any(
        term in combined_text
        for term in [
            "ppe",
            "helmet",
            "glove",
            "mask",
            "unauthorized worker",
        ]
    ):
        add_action(
            action_type="worker_control",
            title="Remove unprotected workers from the zone",
            description=(
                "Restrict access until authorization and required "
                "PPE have been verified."
            ),
            assigned_role="zone_supervisor",
        )

    if incident.exposed_worker_count > 0:
        add_action(
            action_type="worker_accountability",
            title="Account for exposed workers",
            description=(
                "Confirm worker identity, condition and location, "
                "and arrange medical evaluation when required."
            ),
            assigned_role="safety_officer",
            minutes=5,
        )

    add_action(
        action_type="area_control",
        title="Secure the affected zone",
        description=(
            "Establish a safe perimeter and prevent unauthorized "
            "entry until the incident is controlled."
        ),
        assigned_role="zone_supervisor",
    )

    add_action(
        action_type="risk_verification",
        title="Verify that the hazard is controlled",
        description=(
            "Repeat sensor checks and physically verify controls "
            "before recommending incident resolution."
        ),
        assigned_role="safety_officer",
    )

    unique_actions: dict[str, dict] = {}

    for action in actions:
        unique_actions[action["action_type"]] = action

    return list(
        unique_actions.values()
    )


async def find_existing_action(
    db: AsyncSession,
    incident_id: int,
    action_type: str,
) -> ResponseAction | None:
    result = await db.execute(
        select(ResponseAction)
        .where(
            ResponseAction.incident_id == incident_id,
            ResponseAction.action_type == action_type,
            ResponseAction.status.notin_(
                {
                    "verified",
                    "cancelled",
                }
            ),
        )
        .limit(1)
    )

    return result.scalar_one_or_none()


async def create_actions_for_incident(
    db: AsyncSession,
    incident: Incident,
    alert: Alert | None = None,
) -> list[ResponseAction]:
    """
    Automatically creates non-duplicate response actions.
    """

    action_definitions = determine_response_actions(
        incident
    )

    now = datetime.now(timezone.utc)
    created_actions: list[ResponseAction] = []

    for definition in action_definitions:
        existing = await find_existing_action(
            db=db,
            incident_id=incident.id,
            action_type=definition["action_type"],
        )

        if existing is not None:
            continue

        action = ResponseAction(
            incident_id=incident.id,
            alert_id=(
                alert.id
                if alert is not None
                else None
            ),
            plant_id=incident.plant_id,
            zone_id=incident.zone_id,
            equipment_id=incident.equipment_id,
            action_type=definition["action_type"],
            title=definition["title"],
            description=definition["description"],
            priority=definition["priority"],
            status="pending",
            assigned_role=definition["assigned_role"],
            assigned_to=None,
            created_automatically=True,
            mandatory=True,
            verification_required=True,
            created_at=now,
            due_at=(
                now
                + timedelta(
                    minutes=definition["due_minutes"]
                )
            ),
            updated_at=now,
        )

        db.add(action)
        created_actions.append(action)

    await db.flush()

    return created_actions