from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_PATH = (
    BASE_DIR
    / "data"
    / "raw"
    / "industrial_iot_sensor_data.csv"
)

MODEL_DIR = BASE_DIR / "models_artifacts"

MODEL_PATH = (
    MODEL_DIR
    / "anomaly_model.joblib"
)

METRICS_PATH = (
    MODEL_DIR
    / "anomaly_model_metrics.json"
)


# ---------------------------------------------------------
# MODEL FEATURES
# ---------------------------------------------------------

FEATURE_COLUMNS = [
    "temperature",
    "vibration",
    "pressure",
    "motor_current",
    "rpm",
    "ambient_humidity",
    "tool_wear",
    "coolant_flow_rate",
    "voltage_fluctuation_percent",
    "operator_experience_years",
]

TARGET_COLUMN = "status"

NORMAL_STATUS = "normal"

ABNORMAL_STATUSES = {
    "warning",
    "failure",
}


# ---------------------------------------------------------
# DATA VALIDATION
# ---------------------------------------------------------

def load_and_validate_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            "IoT dataset not found at:\n"
            f"{DATA_PATH}"
        )

    dataframe = pd.read_csv(DATA_PATH)

    required_columns = [
        *FEATURE_COLUMNS,
        TARGET_COLUMN,
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(missing_columns)
        )

    dataframe[TARGET_COLUMN] = (
        dataframe[TARGET_COLUMN]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    valid_statuses = {
        NORMAL_STATUS,
        *ABNORMAL_STATUSES,
    }

    unknown_statuses = set(
        dataframe[TARGET_COLUMN].unique()
    ) - valid_statuses

    if unknown_statuses:
        raise ValueError(
            "Unexpected equipment status values: "
            f"{unknown_statuses}"
        )

    for column in FEATURE_COLUMNS:
        dataframe[column] = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        )

        dataframe[column] = (
            dataframe[column]
            .fillna(
                dataframe[column].median()
            )
        )

    return dataframe


# ---------------------------------------------------------
# TIME-AWARE SPLIT
# ---------------------------------------------------------

