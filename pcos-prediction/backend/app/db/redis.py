"""Redis connection helpers."""

from __future__ import annotations

import logging

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_redis_client() -> redis.Redis:
    """Create a Redis client using the configured URL."""

    client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    logger.debug("Created Redis client for %s", settings.redis_url)
    return client
