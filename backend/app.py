"""
Backend server for the LB playground.

Three copies of this run (S1, S2, S3). Each one:
  - serves GET /restaurants?zip=...  (slow "database" lookup, cached in Redis)
  - reports its own stats so the dashboard can show how "full" it is
  - can be made slow or unhealthy on command (for failure scenarios later)

TODAY (Day 2 - caching): you write get_restaurants_cached() below.
"""
import asyncio
import json
import os
import random
import time

import redis.asyncio as redis
from fastapi import FastAPI, HTTPException

SERVER_ID = os.getenv("SERVER_ID", "S?")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "30"))

app = FastAPI(title=f"backend-{SERVER_ID}")
cache = redis.from_url(REDIS_URL, decode_responses=True)

# Live state the dashboard will read later
stats = {"requests": 0, "in_flight": 0, "cache_hits": 0, "cache_misses": 0}
chaos = {"extra_latency_ms": 0, "healthy": True}


# ---------------------------------------------------------------------------
# Fake "database". Postgres replaces this on Day 3.
# It is deliberately slow (~300ms) so cache hits vs misses are obvious.
# ---------------------------------------------------------------------------
async def slow_db_lookup(zip_code: str) -> list[dict]:
    await asyncio.sleep(0.3)
    random.seed(zip_code)  # same zip -> same results
    names = ["Taco Joint", "Pho House", "BBQ Pit", "Ramen Bar", "Pizza Co", "Kolache Spot"]
    return [{"name": n, "zip": zip_code, "rating": round(random.uniform(3, 5), 1)}
            for n in random.sample(names, 3)]


# ---------------------------------------------------------------------------
# YOUR CODE: cache-aside
# ---------------------------------------------------------------------------
async def get_restaurants_cached(zip_code: str) -> tuple[list[dict], bool]:
    key = f"restaurants:{zip_code}"

    # 1. Try the cache. If Redis is down, log it and fall through to the DB.
    try:
        cached = await cache.get(key)
        if cached is not None:
            stats["cache_hits"] += 1
            return json.loads(cached), True
    except Exception as e:
        print(f"{SERVER_ID} cache read failed, falling back to DB: {e}")

    # 2. Miss (or Redis down): go to the database
    data = await slow_db_lookup(zip_code)

    # 3. Try to save it. If Redis is down, skip caching. The request still succeeds.
    try:
        await cache.set(key, json.dumps(data), ex=CACHE_TTL_SECONDS)
    except Exception as e:
        print(f"{SERVER_ID} cache write failed, skipping: {e}")

    stats["cache_misses"] += 1
    return data, False


# ---------------------------------------------------------------------------
# Endpoints (done for you)
# ---------------------------------------------------------------------------
@app.get("/restaurants")
async def restaurants(zip: str = "78701"):
    if not chaos["healthy"]:
        raise HTTPException(503, "unhealthy")
    stats["requests"] += 1
    stats["in_flight"] += 1
    start = time.perf_counter()
    try:
        if chaos["extra_latency_ms"]:
            await asyncio.sleep(chaos["extra_latency_ms"] / 1000)
        data, hit = await get_restaurants_cached(zip)
        return {
            "server": SERVER_ID,
            "cache": "HIT" if hit else "MISS",
            "ms": round((time.perf_counter() - start) * 1000, 1),
            "results": data,
        }
    finally:
        stats["in_flight"] -= 1


@app.get("/health")
async def health():
    if not chaos["healthy"]:
        raise HTTPException(503, "unhealthy")
    return {"server": SERVER_ID, "ok": True}


@app.get("/stats")
async def get_stats():
    return {"server": SERVER_ID, **stats, **chaos}


# Chaos controls. The MCP server will call these on Friday.
@app.post("/admin/slow/{ms}")
async def make_slow(ms: int):
    chaos["extra_latency_ms"] = ms
    return chaos


@app.post("/admin/health/{state}")
async def set_health(state: str):
    chaos["healthy"] = state == "up"
    return chaos