def create_time_aware_split(
    dataframe: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Uses earlier records for training and later records for testing.

    Only normal rows from the training period are used for fitting.
    The test set contains normal, warning and failure rows.
    """

    dataframe = dataframe.copy()

    dataframe["timestamp"] = pd.to_datetime(
        dataframe["timestamp"],
        errors="coerce",
    )

    dataframe = (
        dataframe
        .dropna(subset=["timestamp"])
        .sort_values("timestamp")
        .reset_index(drop=True)
    )

    split_index = int(
        len(dataframe) * 0.70
    )

    training_period = dataframe.iloc[
        :split_index
    ].copy()

    test_dataframe = dataframe.iloc[
        split_index:
    ].copy()

    normal_training_dataframe = (
        training_period[
            training_period[TARGET_COLUMN]
            == NORMAL_STATUS
        ]
        .copy()
    )

    return (
        normal_training_dataframe,
        test_dataframe,
    )


# ---------------------------------------------------------
# MODEL
# ---------------------------------------------------------

def build_anomaly_pipeline(
    contamination: float,
) -> Pipeline:
    return Pipeline(
        steps=[
            (
                "scaler",
                StandardScaler(),
            ),
            (
                "model",
                IsolationForest(
                    n_estimators=300,
                    contamination=contamination,
                    max_samples="auto",
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )


# ---------------------------------------------------------
# SCORE NORMALIZATION
# ---------------------------------------------------------

def normalize_anomaly_scores(
    raw_scores: np.ndarray,
) -> np.ndarray:
    """
    Converts Isolation Forest scores to a 0-100 anomaly score.

    Higher score means more anomalous.
    """

    minimum = raw_scores.min()
    maximum = raw_scores.max()

    if maximum == minimum:
        return np.zeros_like(
            raw_scores,
            dtype=float,
        )

    normalized = (
        raw_scores - minimum
    ) / (
        maximum - minimum
    )

    return normalized * 100


# ---------------------------------------------------------
# EVALUATION
# ---------------------------------------------------------

def evaluate_model(
    pipeline: Pipeline,
    test_dataframe: pd.DataFrame,
) -> dict:
    test_features = test_dataframe[
        FEATURE_COLUMNS
    ]

    # Isolation Forest output:
    #  1  = normal
    # -1  = anomaly
    predictions = pipeline.predict(
        test_features
    )

    predicted_labels = (
        predictions == -1
    ).astype(int)

    actual_labels = (
        test_dataframe[TARGET_COLUMN]
        .isin(ABNORMAL_STATUSES)
        .astype(int)
        .to_numpy()
    )

    confusion = confusion_matrix(
        actual_labels,
        predicted_labels,
        labels=[0, 1],
    )

    true_negative = int(confusion[0][0])
    false_positive = int(confusion[0][1])
    false_negative = int(confusion[1][0])
    true_positive = int(confusion[1][1])

    false_negative_rate = (
        false_negative
        / (
            false_negative
            + true_positive
        )
        if (
            false_negative
            + true_positive
        ) > 0
        else 0.0
    )

    precision = precision_score(
        actual_labels,
        predicted_labels,
        zero_division=0,
    )

    recall = recall_score(
        actual_labels,
        predicted_labels,
        zero_division=0,
    )

    f1 = f1_score(
        actual_labels,
        predicted_labels,
        zero_division=0,
    )

    print("\nANOMALY MODEL RESULTS")
    print("=" * 60)

    print(
        classification_report(
            actual_labels,
            predicted_labels,
            target_names=[
                "normal",
                "warning_or_failure",
            ],
            zero_division=0,
        )
    )

    print(
        "False-negative rate:",
        round(
            false_negative_rate,
            4,
        ),
    )

    return {
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "false_negative_rate": float(
            false_negative_rate
        ),
        "confusion_matrix": {
            "true_negative": true_negative,
            "false_positive": false_positive,
            "false_negative": false_negative,
            "true_positive": true_positive,
        },
    }


# TRAINING

def train_anomaly_model() -> None:
    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe = load_and_validate_data()

    print(
        f"Dataset shape: {dataframe.shape}"
    )

    print("\nStatus distribution:")
    print(
        dataframe[TARGET_COLUMN]
        .value_counts()
    )

    (
        normal_training_dataframe,
        test_dataframe,
    ) = create_time_aware_split(
        dataframe
    )

    print(
        "\nNormal training rows:",
        len(normal_training_dataframe),
    )

    print(
        "Test rows:",
        len(test_dataframe),
    )

    # The complete dataset contains about 4.3% warning/failure records.
    # This is only an initial unsupervised-model setting.
    contamination = 0.045

    pipeline = build_anomaly_pipeline(
        contamination=contamination
    )

    training_features = (
        normal_training_dataframe[
            FEATURE_COLUMNS
        ]
    )

    pipeline.fit(
        training_features
    )

    metrics = evaluate_model(
        pipeline=pipeline,
        test_dataframe=test_dataframe,
    )

    test_features = test_dataframe[
        FEATURE_COLUMNS
    ]

    raw_anomaly_scores = (
        -pipeline.decision_function(
            test_features
        )
    )

    normalized_scores = (
        normalize_anomaly_scores(
            raw_anomaly_scores
        )
    )

    score_reference = {
        "raw_score_min": float(
            raw_anomaly_scores.min()
        ),
        "raw_score_max": float(
            raw_anomaly_scores.max()
        ),
    }

    artifact = {
        "model": pipeline,
        "model_name": "isolation_forest",
        "feature_columns": FEATURE_COLUMNS,
        "normal_status": NORMAL_STATUS,
        "abnormal_statuses": list(
            ABNORMAL_STATUSES
        ),
        "contamination": contamination,
        "score_reference": score_reference,
    }

    joblib.dump(
        artifact,
        MODEL_PATH,
    )

    output_payload = {
        "model_name": "isolation_forest",
        "training_rows": len(
            normal_training_dataframe
        ),
        "test_rows": len(
            test_dataframe
        ),
        "contamination": contamination,
        "metrics": metrics,
        "test_score_summary": {
            "minimum": float(
                normalized_scores.min()
            ),
            "mean": float(
                normalized_scores.mean()
            ),
            "maximum": float(
                normalized_scores.max()
            ),
        },
    }

    with open(
        METRICS_PATH,
        "w",
        encoding="utf-8",
    ) as metrics_file:
        json.dump(
            output_payload,
            metrics_file,
            indent=4,
        )

    print(
        "\nSaved anomaly model to:\n"
        f"{MODEL_PATH}"
    )

    print(
        "\nSaved metrics to:\n"
        f"{METRICS_PATH}"
    )


if __name__ == "__main__":
    train_anomaly_model()