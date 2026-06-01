"""Evaluation helper for trained PCOS model artifacts."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import joblib
from sklearn.metrics import confusion_matrix, roc_auc_score


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.ml.features import load_training_dataset


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


def main() -> None:
    """Load a saved artifact and print evaluation metrics."""

    parser = argparse.ArgumentParser(description="Evaluate the PCOS ensemble artifact.")
    parser.add_argument(
        "--dataset",
        default=str(PROJECT_ROOT / "ml_pipeline" / "data" / "pcos.csv"),
        help="Path to the PCOS CSV dataset.",
    )
    parser.add_argument(
        "--artifact",
        default=str(PROJECT_ROOT / "backend" / "storage" / "models" / "pcos_ensemble_v1.joblib"),
        help="Path to the saved joblib artifact.",
    )
    args = parser.parse_args()

    features, target, _ = load_training_dataset(args.dataset)
    artifact = joblib.load(args.artifact)
    transformed = artifact["scaler"].transform(artifact["imputer"].transform(features))
    probabilities = artifact["models"]["ensemble"].predict_proba(transformed)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)
    matrix = confusion_matrix(target, predictions)

    summary = {
        "model_version": artifact["model_version"],
        "metrics": artifact["metrics"],
        "dataset_roc_auc": float(roc_auc_score(target, probabilities)),
        "confusion_matrix": matrix.tolist(),
    }
    logger.info("Evaluation summary:\n%s", json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
