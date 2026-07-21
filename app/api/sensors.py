from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.incident_agent import (
    create_or_update_incident,
)
from app.agents.permit_agent import (
    build_permit_maintenance_context,
)
from app.agents.worker_agent import (
    build_worker_exposure_context,
)
from app.database.connection import get_db
from app.database.schemas import (
    RiskEvent,
    SensorReading,
)
from app.engines.alert_engine import (
    should_create_risk_event,
)
from app.engines.compound_risk_engine import (
    assess_compound_risk,
    assess_sensor_reading,
)
from app.models.incident_model import (
    CompoundRiskProcessingResponse,
    IncidentDecisionResponse,
)
from app.models.risk_model import (
    CompoundRiskRequest,
    RiskAssessment,
    SensorReadingCreate,
    SensorReadingResponse,
)
from app.agents.worker_agent import build_worker_exposure_context


router = APIRouter(
    prefix="/sensors",
    tags=["Sensors"],
)



@router.post(
    "/readings",
    response_model=RiskAssessment,
    status_code=status.HTTP_201_CREATED,
)
async def create_sensor_reading(
    payload: SensorReadingCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Saves a sensor reading, runs the rule-based safety
    assessment, and stores a RiskEvent when the result
    is warning, high or critical.
    """

    reading = SensorReading(
        **payload.model_dump()
    )

    db.add(reading)

    assessment = assess_sensor_reading(
        payload
    )

    if should_create_risk_event(assessment):
        risk_event = RiskEvent(
            created_at=payload.timestamp,
            plant_id=payload.plant_id,
            zone_id=payload.zone_id,
            equipment_id=payload.equipment_id,
            sensor_id=payload.sensor_id,
            risk_score=assessment.risk_score,
            risk_level=assessment.risk_level.value,
            predicted_event=assessment.predicted_event,
            explanation=assessment.explanation,
            contributing_factors=" | ".join(
                assessment.contributing_factors
            ),
            recommended_action=(
                assessment.recommended_action
            ),
            requires_acknowledgement=(
                assessment.requires_acknowledgement
            ),
            acknowledged=False,
        )

        db.add(risk_event)

    await db.commit()
    await db.refresh(reading)

    return assessment


@router.get(
    "/readings",
    response_model=list[SensorReadingResponse],
)
async def list_sensor_readings(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the latest stored sensor readings.
    """

    if limit < 1 or limit > 500:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 500",
        )

    result = await db.execute(
        select(SensorReading)
        .order_by(
            SensorReading.timestamp.desc()
        )
        .limit(limit)
    )

    readings = result.scalars().all()

    return list(readings)


@router.post(
    "/assess",
    response_model=RiskAssessment,
)
async def assess_sensor_risk(
    payload: SensorReadingCreate,
):
    """
    Runs the rule-based risk assessment without
    storing the sensor reading.
    """

    return assess_sensor_reading(
        payload
    )


