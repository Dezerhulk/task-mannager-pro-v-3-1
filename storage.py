



import asyncio
import logging
import os
import sqlite3
import time
from typing import Callable, Dict, List
from uuid import uuid4

from fastapi import Depends, HTTPException, Request

from config import QUEUE_DB_PATH, RATE_LIMIT, RATE_LIMIT_BACKEND, RATE_LIMIT_WINDOW_SECONDS, REDIS_URL

logger = logging.getLogger("task_app.storage")


class PersistentQueue:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._condition = asyncio.Condition()
        self._current_item: str | None = None
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS queue_items (id TEXT PRIMARY KEY, state TEXT NOT NULL, created_at REAL NOT NULL)"
            )
            conn.execute("UPDATE queue_items SET state='pending' WHERE state='processing'")
            conn.commit()

    async def put(self, item: str) -> None:
        async with self._condition:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR IGNORE INTO queue_items (id, state, created_at) VALUES (?, 'pending', ?)",
                    (item, time.time()),
                )
                conn.commit()
            self._condition.notify_all()

    async def get(self) -> str:
        async with self._condition:
            while True:
                with sqlite3.connect(self.db_path) as conn:
                    row = conn.execute(
                        "SELECT id FROM queue_items WHERE state='pending' ORDER BY created_at ASC, id ASC LIMIT 1"
                    ).fetchone()
                    if row is not None:
                        self._current_item = row[0]
                        conn.execute("UPDATE queue_items SET state='processing' WHERE id=?", (row[0],))
                        conn.commit()
                        return row[0]
                await self._condition.wait()

    async def task_done(self) -> None:
        async with self._condition:
            with sqlite3.connect(self.db_path) as conn:
                if self._current_item is not None:
                    conn.execute("DELETE FROM queue_items WHERE id=?", (self._current_item,))
                    self._current_item = None
                conn.commit()
            self._condition.notify_all()


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, List[float]]] = {}

    def allow(self, key: str, route_key: str, window_seconds: int, limit: int) -> bool:
        now = time.time()
        route_limits = self._store.setdefault(key, {})
        timestamps = route_limits.setdefault(route_key, [])
        route_limits[route_key] = [t for t in timestamps if now - t < window_seconds]

        if len(route_limits[route_key]) >= limit:
            return False

        route_limits[route_key].append(now)
        return True


class RedisRateLimiter:
    def __init__(self, redis_url: str) -> None:
        try:
            import redis  # type: ignore
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise RuntimeError("redis package is required for Redis rate limiting") from exc

        self._client = redis.Redis.from_url(redis_url, decode_responses=False)
        self._client.ping()

    def allow(self, key: str, route_key: str, window_seconds: int, limit: int) -> bool:
        now = int(time.time())
        item_id = f"{now}-{uuid4().hex}"
        bucket_key = f"ratelimit:{key}:{route_key}"
        pipeline = self._client.pipeline()
        pipeline.zremrangebyscore(bucket_key, 0, now - window_seconds)
        pipeline.zcard(bucket_key)
        pipeline.zadd(bucket_key, {item_id: now})
        pipeline.expire(bucket_key, window_seconds)
        _, current_count, _, _ = pipeline.execute()
        return int(current_count) < limit


queue = PersistentQueue(QUEUE_DB_PATH)

if RATE_LIMIT_BACKEND == "redis" and REDIS_URL:
    rate_limiter_backend = RedisRateLimiter(REDIS_URL)
else:
    rate_limiter_backend = InMemoryRateLimiter()


def rate_limiter(route_key: str = "default") -> Callable:
    def _dependency(request: Request):
        ip = request.client.host if request.client else "unknown"
        allowed = rate_limiter_backend.allow(ip, route_key, RATE_LIMIT_WINDOW_SECONDS, RATE_LIMIT)

        if not allowed:
            logger.warning("Rate limit exceeded for %s on %s", ip, route_key)
            raise HTTPException(status_code=429, detail="Too many requests")

    return Depends(_dependency)


def global_rate_limiter(request: Request):
    ip = request.client.host if request.client else "unknown"
    allowed = rate_limiter_backend.allow(ip, "global", RATE_LIMIT_WINDOW_SECONDS, RATE_LIMIT)

    if not allowed:
        logger.warning("Global rate limit exceeded for %s", ip)
        raise HTTPException(status_code=429, detail="Too many requests")

    return True
