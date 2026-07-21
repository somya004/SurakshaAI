import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]

METRICS_PATH = (
    PROJECT_ROOT
    / "models_artifacts"
    / "risk_model_metrics.json"
)


def load_risk_model_metrics() -> dict[str, Any]:
    if not METRICS_PATH.exists():
        return {
            "available": False,
            "model_name": None,
        }

    with METRICS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        metrics = json.load(file)

    final_metrics = metrics.get(
        "final_test_metrics",
        {},
    )

    return {
        "available": True,
        "model_name": final_metrics.get(
            "model_name",
        ),
        "accuracy": round(
            final_metrics.get("accuracy", 0) * 100,
            2,
        ),
        "precision": round(
            final_metrics.get("precision", 0) * 100,
            2,
        ),
        "recall": round(
            final_metrics.get("recall", 0) * 100,
            2,
        ),
        "f1_score": round(
            final_metrics.get("f1_score", 0) * 100,
            2,
        ),
        "roc_auc": round(
            final_metrics.get("roc_auc", 0) * 100,
            2,
        ),
        "pr_auc": round(
            final_metrics.get("pr_auc", 0) * 100,
            2,
        ),
        "false_negative_rate": round(
            final_metrics.get(
                "false_negative_rate",
                0,
            ) * 100,
            2,
        ),
        "confusion_matrix": final_metrics.get(
            "confusion_matrix",
            {},
        ),
    }