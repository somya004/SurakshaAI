from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class WorkerCreate(BaseModel):
    worker_id: str = Field(
        min_length=1,
        max_length=50,
    )

    worker_name: str = Field(
        min_length=2,
        max_length=100,
    )

    employer_name: str | None = None

    job_role: str = Field(
        min_length=2,
        max_length=100,
    )

    department: str | None = None

    experience_years: float = Field(
        default=0,
        ge=0,
    )

    safety_training_completed: bool = False

    hot_work_authorized: bool = False
    confined_space_authorized: bool = False
    electrical_work_authorized: bool = False
    work_at_height_authorized: bool = False

    training_expiry_date: datetime | None = None
    medical_clearance_valid: bool = True
    active: bool = True


class WorkerResponse(WorkerCreate):
    id: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class WorkerLocationCreate(BaseModel):
    worker_id: str
    plant_id: str
    zone_id: str

    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
    )

    location_source: str = "manual"

    entry_status: str = "inside"

    timestamp: datetime


class WorkerLocationResponse(WorkerLocationCreate):
    id: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class WorkerPPEStatusCreate(BaseModel):
    worker_id: str
    zone_id: str

    helmet_detected: bool = False
    safety_vest_detected: bool = False
    gloves_detected: bool = False
    goggles_detected: bool = False
    safety_shoes_detected: bool = False

    detection_source: str = "manual"

    confidence: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    timestamp: datetime


class WorkerPPEStatusResponse(WorkerPPEStatusCreate):
    id: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class ShiftRecordCreate(BaseModel):
    shift_id: str
    worker_id: str
    plant_id: str
    zone_id: str | None = None

    shift_name: str

    shift_start: datetime
    shift_end: datetime

    attendance_status: str = "present"

    fatigue_hours: float = Field(
        default=0,
        ge=0,
    )

    handover_completed: bool = False
    handover_notes: str | None = None

    @model_validator(mode="after")
    def validate_shift(self):
        if self.shift_end <= self.shift_start:
            raise ValueError(
                "shift_end must be after shift_start"
            )

        return self


class ShiftRecordResponse(ShiftRecordCreate):
    id: int

    model_config = ConfigDict(
        from_attributes=True,
    )
    
class ExposedWorker(BaseModel):
    worker_id: str
    worker_name: str
    job_role: str

    zone_id: str

    safety_training_completed: bool
    training_valid: bool
    medical_clearance_valid: bool

    required_work_authorized: bool

    current_shift_active: bool
    fatigue_hours: float
    handover_completed: bool

    missing_ppe: list[str]

    worker_risk_score: float = Field(
        ge=0,
        le=100,
    )

    detected_issues: list[str]


class WorkerExposureContext(BaseModel):
    zone_id: str

    exposed_worker_count: int = Field(
        ge=0,
    )

    unauthorized_worker_count: int = Field(
        ge=0,
    )

    untrained_worker_count: int = Field(
        ge=0,
    )

    ppe_violation_count: int = Field(
        ge=0,
    )

    fatigued_worker_count: int = Field(
        ge=0,
    )

    worker_context_score: float = Field(
        ge=0,
        le=100,
    )

    exposed_workers: list[ExposedWorker]

    detected_conflicts: list[str]
    recommended_actions: list[str]