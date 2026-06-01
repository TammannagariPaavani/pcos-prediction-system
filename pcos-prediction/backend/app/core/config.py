"""Runtime configuration for the backend service."""

from __future__ import annotations

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed application settings."""

    project_name: str = "PCOS Prediction System"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False
    environment: str = "development"
    frontend_url: str = "http://localhost:3000"
    cookie_secure: bool = False
    rate_limit_requests_per_minute: int = 120

    database_url: str = "sqlite:///./pcos_dev.db"
    redis_url: str = "redis://localhost:6379/0"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"

    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket_reports: str = "pcos-reports"
    minio_secure: bool = False

    mlflow_tracking_uri: str = "file:./backend/storage/mlruns"
    model_path: str = "backend/storage/models/pcos_ensemble_v1.joblib"
    model_version: str = "v1.3.0"

    report_storage_path: str = "backend/storage/reports"
    model_storage_path: str = "backend/storage/models"
    celery_task_soft_time_limit: int = 60

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str | None) -> str:
        """Fallback to a local SQLite database when the placeholder URL is still present."""

        if value is None:
            return "sqlite:///./pcos_dev.db"
        normalized = value.strip()
        if not normalized or normalized == "postgresql://user:pass@localhost:5432/pcos_db":
            return "sqlite:///./pcos_dev.db"
        return normalized

    @property
    def project_root(self) -> Path:
        """Return the absolute project root directory."""

        return Path(__file__).resolve().parents[3]

    @property
    def backend_root(self) -> Path:
        """Return the backend root directory."""

        return Path(__file__).resolve().parents[2]

    @property
    def resolved_model_path(self) -> Path:
        """Return the absolute model artifact path."""

        return self.project_root / self.model_path

    @property
    def resolved_report_storage_path(self) -> Path:
        """Return the absolute report storage directory."""

        return self.project_root / self.report_storage_path

    @property
    def resolved_model_storage_path(self) -> Path:
        """Return the absolute model storage directory."""

        return self.project_root / self.model_storage_path


settings = Settings()
