#!/usr/bin/env python3
"""
Standalone load tester for the FROMO API — measures per-endpoint latency
(p50 / p95 / p99) and throughput under concurrent load.

Stdlib only (no dependencies to install). Run against a local or deployed API.

Usage:
    python load_test.py                              # defaults to the deployed API
    python load_test.py http://localhost:8000
    python load_test.py https://fromo.onrender.com --requests 200 --concurrency 20
"""
import argparse
import json
import ssl
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from statistics import mean

# Use certifi's CA bundle if available (matches app/core/security.py), so HTTPS
# verification works regardless of the system trust store.
try:
    import certifi
    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    _SSL_CTX = ssl.create_default_context()


def hit(url: str) -> tuple[float, int]:
    """Fire one request; return (latency_ms, status_code)."""
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=30, context=_SSL_CTX) as r:
            r.read()
            code = r.status
    except urllib.error.HTTPError as e:
        code = e.code
    except Exception:
        code = 0
    return (time.perf_counter() - t0) * 1000, code


def percentile(sorted_vals: list[float], p: float) -> float:
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * p
    lo = int(k)
    hi = min(lo + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)


def bench(url: str, n: int, concurrency: int) -> dict:
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        wall0 = time.perf_counter()
        results = list(ex.map(lambda _: hit(url), range(n)))
        wall = time.perf_counter() - wall0
    lat = sorted(r[0] for r in results)
    errors = sum(1 for _, code in results if code >= 400 or code == 0)
    return {
        "p50": percentile(lat, 0.50),
        "p95": percentile(lat, 0.95),
        "p99": percentile(lat, 0.99),
        "max": lat[-1],
        "mean": mean(lat),
        "rps": n / wall if wall else 0.0,
        "errors": errors,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="FROMO API load test")
    ap.add_argument("base", nargs="?", default="https://fromo.onrender.com",
                    help="Base URL of the API")
    ap.add_argument("--requests", type=int, default=200, help="requests per endpoint")
    ap.add_argument("--concurrency", type=int, default=20, help="concurrent workers")
    args = ap.parse_args()
    base = args.base.rstrip("/")

    # Discover one real event id for the detail endpoint.
    event_id = None
    try:
        with urllib.request.urlopen(f"{base}/events/?limit=1", timeout=30, context=_SSL_CTX) as r:
            data = json.load(r)
            event_id = data[0]["event"]["id"]
    except Exception:
        pass

    endpoints = [
        ("/health", "baseline (no DB)"),
        ("/events/?limit=30", "event list (filtered)"),
        ("/busyness/areas", "busyness areas (list)"),
        ("/busyness/nearby?lat=40.758&lng=-73.9855&radius_km=5", "nearby (spatial scan)"),
    ]
    if event_id:
        endpoints.insert(2, (f"/events/{event_id}", "event detail (indexed)"))

    # Warm the instance (Render free tier spins down when idle).
    hit(f"{base}/health")

    print(f"\nFROMO API load test  |  {base}")
    print(f"requests/endpoint={args.requests}  concurrency={args.concurrency}\n")
    print(f"{'endpoint':<46}{'p50':>7}{'p95':>7}{'p99':>7}{'max':>7}{'req/s':>8}{'err':>5}")
    print("-" * 87)
    for path, label in endpoints:
        s = bench(f"{base}{path}", args.requests, args.concurrency)
        name = f"{label}"
        print(f"{name:<46}{s['p50']:>6.0f}{s['p95']:>7.0f}{s['p99']:>7.0f}"
              f"{s['max']:>7.0f}{s['rps']:>8.1f}{s['errors']:>5}")
    print("\nlatencies in milliseconds, measured client-side to the target API.")


if __name__ == "__main__":
    main()
