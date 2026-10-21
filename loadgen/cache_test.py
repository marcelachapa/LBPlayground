"""
Day 2 test: prove your cache works.

Run:  python loadgen/cache_test.py
Needs: pip install httpx

Expected once cache-aside works:
  - first request for a zip  -> MISS, ~300ms
  - repeat requests          -> HIT,  a few ms
  - same zip on S2/S3        -> HIT  (they share one Redis, so the cache is shared)
"""
import httpx

SERVERS = ["http://localhost:8001", "http://localhost:8002", "http://localhost:8003"]

with httpx.Client(timeout=5) as client:
    print("Same zip, same server, 3 times:")
    for _ in range(3):
        r = client.get(f"{SERVERS[0]}/restaurants", params={"zip": "78704"}).json()
        print(f"  {r['server']}  {r['cache']:4}  {r['ms']:>7} ms")

    print("\nSame zip, the other two servers:")
    for base in SERVERS[1:]:
        r = client.get(f"{base}/restaurants", params={"zip": "78704"}).json()
        print(f"  {r['server']}  {r['cache']:4}  {r['ms']:>7} ms")

    print("\nNew zip (should MISS once, then HIT):")
    for _ in range(2):
        r = client.get(f"{SERVERS[2]}/restaurants", params={"zip": "78745"}).json()
        print(f"  {r['server']}  {r['cache']:4}  {r['ms']:>7} ms")
