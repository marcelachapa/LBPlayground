# LB Playground

A load balancer I'm building from scratch in Python to understand how traffic, caching, databases, and scaling actually behave. It has L4 and L7 modes, pluggable algorithms, a live dashboard, and an MCP server so an AI can trigger traffic spikes and failures.

## Build plan

| Day | Topic | What gets built |
| --- | --- | --- |
| Tue | Caching | 3 FastAPI backends + Redis cache-aside |
| Wed | Databases | Postgres, GET reads / POST writes, index with `EXPLAIN` |
| Thu | Scaling | L7 proxy (my code), round robin, GET vs POST routing |
| Fri | APIs / networking | L4 proxy (my code), least connections, health checks |
| Sat | Visuals | Live dashboard: per-server fill bars, request log, the 900-request demo |
| Sun | AI | MCP server: `set_mode`, `spike`, `kill_server`, `slow_server`, `get_stats` |
| Mon | Ship | Rate limiting, DNS round robin, deploy, write-up |

## Run it

```bash
docker compose up --build
```

- S1: http://localhost:8001/restaurants?zip=78701
- S2: http://localhost:8002/restaurants?zip=78701
- S3: http://localhost:8003/restaurants?zip=78701
- Stats: http://localhost:8001/stats

## Day 2 task

Write `get_restaurants_cached()` in `backend/app.py`, rebuild, then:

```bash
pip install httpx
python loadgen/cache_test.py
```

Done when the first call MISSes at ~300ms and repeats HIT in a few ms, across all three servers.

## Chaos controls

```bash
curl -X POST localhost:8001/admin/slow/2000   # S1 adds 2s latency
curl -X POST localhost:8001/admin/slow/0      # back to normal
curl -X POST localhost:8002/admin/health/down # S2 fails health checks
curl -X POST localhost:8002/admin/health/up
```
