from typing import Any

from app.models.risk_model import (
    OperationalContext,
    SensorReadingCreate,
)


def require_sensor_value(
    value: float | int | None,
    field_name: str
) -> float:
    """
    Prevents the ML model from silently receiving made-up values.
    """

    if value is None:
        raise ValueError(
            f"'{field_name}' is required for ML risk prediction."
        )

    return float(value)


def build_risk_model_features(
    reading: SensorReadingCreate,
    context: OperationalContext
) -> dict[str, Any]:
    """
    Converts sensor and operational information into the
    exact feature structure used during model training.
    """

    timestamp = reading.timestamp

    return {
        "factory": context.factory.strip(),
        "region": context.region.strip(),
        "shift": context.shift.strip().lower(),
        "workers": context.workers,
        "experience_level": (
            context.experience_level
            .strip()
            .lower()
        ),
        "training": (
            context.training
            .strip()
            .lower()
        ),
        "temperature": require_sensor_value(
            reading.temperature,
            "temperature"
        ),
        "pressure": require_sensor_value(
            reading.pressure,
            "pressure"
        ),
        "humidity": require_sensor_value(
            reading.humidity,
            "humidity"
        ),
        "vibration": require_sensor_value(
            reading.vibration,
            "vibration"
        ),
        "machine_speed": context.machine_speed,
        "equipment_age": context.equipment_age,
        "service_days": context.service_days,
        "gas": require_sensor_value(
            reading.gas,
            "gas"
        ),
        "sparks": require_sensor_value(
            reading.sparks,
            "sparks"
        ),
        "alarm": context.alarm.strip().lower(),
        "year": timestamp.year,
        "month": timestamp.month,
        "hour": timestamp.hour,
        "day_of_week": timestamp.weekday(),
    }