@router.post(
    "/assess-compound",
    response_model=CompoundRiskProcessingResponse,
)
async def assess_sensor_and_operational_risk(
    payload: CompoundRiskRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Runs the complete SurakshaAI compound-risk workflow.

    The workflow combines:

    - sensor safety rules
    - accident-risk ML model
    - machine anomaly model
    - permit and maintenance intelligence
    - worker exposure intelligence

    Warning, high and critical results are stored as
    RiskEvents. High and critical results may also
    create or update an Incident.
    """

    try:
        # -------------------------------------------------
        # 1. BUILD PERMIT AND MAINTENANCE CONTEXT
        # -------------------------------------------------

        permit_maintenance_context = (
            await build_permit_maintenance_context(
                db=db,
                zone_id=(
                    payload.sensor_reading.zone_id
                ),
                event_time=(
                    payload.sensor_reading.timestamp
                ),
                gas_value=(
                    payload.sensor_reading.gas
                ),
                sparks=(
                    payload.sensor_reading.sparks
                ),
                equipment_status=(
                    payload.sensor_reading
                    .equipment_status
                ),
            )
        )

        # -------------------------------------------------
        # 2. DETERMINE ACTIVE WORK TYPE AND REQUIRED PPE
        # -------------------------------------------------

        active_permit_type: str | None = None
        required_ppe: list[str] = []

        hot_work_active = (
            permit_maintenance_context
            .hot_work_active
        )

        confined_space_active = (
            permit_maintenance_context
            .confined_space_active
        )

        if (
            hot_work_active
            and confined_space_active
        ):
            active_permit_type = (
                "hot_work_confined_space"
            )

            required_ppe = [
                "helmet",
                "gloves",
                "goggles",
                "safety_shoes",
            ]

        elif hot_work_active:
            active_permit_type = "hot_work"

            required_ppe = [
                "helmet",
                "gloves",
                "goggles",
                "safety_shoes",
            ]

        elif confined_space_active:
            active_permit_type = (
                "confined_space"
            )

            required_ppe = [
                "helmet",
                "gloves",
                "safety_shoes",
            ]

        # -------------------------------------------------
        # 3. BUILD WORKER EXPOSURE CONTEXT
        # -------------------------------------------------

        worker_exposure_context = (
            await build_worker_exposure_context(
                db=db,
                zone_id=(
                    payload.sensor_reading.zone_id
                ),
                permit_type=active_permit_type,
                required_ppe=required_ppe,
                event_time=(
                    payload.sensor_reading.timestamp
                ),
            )
        )

        # -------------------------------------------------
        # 4. RUN COMPOUND-RISK FUSION
        # -------------------------------------------------

        assessment = assess_compound_risk(
            reading=payload.sensor_reading,
            context=payload.operational_context,
            machine_condition=(
                payload.machine_condition
            ),
            permit_maintenance_context=(
                permit_maintenance_context
            ),
            worker_exposure_context=(
                worker_exposure_context
            ),
        )

        # -------------------------------------------------
        # 5. DEFAULT RISK-EVENT AND INCIDENT RESPONSE
        # -------------------------------------------------

        risk_event_id: int | None = None

        incident_decision = IncidentDecisionResponse(
            required=False,
            created=False,
            updated_existing=False,
            reason=(
                "The compound-risk result did not "
                "require a stored risk event."
            ),
            incident=None,
        )

        # -------------------------------------------------
        # 6. STORE COMPOUND RISK EVENT
        # -------------------------------------------------

        if should_create_risk_event(assessment):
            risk_event = RiskEvent(
                created_at=(
                    payload.sensor_reading.timestamp
                ),
                plant_id=(
                    payload.sensor_reading.plant_id
                ),
                zone_id=(
                    payload.sensor_reading.zone_id
                ),
                equipment_id=(
                    payload.sensor_reading.equipment_id
                ),
                sensor_id=(
                    payload.sensor_reading.sensor_id
                ),
                risk_score=(
                    assessment.final_risk_score
                ),
                risk_level=(
                    assessment.risk_level.value
                ),
                predicted_event=(
                    assessment.predicted_event
                ),
                explanation=(
                    assessment.explanation
                ),
                contributing_factors=" | ".join(
                    assessment.contributing_factors
                ),
                recommended_action=(
                    assessment.recommended_action
                ),
                requires_acknowledgement=(
                    assessment
                    .requires_acknowledgement
                ),
                acknowledged=False,
            )

            db.add(risk_event)

            # Flush generates risk_event.id without
            # committing the transaction yet.
            await db.flush()

            risk_event_id = risk_event.id

            # ---------------------------------------------
            # 7. CREATE OR UPDATE INCIDENT
            # ---------------------------------------------

            incident_decision = (
                await create_or_update_incident(
                    db=db,
                    risk_event=risk_event,
                    reading=(
                        payload.sensor_reading
                    ),
                    assessment=assessment,
                )
            )

        # -------------------------------------------------
        # 8. COMMIT THE COMPLETE TRANSACTION
        # -------------------------------------------------

        await db.commit()

        # Refresh the incident after commit so generated
        # and updated database values are available.
        if incident_decision.incident is not None:
            await db.refresh(
                incident_decision.incident
            )

        # -------------------------------------------------
        # 9. RETURN COMPLETE PROCESSING RESULT
        # -------------------------------------------------

        return CompoundRiskProcessingResponse(
            risk_assessment=assessment,
            risk_event_id=risk_event_id,
            incident=incident_decision,
        )

    except FileNotFoundError as error:
        await db.rollback()

        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    except ValueError as error:
        await db.rollback()

        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except HTTPException:
        await db.rollback()
        raise

    except Exception as error:
        await db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Compound-risk assessment failed: "
                f"{error}"
            ),
        ) from error