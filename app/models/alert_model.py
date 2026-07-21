from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class AlertSeverity(str, Enum):
    warning = "warning"
    high = "high"
    critical = "critical"


class AlertPriority(str, Enum):
    medium = "medium"
    high = "high"
    urgent = "urgent"
    emergency = "emergency"


class AlertStatus(str, Enum):
    pending = "pending"
    sent = "sent"
    acknowledged = "acknowledged"
    escalated = "escalated"
    resolved = "resolved"
    cancelled = "cancelled"


class AlertResponse(BaseModel):
    id: int

    incident_id: int | None
    risk_event_id: int | None

    plant_id: str
    zone_id: str
    equipment_id: str | None

    alert_type: str
    title: str
    message: str

    severity: str
    priority: str
    status: str

    recipient_roles: str
    notification_channels: str

    acknowledged: bool
    acknowledged_by: str | None
    acknowledgement_note: str | None

    current_escalation_level: int
    maximum_escalation_level: int

    next_escalation_at: datetime | None

    created_at: datetime
    sent_at: datetime | None
    acknowledged_at: datetime | None
    resolved_at: datetime | None
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class AlertAcknowledgementRequest(BaseModel):
    acknowledged_by: str = Field(
        min_length=2,
        max_length=100,
    )

    note: str | None = Field(
        default=None,
        max_length=1000,
    )


class AlertResolutionRequest(BaseModel):
    resolved_by: str = Field(
        min_length=2,
        max_length=100,
    )

    note: str = Field(
        min_length=3,
        max_length=2000,
    )


class AlertCreationResult(BaseModel):
    created: bool
    reason: str
    alert: AlertResponse | None = None


class EscalationProcessingResult(BaseModel):
    processed_alerts: int
    escalated_alerts: int
    skipped_alerts: int
    failed_alerts: int