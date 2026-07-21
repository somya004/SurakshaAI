from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ResponseActionStatus(str, Enum):
    pending = "pending"
    assigned = "assigned"
    in_progress = "in_progress"
    completed = "completed"
    verified = "verified"
    cancelled = "cancelled"


class ResponseActionResponse(BaseModel):
    id: int

    incident_id: int
    alert_id: int | None

    plant_id: str
    zone_id: str
    equipment_id: str | None

    action_type: str
    title: str
    description: str

    priority: str
    status: str

    assigned_role: str
    assigned_to: str | None

    created_automatically: bool
    mandatory: bool
    verification_required: bool

    completion_note: str | None
    verification_note: str | None

    completed_by: str | None
    verified_by: str | None

    created_at: datetime
    due_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    verified_at: datetime | None
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class ResponseActionCreateRequest(BaseModel):
    incident_id: int = Field(
        gt=0
    )

    action_type: str = Field(
        min_length=2,
        max_length=50
    )

    title: str = Field(
        min_length=3,
        max_length=250
    )

    description: str = Field(
        min_length=3,
        max_length=3000
    )

    priority: str = Field(
        default="high",
        pattern="^(medium|high|urgent|emergency)$"
    )

    assigned_role: str = Field(
        min_length=2,
        max_length=100
    )

    assigned_to: str | None = Field(
        default=None,
        max_length=100
    )

    mandatory: bool = True
    verification_required: bool = True
    due_minutes: int = Field(
        default=30,
        ge=1,
        le=10080
    )


class ResponseActionAssignmentRequest(BaseModel):
    assigned_to: str = Field(
        min_length=2,
        max_length=100
    )


class ResponseActionCompletionRequest(BaseModel):
    completed_by: str = Field(
        min_length=2,
        max_length=100
    )

    completion_note: str = Field(
        min_length=3,
        max_length=3000
    )


class ResponseActionVerificationRequest(BaseModel):
    verified_by: str = Field(
        min_length=2,
        max_length=100
    )

    verification_note: str = Field(
        min_length=3,
        max_length=3000
    )

    approved: bool = True