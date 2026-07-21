from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RISK_MODEL_PATH = PROJECT_ROOT / "models_artifacts" / "risk_model.joblib"


@lru_cache
def get_risk_model_bundle() -> dict[str, Any]:
    if not RISK_MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Risk model not found: {RISK_MODEL_PATH}. "
            "Run scripts/train_risk_model.py or restore the trained artifact."
        )

    bundle = joblib.load(RISK_MODEL_PATH)
    if not isinstance(bundle, dict) or "model" not in bundle:
        raise ValueError(
            "risk_model.joblib must be a dictionary containing a 'model' key."
        )
    if "numeric_columns" not in bundle or "categorical_columns" not in bundle:
        raise ValueError(
            "risk_model.joblib is missing numeric_columns or categorical_columns."
        )
    return bundle


def prepare_risk_features(payload: dict[str, Any]) -> pd.DataFrame:
    bundle = get_risk_model_bundle()
    model_features = list(bundle["numeric_columns"]) + list(
        bundle["categorical_columns"]
    )
    prepared = payload.copy()

    timestamp = pd.Timestamp(prepared["timestamp"])
    prepared["year"] = int(timestamp.year)
    prepared["month"] = int(timestamp.month)
    prepared["hour"] = int(timestamp.hour)
    prepared["day_of_week"] = int(timestamp.dayofweek)

    missing_features = [
        feature for feature in model_features if feature not in prepared
    ]
    if missing_features:
        raise ValueError(
            "Missing risk-model features: " + ", ".join(missing_features)
        )

    return pd.DataFrame(
        [{feature: prepared[feature] for feature in model_features}],
        columns=model_features,
    )


def predict_accident_risk(payload: dict[str, Any]) -> dict[str, Any]:
    bundle = get_risk_model_bundle()
    model = bundle["model"]
    model_input = prepare_risk_features(payload)

    if not hasattr(model, "predict_proba"):
        raise ValueError("The risk model does not support predict_proba().")

    predicted_class = int(model.predict(model_input)[0])
    probabilities = model.predict_proba(model_input)[0]
    model_classes = list(model.classes_)
    if 1 not in model_classes:
        raise ValueError("Accident class 1 is missing from the model classes.")

    raw_probability = float(probabilities[model_classes.index(1)])
    probability_percentage = raw_probability * 100

    return {
        "model_name": bundle.get("model_name", "logistic_regression"),
        "predicted_class": predicted_class,
        "predicted_event": (
            "Accident Risk" if predicted_class == 1 else "Safe Condition"
        ),
        "raw_accident_probability": raw_probability,
        "accident_probability": round(probability_percentage, 6),
        "display_probability": (
            ">99.99%"
            if probability_percentage >= 99.995
            else f"{probability_percentage:.2f}%"
        ),
    }
