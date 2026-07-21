from pydantic import BaseModel, Field


class PermitMaintenanceContext(BaseModel):
    active_permit_count: int = Field(ge=0)
    active_maintenance_count: int = Field(ge=0)

    hot_work_active: bool
    confined_space_active: bool

    ventilation_unavailable: bool
    equipment_under_maintenance: bool

    isolation_missing: bool
    lockout_tagout_missing: bool

    simultaneous_operations: bool

    context_risk_score: float = Field(
        ge=0,
        le=100
    )

    detected_conflicts: list[str]
    recommended_actions: list[str]