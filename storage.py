



import asyncio
import logging
import time
from typing import Callable, Dict, List

from fastapi import Depends, HTTPException, Request

from config import RATE_LIMIT, RATE_LIMIT_WINDOW_SECONDS

queue: asyncio.Queue[str] = asyncio.Queue()
rate_limit_store: Dict[str, Dict[str, List[float]]] = {}

logger = logging.getLogger("task_app.storage")


def rate_limiter(route_key: str = "default") -> Callable:
    def _dependency(request: Request):
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        route_limits = rate_limit_store.setdefault(ip, {})
        timestamps = route_limits.setdefault(route_key, [])
        route_limits[route_key] = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW_SECONDS]

        if len(route_limits[route_key]) >= RATE_LIMIT:
            logger.warning("Rate limit exceeded for %s on %s", ip, route_key)
            raise HTTPException(status_code=429, detail="Too many requests")

        route_limits[route_key].append(now)

    return Depends(_dependency)


def global_rate_limiter(request: Request):
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    timestamps = rate_limit_store.setdefault(ip, {}).get("global", [])
    timestamps = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW_SECONDS]

    if len(timestamps) >= RATE_LIMIT:
        logger.warning("Global rate limit exceeded for %s", ip)
        raise HTTPException(status_code=429, detail="Too many requests")

    rate_limit_store.setdefault(ip, {})["global"] = timestamps + [now]

    return True
