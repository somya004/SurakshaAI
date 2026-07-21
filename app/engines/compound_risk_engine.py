from app.engines.rule_engine import evaluate_sensor_rules
from app.models.anomaly_model import MachineConditionRequest
from app.models.risk_model import (
    CompoundRiskAssessment,
    OperationalContext,
    RiskAssessment,
    RiskLevel,
    SensorReadingCreate,
)
from app.services.anomaly_model_service import (
    get_anomaly_model_service,
)
from app.services.feature_builder import (
    build_risk_model_features,
)
from app.services.risk_model_service import (
    get_risk_model_service,
)
from app.models.permit_intelligence_model import (
    PermitMaintenanceContext,
)
from app.models.worker_model import (
    WorkerExposureContext,
)


# Prototype fusion weights.
# These will later be validated and tuned using test scenarios.
RULE_WEIGHT = 0.20
ML_WEIGHT = 0.30
ANOMALY_WEIGHT = 0.15
PERMIT_MAINTENANCE_WEIGHT = 0.20
WORKER_CONTEXT_WEIGHT = 0.15

def get_risk_level(
    score: float
) -> RiskLevel:
    """
    Converts a numeric risk score into a risk category.
    """

    if score >= 81:
        return RiskLevel.critical

    if score >= 61:
        return RiskLevel.high

    if score >= 41:
        return RiskLevel.warning

    if score >= 21:
        return RiskLevel.advisory

    return RiskLevel.normal


def assess_sensor_reading(
    reading: SensorReadingCreate
) -> RiskAssessment:
    """
    Runs only the transparent rule-based assessment.
    """

    rule_result = evaluate_sensor_rules(
        reading
    )

    risk_level = get_risk_level(
        rule_result.score
    )

    explanation = (
        f"The safety rule engine detected "
        f"{len(rule_result.contributing_factors)} "
        f"contributing factor(s) in zone "
        f"{reading.zone_id}. "
        f"The rule-based score is "
        f"{rule_result.score:.2f}/100."
    )

    requires_acknowledgement = (
        risk_level
        in {
            RiskLevel.warning,
            RiskLevel.high,
            RiskLevel.critical,
        }
    )

    return RiskAssessment(
        risk_score=rule_result.score,
        risk_level=risk_level,
        predicted_event=rule_result.predicted_event,
        contributing_factors=(
            rule_result.contributing_factors
        ),
        explanation=explanation,
        recommended_action=(
            rule_result.recommended_action
        ),
        requires_acknowledgement=(
            requires_acknowledgement
        )
    )


