"""Model training utilities used by the backend and standalone pipeline."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import joblib
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from app.core.config import settings
from app.ml.features import MODEL_FEATURE_COLUMNS, load_training_dataset

logger = logging.getLogger(__name__)

try:
    import mlflow
except Exception:  # pragma: no cover - import guard
    mlflow = None

try:
    from xgboost import XGBClassifier
except Exception as exc:  # pragma: no cover - import guard
    XGBClassifier = None
    XGBOOST_IMPORT_ERROR = exc
else:
    XGBOOST_IMPORT_ERROR = None


def _metrics(y_true, y_probability) -> dict[str, float]:
    """Compute the shared evaluation metrics."""

    predictions = (y_probability >= 0.5).astype(int)
    return {
        "accuracy": float(accuracy_score(y_true, predictions)),
        "precision": float(precision_score(y_true, predictions, zero_division=0)),
        "recall": float(recall_score(y_true, predictions, zero_division=0)),
        "f1": float(f1_score(y_true, predictions, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, y_probability)),
    }


def train_models(
    dataset_path: str | Path,
    output_path: str | Path,
    model_version: str = "v1.3.0",
    tracking_uri: str | None = None,
) -> dict[str, Any]:
    """Train all requested models and persist the ensemble artifact."""

    if XGBClassifier is None:
        raise RuntimeError(f"xgboost is required for training: {XGBOOST_IMPORT_ERROR}")

    logger.info("Starting model training for version %s", model_version)
    features, target, reference_stats = load_training_dataset(dataset_path)
    X_train, X_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=0.2,
        random_state=42,
        stratify=target,
    )

    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()

    X_train_imputed = imputer.fit_transform(X_train)
    X_test_imputed = imputer.transform(X_test)
    X_train_scaled = scaler.fit_transform(X_train_imputed)
    X_test_scaled = scaler.transform(X_test_imputed)

    random_forest = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42)
    xgboost = XGBClassifier(
        learning_rate=0.05,
        n_estimators=300,
        max_depth=4,
        subsample=0.9,
        colsample_bytree=0.9,
        eval_metric="logloss",
        random_state=42,
    )
    logistic_regression = LogisticRegression(max_iter=2000, random_state=42)

    random_forest.fit(X_train_scaled, y_train)
    xgboost.fit(X_train_scaled, y_train)
    logistic_regression.fit(X_train_scaled, y_train)

    ensemble = VotingClassifier(
        estimators=[
            ("random_forest", random_forest),
            ("xgboost", xgboost),
            ("logistic_regression", logistic_regression),
        ],
        voting="soft",
    )
    ensemble.fit(X_train_scaled, y_train)

    probabilities = {
        "random_forest": random_forest.predict_proba(X_test_scaled)[:, 1],
        "xgboost": xgboost.predict_proba(X_test_scaled)[:, 1],
        "logistic_regression": logistic_regression.predict_proba(X_test_scaled)[:, 1],
        "ensemble": ensemble.predict_proba(X_test_scaled)[:, 1],
    }
    metrics = {name: _metrics(y_test.to_numpy(), proba) for name, proba in probabilities.items()}
    best_model_name = max(
        ("random_forest", "xgboost", "logistic_regression"),
        key=lambda name: metrics[name]["roc_auc"],
    )
    explainer_model_name = (
        "xgboost" if metrics["xgboost"]["roc_auc"] >= metrics["random_forest"]["roc_auc"] else "random_forest"
    )

    artifact = {
        "model_version": model_version,
        "feature_columns": MODEL_FEATURE_COLUMNS,
        "imputer": imputer,
        "scaler": scaler,
        "models": {
            "random_forest": random_forest,
            "xgboost": xgboost,
            "logistic_regression": logistic_regression,
            "ensemble": ensemble,
        },
        "best_model_name": best_model_name,
        "explainer_model_name": explainer_model_name,
        "metrics": metrics,
        "reference_stats": reference_stats,
    }

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, output_file)
    logger.info("Saved trained artifact to %s", output_file)

    if mlflow is not None:
        tracking_target = tracking_uri or settings.mlflow_tracking_uri
        mlflow.set_tracking_uri(tracking_target)
        mlflow.set_experiment("pcos-prediction")
        with mlflow.start_run(run_name=model_version):
            mlflow.log_params(
                {
                    "random_forest_n_estimators": 200,
                    "random_forest_max_depth": 10,
                    "xgboost_learning_rate": 0.05,
                    "xgboost_n_estimators": 300,
                    "logistic_regression_max_iter": 2000,
                    "feature_count": len(MODEL_FEATURE_COLUMNS),
                }
            )
            for model_name, values in metrics.items():
                for metric_name, metric_value in values.items():
                    mlflow.log_metric(f"{model_name}_{metric_name}", metric_value)
            mlflow.log_artifact(str(output_file))

    return artifact
