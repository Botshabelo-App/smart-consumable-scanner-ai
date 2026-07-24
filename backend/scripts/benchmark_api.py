"""Benchmark backend + AI service end-to-end latency and throughput.

Usage:
    cd backend
    BASE_URL=http://localhost:8000 AI_SERVICE_URL=http://localhost:8001 \
        python scripts/benchmark_api.py --image /tmp/apple.png --runs 10
"""
import argparse
import statistics
import time
import urllib.parse
from pathlib import Path

import httpx


def get_token(base_url: str, email: str, password: str) -> str:
    r = httpx.post(f"{base_url}/auth/login", json={"email": email, "password": password})
    r.raise_for_status()
    return r.json()["access_token"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--email", default="phase3@example.com")
    parser.add_argument("--password", default="testpass123")
    parser.add_argument("--image", default="/tmp/apple.png")
    parser.add_argument("--runs", type=int, default=10)
    args = parser.parse_args()

    token = get_token(args.base_url, args.email, args.password)
    image_path = Path(args.image)

    latencies = []
    print(f"Running {args.runs} inference calls to {args.base_url}/scans/analyze ...")
    for i in range(args.runs):
        start = time.perf_counter()
        with image_path.open("rb") as f:
            files = {"image": (image_path.name, f, "image/png")}
            data = {"product_name": "apple"}
            r = httpx.post(
                f"{args.base_url}/scans/analyze",
                files=files,
                data=data,
                headers={"Authorization": f"Bearer {token}"},
                timeout=60.0,
            )
        end = time.perf_counter()
        r.raise_for_status()
        latencies.append((end - start) * 1000)
        print(f"  run {i + 1}: {latencies[-1]:.1f} ms -> {r.json()['condition']}")

    latencies.sort()
    n = len(latencies)
    report = {
        "endpoint": f"{args.base_url}/scans/analyze",
        "runs": n,
        "image": str(image_path),
        "mean_ms": round(statistics.mean(latencies), 2),
        "min_ms": round(latencies[0], 2),
        "max_ms": round(latencies[-1], 2),
        "p50_ms": round(latencies[n // 2], 2),
        "p95_ms": round(latencies[int(n * 0.95)], 2) if n >= 20 else round(latencies[-1], 2),
        "throughput_rps": round(1000 / statistics.mean(latencies), 2),
    }

    print("\nBenchmark report:")
    print(report)

    out = Path("backend/reports/api_benchmark.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    import json

    out.write_text(json.dumps(report, indent=2))
    print(f"Report saved to {out}")


if __name__ == "__main__":
    main()
