from typing import Any


SEVERITY_SCORES = {
    "LOW": 25.0,
    "MEDIUM": 50.0,
    "HIGH": 75.0,
    "CRITICAL": 100.0,
}


def detect_safety_rules(
    data: dict[str, Any],
) -> dict[str, Any]:
    triggered_rules: list[dict[str, Any]] = []

    # These are configurable demonstration thresholds.
    # They are separate from the ML prediction.
    if data["gas"] >= 8 and data["sparks"] > 0:
        triggered_rules.append({
            "rule_id": "RULE-GAS-SPARK",
            "severity": "CRITICAL",
            "message": (
                "Elevated gas and sparks were detected "
                "at the same time."
            ),
        })

    if (
        data["temperature"] >= 40
        and data["alarm"] == "off"
    ):
        triggered_rules.append({
            "rule_id": "RULE-TEMP-ALARM",
            "severity": "HIGH",
            "message": (
                "High temperature was detected while "
                "the safety alarm was off."
            ),
        })

    if (
        data["vibration"] >= 5
        and data["machine_speed"] >= 3000
    ):
        triggered_rules.append({
            "rule_id": "RULE-VIBRATION-SPEED",
            "severity": "HIGH",
            "message": (
                "High vibration occurred together with "
                "excessive machine speed."
            ),
        })

    if (
        data["service_days"] >= 250
        and data["equipment_age"] >= 15
    ):
        triggered_rules.append({
            "rule_id": "RULE-SERVICE-EQUIPMENT",
            "severity": "HIGH",
            "message": (
                "Aging equipment has a long service interval."
            ),
        })

    if (
        data["training"] == "no"
        and data["experience_level"] == "junior"
    ):
        triggered_rules.append({
            "rule_id": "RULE-TRAINING-EXPERIENCE",
            "severity": "MEDIUM",
            "message": (
                "Junior workers without safety training "
                "are present."
            ),
        })

    rule_scores = [
        SEVERITY_SCORES[rule["severity"]]
        for rule in triggered_rules
    ]

    rule_score = (
        sum(rule_scores) / len(rule_scores)
        if rule_scores
        else 0.0
    )

    return {
        "triggered": bool(triggered_rules),
        "triggered_rule_count": len(triggered_rules),
        "rule_score": round(rule_score, 2),
        "triggered_rules": triggered_rules,
    }


def check_permit_conflict(
    data: dict[str, Any],
) -> dict[str, Any]:
    permit = data.get("active_permit")

    if permit is None:
        return {
            "conflict_detected": False,
            "permit_id": None,
            "permit_type": None,
            "reason": "No active permit was provided.",
            "recommended_action": (
                "No permit intervention is required."
            ),
        }

    permit_type = str(
        permit.get("permit_type", "")
    ).upper()

    permit_status = str(
        permit.get("status", "")
    ).upper()

    hazardous_condition = (
        data["gas"] >= 8
        or data["sparks"] > 0
        or data["temperature"] >= 40
    )

    conflict_detected = (
        permit_type == "HOT_WORK"
        and permit_status == "ACTIVE"
        and hazardous_condition
    )

    return {
        "conflict_detected": conflict_detected,
        "permit_id": permit.get("permit_id"),
        "permit_type": permit.get("permit_type"),
        "reason": (
            "An active hot-work permit overlaps with "
            "hazardous gas, sparks or high temperature."
            if conflict_detected
            else "No dangerous permit overlap was detected."
        ),
        "recommended_action": (
            "Suspend the hot-work permit immediately."
            if conflict_detected
            else "No permit intervention is required."
        ),
    }


def calculate_worker_exposure(
    data: dict[str, Any],
) -> dict[str, Any]:
    hazardous_condition = (
        data["gas"] >= 8
        or data["sparks"] > 0
        or data["temperature"] >= 40
        or data["vibration"] >= 5
    )

    workers_present = int(data["workers"])

    workers_exposed = (
        workers_present if hazardous_condition else 0
    )

    return {
        "workers_present": workers_present,
        "workers_exposed": workers_exposed,
        "evacuation_required": workers_exposed > 0,
        "training_status": data["training"],
        "experience_level": data["experience_level"],
    }


def calculate_compound_assessment(
    data: dict[str, Any],
    ml_result: dict[str, Any],
    anomaly_result: dict[str, Any],
    rule_result: dict[str, Any],
    permit_result: dict[str, Any],
    exposure_result: dict[str, Any],
) -> dict[str, Any]:
    ml_score = float(
        ml_result["accident_probability"]
    )

    anomaly_score = float(
        anomaly_result["anomaly_component_score"]
    )

    rule_score = float(
        rule_result["rule_score"]
    )

    operational_score = 0.0
    operational_factors: list[str] = []

    if permit_result["conflict_detected"]:
        operational_score += 35
        operational_factors.append(
            "Active hot-work permit conflict"
        )

    if exposure_result["workers_exposed"] > 0:
        operational_score += 25
        operational_factors.append(
            f'{exposure_result["workers_exposed"]} '
            "workers are exposed"
        )

    if data["alarm"] == "off":
        operational_score += 20
        operational_factors.append(
            "Safety alarm is off"
        )

    if data["training"] == "no":
        operational_score += 20
        operational_factors.append(
            "Workers do not have safety training"
        )

    operational_score = min(
        operational_score,
        100.0,
    )

    # Final compound score:
    # 60% trained ML model
    # 15% anomaly model
    # 15% triggered safety rules
    # 10% operational context
    compound_score = round(
        (0.60 * ml_score)
        + (0.15 * anomaly_score)
        + (0.15 * rule_score)
        + (0.10 * operational_score),
        2,
    )

    if compound_score >= 80:
        risk_level = "CRITICAL"
        final_decision = "STOP WORK AND EVACUATE"

    elif compound_score >= 60:
        risk_level = "HIGH"
        final_decision = (
            "SUSPEND OPERATION AND INSPECT"
        )

    elif compound_score >= 35:
        risk_level = "ALERT"
        final_decision = (
            "INCREASE MONITORING AND VERIFY CONDITIONS"
        )

    else:
        risk_level = "SAFE"
        final_decision = (
            "CONTINUE NORMAL OPERATION"
        )

    contributing_factors = [
        rule["message"]
        for rule in rule_result["triggered_rules"]
    ]

    contributing_factors.extend(
        operational_factors
    )

    return {
        "ml_score": round(ml_score, 2),
        "anomaly_score": round(anomaly_score, 2),
        "rule_score": round(rule_score, 2),
        "operational_score": round(
            operational_score,
            2,
        ),
        "compound_risk_score": compound_score,
        "risk_level": risk_level,
        "final_decision": final_decision,
        "contributing_factors":
            list(dict.fromkeys(contributing_factors)),
    }