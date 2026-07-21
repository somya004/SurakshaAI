from pathlib import Path
import json

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


# ---------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"

TRAIN_DATA_PATH = (
    PROCESSED_DATA_DIR
    / "fire_risk_train.csv"
)

VALIDATION_DATA_PATH = (
    PROCESSED_DATA_DIR
    / "fire_risk_validation.csv"
)

TEST_DATA_PATH = (
    PROCESSED_DATA_DIR
    / "fire_risk_test.csv"
)

MODEL_OUTPUT_DIR = (
    BASE_DIR
    / "models_artifacts"
)

MODEL_OUTPUT_PATH = (
    MODEL_OUTPUT_DIR
    / "risk_model.joblib"
)

METRICS_OUTPUT_PATH = (
    MODEL_OUTPUT_DIR
    / "risk_model_metrics.json"
)


# ---------------------------------------------------------
# MODEL CONFIGURATION
# ---------------------------------------------------------

TARGET_COLUMN = "accident"

DROP_COLUMNS = [
    "timestamp",
]

CATEGORICAL_COLUMNS = [
    "factory",
    "region",
    "shift",
    "experience_level",
    "training",
    "alarm",
]

NUMERIC_COLUMNS = [
    "workers",
    "temperature",
    "pressure",
    "humidity",
    "vibration",
    "machine_speed",
    "equipment_age",
    "service_days",
    "gas",
    "sparks",
    "year",
    "month",
    "hour",
    "day_of_week",
]


# ---------------------------------------------------------
# DATA LOADING
# ---------------------------------------------------------

def load_dataset(
    file_path: Path,
) -> pd.DataFrame:
    if not file_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {file_path}"
        )

    dataframe = pd.read_csv(file_path)

    if TARGET_COLUMN not in dataframe.columns:
        raise ValueError(
            f"Target column '{TARGET_COLUMN}' is missing."
        )

    return dataframe


def split_features_and_target(
    dataframe: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series]:
    features = dataframe.drop(
        columns=[
            TARGET_COLUMN,
            *DROP_COLUMNS,
        ],
        errors="ignore",
    )

    target = dataframe[TARGET_COLUMN].astype(int)

    return features, target


# ---------------------------------------------------------
# PREPROCESSOR
# ---------------------------------------------------------

def build_preprocessor() -> ColumnTransformer:
    numeric_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="median"
                ),
            ),
            (
                "scaler",
                StandardScaler(),
            ),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="most_frequent"
                ),
            ),
            (
                "encoder",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=True,
                ),
            ),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                numeric_pipeline,
                NUMERIC_COLUMNS,
            ),
            (
                "categorical",
                categorical_pipeline,
                CATEGORICAL_COLUMNS,
            ),
        ],
        remainder="drop",
    )

    return preprocessor


# ---------------------------------------------------------
# MODEL BUILDERS
# ---------------------------------------------------------

