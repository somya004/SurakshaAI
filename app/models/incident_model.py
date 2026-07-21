from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.risk_model import CompoundRiskAssessment


class IncidentResponse(BaseModel):
    id: int
    risk_event_id: int | None

    plant_id: str
    zone_id: str
    equipment_id: str | None
    sensor_id: str | None

    incident_type: str
    title: str
    description: str

    severity: str
    status: str
    final_risk_score: float

    contributing_factors: str
    recommended_actions: str

    exposed_worker_count: int
    event_count: int

    assigned_to: str | None
    acknowledged_by: str | None
    acknowledgement_note: str | None

    resolution_notes: str | None
    corrective_actions: str | None

    escalation_level: int

    created_at: datetime
    latest_event_at: datetime
    updated_at: datetime

    acknowledged_at: datetime | None
    resolved_at: datetime | None
    closed_at: datetime | None

    model_config = ConfigDict(
        from_attributes=True
    )


class IncidentAcknowledgementRequest(BaseModel):
    acknowledged_by: str = Field(
        min_length=2,
        max_length=100,
    )

    note: str | None = Field(
        default=None,
        max_length=1000,
    )


class IncidentAssignmentRequest(BaseModel):
    assigned_to: str = Field(
        min_length=2,
        max_length=100,
    )


class IncidentStatusNoteRequest(BaseModel):
    note: str | None = Field(
        default=None,
        max_length=2000,
    )


class IncidentResolutionRequest(BaseModel):
    resolution_notes: str = Field(
        min_length=3,
        max_length=3000,
    )

    corrective_actions: str | None = Field(
        default=None,
        max_length=3000,
    )


class IncidentDecisionResponse(BaseModel):
    required: bool
    created: bool
    updated_existing: bool
    reason: str
    incident: IncidentResponse | None = None


class CompoundRiskProcessingResponse(BaseModel):
    risk_assessment: CompoundRiskAssessment
    risk_event_id: int | None = None
    incident: IncidentDecisionResponse