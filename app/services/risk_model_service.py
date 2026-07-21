from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    BASE_DIR
    / "models_artifacts"
    / "risk_model.joblib"
)


class RiskModelService:
    """
    Loads the trained accident-risk model and produces
    an accident probability.

    The saved artifact contains:
    - preprocessing pipeline
    - categorical encoding
    - numeric preprocessing
    - trained classifier
    """

    def __init__(self, model_path: Path = MODEL_PATH):
        self.model_path = model_path
        self.artifact: dict[str, Any] | None = None
        self.model = None
        self.model_name: str | None = None

        self._load_model()

    def _load_model(self) -> None:
        if not self.model_path.exists():
            raise FileNotFoundError(
                "Trained risk model was not found at:\n"
                f"{self.model_path}\n"
                "Run scripts/train_risk_model.py first."
            )

        loaded_artifact = joblib.load(
            self.model_path
        )

        if not isinstance(loaded_artifact, dict):
            raise ValueError(
                "The saved risk-model artifact has an invalid format."
            )

        if "model" not in loaded_artifact:
            raise ValueError(
                "The saved artifact does not contain a 'model' key."
            )

        self.artifact = loaded_artifact
        self.model = loaded_artifact["model"]
        self.model_name = loaded_artifact.get(
            "model_name",
            "unknown_model"
        )

    def predict_probability(
        self,
        feature_values: dict[str, Any]
    ) -> float:
        """
        Returns accident probability between 0 and 1.
        """

        if self.model is None:
            raise RuntimeError(
                "Risk model has not been loaded."
            )

        feature_dataframe = pd.DataFrame(
            [feature_values]
        )

        probability = self.model.predict_proba(
            feature_dataframe
        )[0][1]

        return float(probability)


@lru_cache
def get_risk_model_service() -> RiskModelService:
    """
    Loads the model once and reuses it for later requests.
    """

    return RiskModelService()