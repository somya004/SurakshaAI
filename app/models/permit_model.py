from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PermitCreate(BaseModel):
    permit_id: str = Field(min_length=1, max_length=50)
    plant_id: str = Field(min_length=1, max_length=50)
    zone_id: str = Field(min_length=1, max_length=50)

    equipment_id: str | None = None

    permit_type: str = Field(min_length=1, max_length=50)
    work_description: str = Field(min_length=3)

    issue_time: datetime
    start_time: datetime
    expiry_time: datetime

    permit_status: str = "active"

    issuer_id: str
    approver_id: str

    contractor_name: str | None = None

    worker_count: int = Field(default=0, ge=0)

    gas_test_required: bool = False
    gas_test_value: float | None = None

    isolation_required: bool = False
    isolation_confirmed: bool = False

    ppe_required: str | None = None

    hot_work_flag: bool = False
    confined_space_flag: bool = False

    risk_level: str = "medium"

    @model_validator(mode="after")
    def validate_permit(self):
        if self.expiry_time <= self.start_time:
            raise ValueError(
                "expiry_time must be after start_time"
            )

        if (
            self.isolation_required
            and not self.isolation_confirmed
            and self.permit_status.lower() == "active"
        ):
            raise ValueError(
                "An active permit requiring isolation "
                "must have isolation_confirmed=true"
            )

        if (
            self.gas_test_required
            and self.gas_test_value is None
        ):
            raise ValueError(
                "gas_test_value is required when "
                "gas_test_required=true"
            )

        return self


class PermitResponse(PermitCreate):
    id: int

    model_config = ConfigDict(
        from_attributes=True
    )