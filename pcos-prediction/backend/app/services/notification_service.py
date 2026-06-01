"""Notification helpers for audit-worthy events."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def send_prediction_notification(email: str, message: str) -> None:
    """Emit a log-based notification for a prediction event."""

    logger.info("Notification queued for %s: %s", email, message)