def build_logistic_model() -> Pipeline:
    return Pipeline(
        steps=[
            (
                "preprocessor",
                build_preprocessor(),
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )


def build_random_forest_model() -> Pipeline:
    return Pipeline(
        steps=[
            (
                "preprocessor",
                build_preprocessor(),
            ),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=300,
                    max_depth=18,
                    min_samples_split=6,
                    min_samples_leaf=3,
                    class_weight="balanced",
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )


# ---------------------------------------------------------
# EVALUATION
# ---------------------------------------------------------

def evaluate_model(
    model_name: str,
    model: Pipeline,
    features: pd.DataFrame,
    target: pd.Series,
) -> dict:
    predictions = model.predict(features)

    probabilities = model.predict_proba(
        features
    )[:, 1]

    confusion = confusion_matrix(
        target,
        predictions,
        labels=[0, 1],
    )

    true_negative = int(confusion[0][0])
    false_positive = int(confusion[0][1])
    false_negative = int(confusion[1][0])
    true_positive = int(confusion[1][1])

    false_negative_rate = (
        false_negative
        / (false_negative + true_positive)
        if (false_negative + true_positive) > 0
        else 0.0
    )

    metrics = {
        "model_name": model_name,
        "accuracy": float(
            accuracy_score(
                target,
                predictions,
            )
        ),
        "precision": float(
            precision_score(
                target,
                predictions,
                zero_division=0,
            )
        ),
        "recall": float(
            recall_score(
                target,
                predictions,
                zero_division=0,
            )
        ),
        "f1_score": float(
            f1_score(
                target,
                predictions,
                zero_division=0,
            )
        ),
        "roc_auc": float(
            roc_auc_score(
                target,
                probabilities,
            )
        ),
        "pr_auc": float(
            average_precision_score(
                target,
                probabilities,
            )
        ),
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

    print("\n" + "=" * 60)
    print(f"MODEL: {model_name}")
    print("=" * 60)

    print(
        classification_report(
            target,
            predictions,
            zero_division=0,
        )
    )

    print(
        "False-negative rate:",
        round(false_negative_rate, 4),
    )

    print(
        "PR-AUC:",
        round(metrics["pr_auc"], 4),
    )

    print(
        "ROC-AUC:",
        round(metrics["roc_auc"], 4),
    )

    return metrics


# ---------------------------------------------------------
# MODEL SELECTION
# ---------------------------------------------------------

def select_best_model(
    candidates: list[dict],
) -> dict:
    """
    Main priority:
    1. Lowest false-negative rate
    2. Highest recall
    3. Highest PR-AUC
    """

    return min(
        candidates,
        key=lambda result: (
            result["metrics"][
                "false_negative_rate"
            ],
            -result["metrics"]["recall"],
            -result["metrics"]["pr_auc"],
        ),
    )


# ---------------------------------------------------------
# TRAINING PIPELINE
# ---------------------------------------------------------

def train_risk_models() -> None:
    MODEL_OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    train_dataframe = load_dataset(
        TRAIN_DATA_PATH
    )

    validation_dataframe = load_dataset(
        VALIDATION_DATA_PATH
    )

    test_dataframe = load_dataset(
        TEST_DATA_PATH
    )

    (
        train_features,
        train_target,
    ) = split_features_and_target(
        train_dataframe
    )

    (
        validation_features,
        validation_target,
    ) = split_features_and_target(
        validation_dataframe
    )

    (
        test_features,
        test_target,
    ) = split_features_and_target(
        test_dataframe
    )

    print(
        f"Training rows: {len(train_features)}"
    )

    print(
        f"Validation rows: "
        f"{len(validation_features)}"
    )

    print(
        f"Test rows: {len(test_features)}"
    )

    candidate_models = {
        "logistic_regression": (
            build_logistic_model()
        ),
        "random_forest": (
            build_random_forest_model()
        ),
    }

    candidate_results = []

    for model_name, model in (
        candidate_models.items()
    ):
        print(
            f"\nTraining {model_name}..."
        )

        model.fit(
            train_features,
            train_target,
        )

        validation_metrics = evaluate_model(
            model_name=model_name,
            model=model,
            features=validation_features,
            target=validation_target,
        )

        candidate_results.append({
            "name": model_name,
            "model": model,
            "metrics": validation_metrics,
        })

    best_result = select_best_model(
        candidate_results
    )

    best_model_name = best_result["name"]
    best_model = best_result["model"]

    print("\n" + "#" * 60)
    print(
        f"SELECTED MODEL: {best_model_name}"
    )
    print("#" * 60)

    combined_dataframe = pd.concat(
        [
            train_dataframe,
            validation_dataframe,
        ],
        ignore_index=True,
    )

    (
        combined_features,
        combined_target,
    ) = split_features_and_target(
        combined_dataframe
    )

    best_model.fit(
        combined_features,
        combined_target,
    )

    final_test_metrics = evaluate_model(
        model_name=best_model_name,
        model=best_model,
        features=test_features,
        target=test_target,
    )

    artifact = {
        "model": best_model,
        "model_name": best_model_name,
        "target_column": TARGET_COLUMN,
        "numeric_columns": NUMERIC_COLUMNS,
        "categorical_columns": (
            CATEGORICAL_COLUMNS
        ),
        "drop_columns": DROP_COLUMNS,
    }

    joblib.dump(
        artifact,
        MODEL_OUTPUT_PATH,
    )

    metrics_payload = {
        "selected_model": best_model_name,
        "validation_metrics": {
            result["name"]: result["metrics"]
            for result in candidate_results
        },
        "final_test_metrics": (
            final_test_metrics
        ),
    }

    with open(
        METRICS_OUTPUT_PATH,
        "w",
        encoding="utf-8",
    ) as metrics_file:
        json.dump(
            metrics_payload,
            metrics_file,
            indent=4,
        )

    print(
        f"\nSaved model to:\n"
        f"{MODEL_OUTPUT_PATH}"
    )

    print(
        f"\nSaved metrics to:\n"
        f"{METRICS_OUTPUT_PATH}"
    )


if __name__ == "__main__":
    train_risk_models()