def assess_compound_risk(
    reading: SensorReadingCreate,
    context: OperationalContext,
    machine_condition: MachineConditionRequest,
    permit_maintenance_context: PermitMaintenanceContext,
    worker_exposure_context: WorkerExposureContext,
) -> CompoundRiskAssessment:
    """
    Combines five intelligence sources:

    1. Deterministic safety rules
    2. Supervised accident-risk probability
    3. Machine anomaly score
    4. Permit and maintenance intelligence
    5. Worker exposure intelligence
    """

    # -----------------------------------------------------
    # 1. RULE ENGINE
    # -----------------------------------------------------

    rule_result = evaluate_sensor_rules(reading)

    # -----------------------------------------------------
    # 2. ACCIDENT-RISK MODEL
    # -----------------------------------------------------

    risk_model_features = build_risk_model_features(
        reading=reading,
        context=context,
    )

    risk_model_service = get_risk_model_service()

    accident_probability = (
        risk_model_service.predict_probability(
            risk_model_features
        )
    )

    ml_score = accident_probability * 100

    # -----------------------------------------------------
    # 3. MACHINE ANOMALY MODEL
    # -----------------------------------------------------

    anomaly_model_service = get_anomaly_model_service()

    anomaly_result = anomaly_model_service.predict(
        machine_condition.model_dump()
    )
    required_anomaly_fields = {
        "model_name",
        "is_anomaly",
        "raw_anomaly_score",
        "anomaly_score",
    }

    missing_fields = (
        required_anomaly_fields
        - anomaly_result.keys()
    )

    if missing_fields:
        raise ValueError(
            "Anomaly model result is missing fields: "
            + ", ".join(sorted(missing_fields))
        )

    anomaly_score = float(
        anomaly_result["anomaly_score"]
    )

    machine_is_anomaly = bool(
        anomaly_result["is_anomaly"]
    )

    # -----------------------------------------------------
    # 4. PERMIT AND MAINTENANCE INTELLIGENCE
    # -----------------------------------------------------

    permit_maintenance_score = float(
        permit_maintenance_context.context_risk_score
    )

    worker_context_score = (
    worker_exposure_context.worker_context_score
    )
    # -----------------------------------------------------
    # 5. WEIGHTED FUSION
    # -----------------------------------------------------

    final_score = (
        RULE_WEIGHT
        * rule_result.score

        + ML_WEIGHT
        * ml_score

        + ANOMALY_WEIGHT
        * anomaly_score

        + PERMIT_MAINTENANCE_WEIGHT
        * permit_maintenance_score

        + WORKER_CONTEXT_WEIGHT
        * worker_context_score
    )

    # -----------------------------------------------------
    # 6. SAFETY OVERRIDES
    # -----------------------------------------------------

    # A strong deterministic hazard must remain critical.
    if rule_result.score >= 81:
        final_score = max(final_score, 81)

    # Very high accident probability must be at least high risk.
    if accident_probability >= 0.85:
        final_score = max(final_score, 61)

    # Severe anomaly combined with elevated rule risk.
    if (
        machine_is_anomaly
        and anomaly_score >= 75
        and rule_result.score >= 41
    ):
        final_score = max(final_score, 71)

    # Hot work during elevated gas conditions.
    if (
        permit_maintenance_context.hot_work_active
        and reading.gas is not None
        and reading.gas >= 12
    ):
        final_score = max(final_score, 81)

    # Confined-space work during elevated gas conditions.
    if (
        permit_maintenance_context.confined_space_active
        and reading.gas is not None
        and reading.gas >= 12
    ):
        final_score = max(final_score, 81)

    # Missing isolation or lockout/tagout.
    if (
        permit_maintenance_context.isolation_missing
        or permit_maintenance_context.lockout_tagout_missing
    ):
        final_score = max(final_score, 61)

    # Elevated gas while ventilation is unavailable.
    if (
        permit_maintenance_context.ventilation_unavailable
        and reading.gas is not None
        and reading.gas >= 12
    ):
        final_score = max(final_score, 81)
        
    # Hazardous conditions with exposed workers must not
    # remain classified as low risk.
    if (
        worker_exposure_context.exposed_worker_count > 0
        and rule_result.score >= 61
    ):
        final_score = max(
            final_score,
            61,
        )


    # Critical environmental condition with exposed workers.
    if (
        worker_exposure_context.exposed_worker_count > 0
        and rule_result.score >= 81
    ):
        final_score = max(
            final_score,
            81,
        )


    # Unauthorised workers during high-risk permitted work.
    if (
        worker_exposure_context.unauthorized_worker_count > 0
        and (
            permit_maintenance_context.hot_work_active
            or permit_maintenance_context.confined_space_active
        )
    ):
        final_score = max(
            final_score,
            61,
        )


    # PPE violations during high-risk activity.
    if (
        worker_exposure_context.ppe_violation_count > 0
        and (
            permit_maintenance_context.hot_work_active
            or permit_maintenance_context.confined_space_active
        )
    ):
        final_score = max(
            final_score,
            61,
        )

    # Clamp only after all overrides.
    final_score = round(
        min(max(final_score, 0.0), 100.0),
        2,
    )

    # Calculate the category only after the final score is complete.
    risk_level = get_risk_level(final_score)

    # -----------------------------------------------------
    # 7. CONTRIBUTING FACTORS
    # -----------------------------------------------------

    contributing_factors = list(
        rule_result.contributing_factors
    )

    contributing_factors.append(
        "Accident-risk model probability: "
        f"{accident_probability * 100:.2f}%"
    )

    contributing_factors.append(
        "Machine anomaly score: "
        f"{anomaly_score:.2f}/100"
    )

    contributing_factors.append(
        "Permit and maintenance context score: "
        f"{permit_maintenance_score:.2f}/100"
    )
    
    contributing_factors.append(
        "Worker exposure score: "
        f"{worker_context_score:.2f}/100"
    )

    contributing_factors.extend(
        worker_exposure_context.detected_conflicts
    )

    if machine_is_anomaly:
        contributing_factors.append(
            "The equipment condition differs from "
            "learned normal machine behaviour."
        )

    contributing_factors.extend(
        permit_maintenance_context.detected_conflicts
    )

    # Remove duplicate factors while preserving order.
    contributing_factors = list(
        dict.fromkeys(contributing_factors)
    )

    # -----------------------------------------------------
    # 8. PREDICTED EVENTS
    # -----------------------------------------------------

    predicted_events = []

    if rule_result.predicted_event:
        predicted_events.append(
            rule_result.predicted_event
        )

    if machine_is_anomaly:
        predicted_events.append(
            "abnormal machine behaviour"
        )

    if permit_maintenance_context.detected_conflicts:
        predicted_events.append(
            "permit or maintenance conflict"
        )

    predicted_event = ", ".join(
        dict.fromkeys(predicted_events)
    )

    if not predicted_event:
        predicted_event = "normal operation"

    # -----------------------------------------------------
    # 9. EXPLANATION
    # -----------------------------------------------------

    explanation = (
        "The compound-risk engine combined five intelligence sources. "
        f"The rule score was {rule_result.score:.2f}/100, "
        f"the accident-model score was {ml_score:.2f}/100, "
        f"the machine anomaly score was {anomaly_score:.2f}/100, "
        f"the permit and maintenance score was {permit_maintenance_score:.2f}/100, "
        f"and the worker exposure score was {worker_context_score:.2f}/100. "
        f"The final risk score is {final_score:.2f}/100. "
        f"There are {worker_exposure_context.exposed_worker_count} "
        "worker(s) currently exposed in the zone."
    )

    # -----------------------------------------------------
    # 10. RECOMMENDED ACTIONS
    # -----------------------------------------------------

    recommended_actions: list[str] = []

    if rule_result.recommended_action:
        recommended_actions.append(
            rule_result.recommended_action
        )

    recommended_actions.extend(
        permit_maintenance_context.recommended_actions
    )

    recommended_actions.extend(
        worker_exposure_context.recommended_actions
    )

    if machine_is_anomaly:
        recommended_actions.append(
            "Inspect the equipment condition, compare it "
            "with recent operating history, and verify "
            "whether maintenance or isolation is required."
        )

    # Remove duplicate and empty actions.
    recommended_actions = list(
        dict.fromkeys(
            action
            for action in recommended_actions
            if action
        )
    )

    recommended_action = " ".join(
        recommended_actions
    )

    if not recommended_action:
        recommended_action = "Continue monitoring."

    requires_acknowledgement = (
        risk_level
        in {
            RiskLevel.warning,
            RiskLevel.high,
            RiskLevel.critical,
        }
    )

    # -----------------------------------------------------
    # 11. RESPONSE
    # -----------------------------------------------------

    return CompoundRiskAssessment(
        rule_score=round(
            rule_result.score,
            2,
        ),
        ml_probability=round(
            accident_probability,
            4,
        ),
        ml_score=round(
            ml_score,
            2,
        ),
        machine_anomaly_score=round(
            anomaly_score,
            2,
        ),
        machine_is_anomaly=machine_is_anomaly,
        permit_maintenance_score=round(
            permit_maintenance_score,
            2,
        ),
        permit_maintenance_context=(
            permit_maintenance_context
        ),
        final_risk_score=final_score,
        risk_level=risk_level,
        predicted_event=predicted_event,
        contributing_factors=contributing_factors,
        explanation=explanation,
        recommended_action=recommended_action,
        requires_acknowledgement=(
            requires_acknowledgement
        ),
        risk_model_name=(
            risk_model_service.model_name
            or "unknown_model"
        ),
        anomaly_model_name=(
            anomaly_result["model_name"]
        ),
        worker_context_score=round(
            worker_context_score,
            2,
        ),

        worker_exposure_context=(
            worker_exposure_context
        ),
    )