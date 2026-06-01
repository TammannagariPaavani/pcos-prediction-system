"""Common API schema definitions."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """Base schema configured for SQLAlchemy object parsing."""

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """Standardized error response body."""

    error: str
    code: str
