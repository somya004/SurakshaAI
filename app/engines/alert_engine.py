from app.models.risk_model import (
    CompoundRiskAssessment,
    RiskAssessment,
    RiskLevel,
)


def should_create_risk_event(
    assessment: RiskAssessment | CompoundRiskAssessment,
) -> bool:
    """
    Warning, high and critical assessments are stored
    as risk events.

    Normal and advisory assessments are not stored.
    """

    return assessment.risk_level in {
        RiskLevel.warning,
        RiskLevel.high,
        RiskLevel.critical,
    }