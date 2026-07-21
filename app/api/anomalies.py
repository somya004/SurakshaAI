from fastapi import APIRouter, HTTPException

from app.models.anomaly_model import (
    MachineAnomalyAssessment,
    MachineConditionRequest,
)
from app.services.anomaly_model_service import (
    get_anomaly_model_service,
)


router = APIRouter(
    prefix="/anomalies",
    tags=["Machine Anomalies"],
)


@router.post(
    "/assess",
    response_model=MachineAnomalyAssessment,
)
async def assess_machine_anomaly(
    payload: MachineConditionRequest,
):
    try:
        service = (
            get_anomaly_model_service()
        )

        result = service.predict(
            payload.model_dump()
        )

        return MachineAnomalyAssessment(
            **result
        )

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "Machine anomaly assessment failed: "
                f"{error}"
            ),
        ) from error