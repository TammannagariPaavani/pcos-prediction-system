"""SHAP-based explanation helpers."""

from __future__ import annotations

import logging

import numpy as np

from app.ml.features import DISPLAY_NAME_MAP

logger = logging.getLogger(__name__)

try:
    import shap
except Exception:  # pragma: no cover - import guard
    shap = None


def _safe_feature_value(value) -> float:
    """Return a chart-safe numeric feature value for explanation payloads."""

    if value is None:
        return 0.0
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    if np.isnan(numeric):
        return 0.0
    return numeric


def calculate_shap_feature_impacts(
    model,
    transformed_frame,
    raw_frame,
    feature_names: list[str],
    top_k: int = 5,
) -> list[dict]:
    """Return the top SHAP feature impacts for a single prediction."""

    if shap is None:
        logger.warning("SHAP is not installed; using feature importance fallback.")
        importances = getattr(model, "feature_importances_", np.ones(len(feature_names)))
        ranked = np.argsort(np.abs(importances))[::-1][:top_k]
        return [
            {
                "feature": DISPLAY_NAME_MAP.get(feature_names[index], feature_names[index]),
                "impact": float(abs(importances[index])),
                "value": _safe_feature_value(raw_frame.iloc[0][feature_names[index]]),
            }
            for index in ranked
        ]

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(transformed_frame)
    if isinstance(shap_values, list):
        shap_values = shap_values[1]
    if getattr(shap_values, "ndim", 1) == 3:
        shap_values = shap_values[:, :, 1]

    impacts = []
    values = np.asarray(shap_values)[0]
    for index, feature_name in enumerate(feature_names):
        impacts.append(
            {
                "feature": DISPLAY_NAME_MAP.get(feature_name, feature_name),
                "impact": float(abs(values[index])),
                "value": _safe_feature_value(raw_frame.iloc[0][feature_name]),
            }
        )
    impacts.sort(key=lambda item: item["impact"], reverse=True)
    return impacts[:top_k]
