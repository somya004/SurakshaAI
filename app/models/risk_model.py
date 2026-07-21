from datetime import datetime, timezone
from enum import Enum
from app.models.anomaly_model import MachineConditionRequest
from pydantic import BaseModel, ConfigDict, Field
from app.models.permit_intelligence_model import (
    PermitMaintenanceContext,
)
from app.models.worker_model import (
    WorkerExposureContext,
)

class SensorReadingCreate(BaseModel):
    """
    Validates incoming industrial sensor readings.
    """

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    plant_id: str = Field(
        min_length=1,
        max_length=50
    )

    zone_id: str = Field(
        min_length=1,
        max_length=50
    )

    equipment_id: str = Field(
        min_length=1,
        max_length=50
    )

    sensor_id: str = Field(
        min_length=1,
        max_length=50
    )

    temperature: float | None = None
    pressure: float | None = None

    humidity: float | None = Field(
        default=None,
        ge=0,
        le=100
    )

    vibration: float | None = Field(
        default=None,
        ge=0
    )

    gas: float | None = Field(
        default=None,
        ge=0
    )

    sparks: int | None = Field(
        default=None,
        ge=0
    )

    motor_current: float | None = Field(
        default=None,
        ge=0
    )

    rpm: float | None = Field(
        default=None,
        ge=0
    )

    coolant_flow_rate: float | None = Field(
        default=None,
        ge=0
    )

    equipment_status: str | None = None

    source: str = "api"


class SensorReadingResponse(SensorReadingCreate):
    """
    Response model for stored sensor readings.
    """

    id: int

    model_config = ConfigDict(
        from_attributes=True
    )


class RiskLevel(str, Enum):
    normal = "normal"
    advisory = "advisory"
    warning = "warning"
    high = "high"
    critical = "critical"


class RiskAssessment(BaseModel):
    """
    Output returned by the safety risk engine.
    """

    risk_score: float = Field(
        ge=0,
        le=100
    )

    risk_level: RiskLevel

    predicted_event: str

    contributing_factors: list[str]

    explanation: str

    recommended_action: str

    requires_acknowledgement: bool
    
class RiskEventResponse(BaseModel):
    id: int
    created_at: datetime

    plant_id: str
    zone_id: str
    equipment_id: str | None
    sensor_id: str | None

    risk_score: float
    risk_level: str
    predicted_event: str

    explanation: str
    contributing_factors: str
    recommended_action: str

    requires_acknowledgement: bool
    acknowledged: bool

    acknowledged_by: str | None
    acknowledged_at: datetime | None

    model_config = ConfigDict(
        from_attributes=True
    )


class RiskAcknowledgementRequest(BaseModel):
    acknowledged_by: str = Field(
        min_length=2,
        max_length=100
    )
    
class OperationalContext(BaseModel):
    """
    Non-sensor operational information required by
    the trained accident-risk model.

    Later, this information will be retrieved from:
    - equipment tables
    - worker tables
    - shift records
    - alarm systems
    """

    factory: str = Field(
        min_length=1,
        max_length=100
    )

    region: str = Field(
        min_length=1,
        max_length=100
    )

    shift: str = Field(
        min_length=1,
        max_length=50
    )

    workers: float = Field(
        ge=0
    )

    experience_level: str = Field(
        min_length=1,
        max_length=50
    )

    training: str = Field(
        min_length=1,
        max_length=30
    )

    machine_speed: float = Field(
        ge=0
    )

    equipment_age: float = Field(
        ge=0
    )

    service_days: float = Field(
        ge=0
    )

    alarm: str = Field(
        min_length=1,
        max_length=30
    )


class CompoundRiskRequest(BaseModel):
    """
    Complete input required for the current compound-risk engine.
    """

    sensor_reading: SensorReadingCreate
    operational_context: OperationalContext
    machine_condition: MachineConditionRequest


class MLRiskPrediction(BaseModel):
    model_name: str
    accident_probability: float = Field(
        ge=0,
        le=1
    )

    accident_probability_percent: float = Field(
        ge=0,
        le=100
    )


class CompoundRiskAssessment(BaseModel):
    """
    Combined result from:

    - rule engine
    - accident-risk model
    - machine anomaly model
    - permit and maintenance intelligence
    - worker exposure intelligence
    """

    rule_score: float = Field(
        ge=0,
        le=100,
    )

    ml_probability: float = Field(
        ge=0,
        le=1,
    )

    ml_score: float = Field(
        ge=0,
        le=100,
    )

    machine_anomaly_score: float = Field(
        ge=0,
        le=100,
    )

    machine_is_anomaly: bool

    permit_maintenance_score: float = Field(
        ge=0,
        le=100,
    )

    permit_maintenance_context: PermitMaintenanceContext

    worker_context_score: float = Field(
        ge=0,
        le=100,
    )

    worker_exposure_context: WorkerExposureContext

    final_risk_score: float = Field(
        ge=0,
        le=100,
    )

    risk_level: RiskLevel

    predicted_event: str

    contributing_factors: list[str]

    explanation: str

    recommended_action: str

    requires_acknowledgement: bool

    risk_model_name: str

    anomaly_model_name: str