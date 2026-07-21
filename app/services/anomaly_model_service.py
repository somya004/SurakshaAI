from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    BASE_DIR
    / "models_artifacts"
    / "anomaly_model.joblib"
)


class AnomalyModelService:
    def __init__(
        self,
        model_path: Path = MODEL_PATH,
    ):
        self.model_path = model_path
        self.artifact: dict[str, Any] | None = None
        self.model = None
        self.model_name = "unknown_model"
        self.feature_columns: list[str] = []
        self.raw_score_min = 0.0
        self.raw_score_max = 1.0

        self._load_model()

    def _load_model(self) -> None:
        if not self.model_path.exists():
            raise FileNotFoundError(
                "Anomaly model not found at:\n"
                f"{self.model_path}\n"
                "Run scripts/train_anomaly_model.py first."
            )

        artifact = joblib.load(
            self.model_path
        )

        if not isinstance(
            artifact,
            dict,
        ):
            raise ValueError(
                "Invalid anomaly-model artifact."
            )

        self.artifact = artifact
        self.model = artifact["model"]
        self.model_name = artifact.get(
            "model_name",
            "isolation_forest",
        )
        self.feature_columns = artifact[
            "feature_columns"
        ]

        score_reference = artifact.get(
            "score_reference",
            {},
        )

        self.raw_score_min = float(
            score_reference.get(
                "raw_score_min",
                0.0,
            )
        )

        self.raw_score_max = float(
            score_reference.get(
                "raw_score_max",
                1.0,
            )
        )

    def _normalize_score(
        self,
        raw_score: float,
    ) -> float:
        score_range = (
            self.raw_score_max
            - self.raw_score_min
        )

        if score_range <= 0:
            return 0.0

        normalized_score = (
            raw_score
            - self.raw_score_min
        ) / score_range

        normalized_score = float(
            np.clip(
                normalized_score,
                0.0,
                1.0,
            )
        )

        return normalized_score * 100

    def predict(
        self,
        feature_values: dict[str, Any],
    ) -> dict[str, Any]:
        if self.model is None:
            raise RuntimeError(
                "Anomaly model is not loaded."
            )

        missing_features = [
            column
            for column in self.feature_columns
            if column not in feature_values
        ]

        if missing_features:
            raise ValueError(
                "Missing anomaly-model features: "
                + ", ".join(
                    missing_features
                )
            )

        feature_dataframe = pd.DataFrame(
            [
                {
                    column: feature_values[
                        column
                    ]
                    for column
                    in self.feature_columns
                }
            ]
        )

        prediction = int(
            self.model.predict(
                feature_dataframe
            )[0]
        )

        raw_score = float(
            -self.model.decision_function(
                feature_dataframe
            )[0]
        )

        anomaly_score = round(
            self._normalize_score(
                raw_score
            ),
            2,
        )

        return {
            "model_name": self.model_name,
            "is_anomaly": prediction == -1,
            "raw_anomaly_score": raw_score,
            "anomaly_score": anomaly_score,
        }


@lru_cache
def get_anomaly_model_service() -> AnomalyModelService:
    return AnomalyModelService()