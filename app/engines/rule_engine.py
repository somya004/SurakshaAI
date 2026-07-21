from dataclasses import dataclass

from app.models.risk_model import SensorReadingCreate


@dataclass
class RuleResult:
    score: float
    predicted_event: str
    contributing_factors: list[str]
    recommended_action: str


def evaluate_sensor_rules(
    reading: SensorReadingCreate
) -> RuleResult:
    """
    Evaluates prototype industrial safety rules.

    These thresholds are demonstration values only.
    Later they will come from configurable plant-specific rules.
    """

    score = 0.0
    factors: list[str] = []
    events: list[str] = []
    actions: list[str] = []

    # Gas risk
    if reading.gas is not None:
        if reading.gas >= 20:
            score += 35
            factors.append(
                f"Critical gas reading detected: {reading.gas}"
            )
            events.append("hazardous gas accumulation")
            actions.append(
                "Suspend work and verify atmospheric conditions."
            )

        elif reading.gas >= 12:
            score += 20
            factors.append(
                f"Elevated gas reading detected: {reading.gas}"
            )
            events.append("developing gas hazard")
            actions.append(
                "Inspect the zone and increase monitoring."
            )

    # Temperature risk
    if reading.temperature is not None:
        if reading.temperature >= 80:
            score += 25
            factors.append(
                f"Critical temperature detected: {reading.temperature}"
            )
            events.append("equipment overheating")
            actions.append(
                "Inspect equipment and cooling systems."
            )

        elif reading.temperature >= 65:
            score += 12
            factors.append(
                f"Elevated temperature detected: {reading.temperature}"
            )

    # Vibration risk
    if reading.vibration is not None:
        if reading.vibration >= 4:
            score += 20
            factors.append(
                f"Critical vibration detected: {reading.vibration}"
            )
            events.append("mechanical instability")
            actions.append(
                "Inspect rotating equipment before continued operation."
            )

        elif reading.vibration >= 3:
            score += 10
            factors.append(
                f"Elevated vibration detected: {reading.vibration}"
            )

    # Spark or ignition source
    if reading.sparks is not None and reading.sparks >= 3:
        score += 25
        factors.append(
            f"Repeated spark events detected: {reading.sparks}"
        )
        events.append("ignition-source activity")
        actions.append(
            "Stop hot work or isolate the ignition source."
        )

    # Cooling problem
    if (
        reading.coolant_flow_rate is not None
        and reading.coolant_flow_rate < 0.7
    ):
        score += 15
        factors.append(
            f"Low coolant flow detected: "
            f"{reading.coolant_flow_rate}"
        )
        events.append("cooling degradation")
        actions.append(
            "Check coolant pump and supply."
        )

    # Equipment status
    if (
        reading.equipment_status
        and reading.equipment_status.lower()
        in {"fault", "critical", "failed"}
    ):
        score += 30
        factors.append(
            f"Equipment status is {reading.equipment_status}"
        )
        events.append("equipment fault")
        actions.append(
            "Isolate equipment and notify maintenance."
        )

    # First compound rule
    if (
        reading.gas is not None
        and reading.gas >= 12
        and reading.sparks is not None
        and reading.sparks >= 1
    ):
        score += 25

        factors.append(
            "Compound condition detected: elevated gas "
            "and an ignition source are present together."
        )

        events.append(
            "fire or explosion risk"
        )

        actions.append(
            "Suspend ignition-producing work, isolate the area "
            "and assess evacuation need."
        )

    score = min(score, 100.0)

    if not factors:
        return RuleResult(
            score=5.0,
            predicted_event="normal operation",
            contributing_factors=[
                "No configured safety threshold was exceeded."
            ],
            recommended_action="Continue monitoring."
        )

    unique_events = list(dict.fromkeys(events))
    unique_actions = list(dict.fromkeys(actions))

    return RuleResult(
        score=score,
        predicted_event=", ".join(unique_events),
        contributing_factors=factors,
        recommended_action=" ".join(unique_actions)
    )