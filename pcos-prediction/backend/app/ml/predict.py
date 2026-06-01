"""Model loading and prediction runtime helpers."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import joblib

from app.core.config import settings
from app.ml.explainer import calculate_shap_feature_impacts
from app.ml.features import prepare_inference_frame

logger = logging.getLogger(__name__)


class PredictionEngine:
    """Load and serve the trained ensemble artifact."""

    def __init__(self, model_path: str | Path | None = None) -> None:
        self.model_path = Path(model_path or settings.resolved_model_path)
        self.artifact: dict[str, Any] | None = None
        if self.model_path.exists():
            self.load(self.model_path)
        else:
            logger.warning("Model artifact not found at %s", self.model_path)

    def load(self, model_path: str | Path) -> None:
        """Load a saved model artifact from disk."""

        self.model_path = Path(model_path)
        self.artifact = joblib.load(self.model_path)
        logger.info("Loaded model artifact from %s", self.model_path)

    @property
    def is_ready(self) -> bool:
        """Return whether a model artifact is loaded."""

        return self.artifact is not None

    def predict(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Run inference and return the scored prediction payload."""

        if not self.artifact:
            raise RuntimeError("Model artifact is not loaded.")

        raw_frame = prepare_inference_frame(payload, self.artifact["reference_stats"])
        imputer = self.artifact["imputer"]
        scaler = self.artifact["scaler"]
        transformed = scaler.transform(imputer.transform(raw_frame))

        ensemble_model = self.artifact["models"]["ensemble"]
        probability = float(ensemble_model.predict_proba(transformed)[0][1])
        explainer_model = self.artifact["models"][self.artifact["explainer_model_name"]]
        top_features = calculate_shap_feature_impacts(
            model=explainer_model,
            transformed_frame=transformed,
            raw_frame=raw_frame,
            feature_names=self.artifact["feature_columns"],
        )

        return {
            "risk_score": probability,
            "top_features": top_features,
            "model_version": self.artifact["model_version"],
            "metrics": self.artifact["metrics"],
        }

    def reload(self, model_path: str | Path) -> None:
        """Reload the active artifact."""

        self.load(model_path)


prediction_engine = PredictionEngine()
