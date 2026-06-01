"""Standalone training entrypoint for the PCOS ensemble model."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.ml.train import train_models


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


def main() -> None:
    """Parse CLI arguments and train the PCOS model ensemble."""

    parser = argparse.ArgumentParser(description="Train the PCOS prediction ensemble.")
    parser.add_argument(
        "--dataset",
        default=str(PROJECT_ROOT / "ml_pipeline" / "data" / "pcos.csv"),
        help="Path to the PCOS CSV dataset.",
    )
    parser.add_argument(
        "--output",
        default=str(PROJECT_ROOT / "backend" / "storage" / "models" / "pcos_ensemble_v1.joblib"),
        help="Destination path for the serialized model artifact.",
    )
    parser.add_argument(
        "--model-version",
        default="v1.3.0",
        help="Semantic version tag to embed in the artifact.",
    )
    args = parser.parse_args()

    logger.info("Training with dataset %s", args.dataset)
    artifact = train_models(args.dataset, args.output, model_version=args.model_version)
    logger.info("Finished training. Ensemble ROC-AUC: %.4f", artifact["metrics"]["ensemble"]["roc_auc"])


if __name__ == "__main__":
    main()
