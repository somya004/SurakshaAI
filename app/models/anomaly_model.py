from pydantic import BaseModel, Field


class MachineConditionRequest(BaseModel):
    temperature: float
    vibration: float = Field(ge=0)
    pressure: float
    motor_current: float = Field(ge=0)
    rpm: float = Field(ge=0)
    ambient_humidity: float = Field(
        ge=0,
        le=100,
    )
    tool_wear: float = Field(ge=0)
    coolant_flow_rate: float = Field(ge=0)
    voltage_fluctuation_percent: float
    operator_experience_years: float = Field(
        ge=0
    )


class MachineAnomalyAssessment(BaseModel):
    model_name: str
    is_anomaly: bool
    raw_anomaly_score: float
    anomaly_score: float = Field(
        ge=0,
        le=100,
    )