"""
cache.py - Redis cache client (fail-open, with a circuit breaker)

Caching is a performance optimization, never a correctness dependency. If Redis is
unreachable (down, restarting, a network blip on ElastiCache), the API must keep
working - a cache outage should degrade performance, not return 500s.

Two layers of protection:

1. Fail-open: `_SafeRedis` catches `redis.RedisError` on every operation. A failed GET
   behaves like a cache miss (returns None) so the caller falls back to the database; a
   failed SET / DELETE is swallowed (the DB write already succeeded).

2. Circuit breaker: once an operation fails, Redis is marked down for a cooldown window
   and every subsequent call short-circuits instantly instead of paying the socket
   timeout again. This keeps a Redis outage from adding latency to every request, and
   is what stops the test suite (no Redis running) from spending seconds per call.

A short socket timeout means the first failure fails fast instead of hanging the request.
"""

import logging
import os
import time

import redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
# How long to stop calling Redis after a failure, in seconds.
CIRCUIT_COOLDOWN = float(os.getenv("REDIS_CIRCUIT_COOLDOWN", "30"))


class _SafeRedis:
    """Fail-open wrapper around redis.Redis with a simple circuit breaker.

    Only the operations the services use are exposed (get / set / delete). Each one
    returns a safe default on failure and trips the breaker so the next calls skip Redis.
    """

    def __init__(self, client: "redis.Redis") -> None:
        self._client = client
        self._down_until = 0.0  # monotonic timestamp; Redis is skipped until this time

    def _is_open(self) -> bool:
        """True when the breaker is tripped (Redis temporarily disabled)."""
        return time.monotonic() < self._down_until

    def _trip(self, op: str, key: str, exc: Exception) -> None:
        self._down_until = time.monotonic() + CIRCUIT_COOLDOWN
        logger.warning(
            "cache %s failed for %s; disabling cache for %.0fs: %s",
            op, key, CIRCUIT_COOLDOWN, exc,
        )

    def get(self, key: str):
        if self._is_open():
            return None
        try:
            return self._client.get(key)
        except RedisError as exc:
            self._trip("GET", key, exc)
            return None

    def set(self, key: str, value, ex: int | None = None):
        if self._is_open():
            return None
        try:
            return self._client.set(key, value, ex=ex)
        except RedisError as exc:
            self._trip("SET", key, exc)
            return None

    def delete(self, key: str):
        if self._is_open():
            return None
        try:
            return self._client.delete(key)
        except RedisError as exc:
            self._trip("DELETE", key, exc)
            return None


# socket_connect_timeout makes a down Redis fail in ~0.5s instead of hanging the request
redis_client = _SafeRedis(
    redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=0,
        decode_responses=True,
        socket_connect_timeout=0.5,
        socket_timeout=0.5,
    )
)
