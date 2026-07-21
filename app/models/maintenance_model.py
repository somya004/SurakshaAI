from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MaintenanceOrderCreate(BaseModel):
    work_order_id: str = Field(
        min_length=1,
        max_length=50
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

    maintenance_type: str = Field(
        min_length=1,
        max_length=50
    )

    failure_description: str | None = None

    reported_time: datetime
    scheduled_start: datetime
    scheduled_end: datetime

    actual_start: datetime | None = None
    actual_end: datetime | None = None

    maintenance_status: str = "scheduled"
    equipment_status: str = "operational"

    lockout_tagout_required: bool = False
    lockout_tagout_confirmed: bool = False

    criticality: str = "medium"

    assigned_team: str = Field(
        min_length=1,
        max_length=100
    )

    maintenance_overdue_days: int = Field(
        default=0,
        ge=0
    )

    @model_validator(mode="after")
    def validate_maintenance_order(self):
        if self.scheduled_end <= self.scheduled_start:
            raise ValueError(
                "scheduled_end must be after scheduled_start"
            )

        if (
            self.actual_end is not None
            and self.actual_start is None
        ):
            raise ValueError(
                "actual_start is required when actual_end is supplied"
            )

        if (
            self.actual_start is not None
            and self.actual_end is not None
            and self.actual_end <= self.actual_start
        ):
            raise ValueError(
                "actual_end must be after actual_start"
            )

        return self


class MaintenanceOrderResponse(
    MaintenanceOrderCreate
):
    id: int

    model_config = ConfigDict(
        from_attributes=True
    )