from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ActivePermitInput(BaseModel):
    permit_id: str
    permit_type: str
    status: str


class SensorAssessmentInput(BaseModel):
    factory: str
    region: str
    zone_id: str

    shift: Literal["day", "night"]
    workers: int = Field(ge=0)
    experience_level: Literal["junior", "senior"]
    training: Literal["yes", "no"]

    # Accident-risk model fields
    temperature: float = Field(ge=-20, le=100)
    pressure: float
    humidity: float
    vibration: float
    machine_speed: float
    equipment_age: int = Field(ge=0)
    service_days: int = Field(ge=0)
    gas: float
    sparks: int = Field(ge=0)
    alarm: Literal["on", "off"]

    # Machine-anomaly model fields
    motor_current: float
    rpm: float
    ambient_humidity: float
    tool_wear: float
    coolant_flow_rate: float
    voltage_fluctuation_percent: float
    operator_experience_years: float

    timestamp: datetime
    active_permit: ActivePermitInput | None = None
    
class PredictionResponse(BaseModel):
    model_name: str
    predicted_class: int
    predicted_event: str
    accident_probability: float


class AnomalyResponse(BaseModel):
    available: bool
    is_anomaly: bool
    raw_anomaly_score: float | None
    anomaly_component_score: float


class TriggeredRuleResponse(BaseModel):
    rule_id: str
    severity: str
    message: str


class RuleDetectionResponse(BaseModel):
    triggered: bool
    triggered_rule_count: int
    rule_score: float
    triggered_rules: list[TriggeredRuleResponse]


class PermitConflictResponse(BaseModel):
    conflict_detected: bool
    permit_id: str | None
    permit_type: str | None
    reason: str
    recommended_action: str


class WorkerExposureResponse(BaseModel):
    workers_present: int
    workers_exposed: int
    evacuation_required: bool
    training_status: str
    experience_level: str


class CompoundAssessmentResponse(BaseModel):
    ml_score: float
    anomaly_score: float
    rule_score: float
    operational_score: float
    compound_risk_score: float
    risk_level: str
    final_decision: str
    contributing_factors: list[str]


class SensorIngestionResponse(BaseModel):
    status: str
    factory: str
    region: str
    zone_id: str
    timestamp: datetime


class CommandCenterAssessmentResponse(BaseModel):
    sensor_ingestion: SensorIngestionResponse
    ml_prediction: PredictionResponse
    anomaly_detection: AnomalyResponse
    rule_detection: RuleDetectionResponse
    permit_conflict: PermitConflictResponse
    worker_exposure: WorkerExposureResponse
    compound_assessment: CompoundAssessmentResponse