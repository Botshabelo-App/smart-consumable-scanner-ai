# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

"""Aggregate mobile device performance logs exported by the in-app profiler.

Usage:
    python mobile/scripts/analyze_device_logs.py --logs-dir device_logs --output reports/device_testing_report.json

Input format (one JSON object per line):
    {"timestamp": 1700000000000, "scanId": "...", "durationMs": 1234, "fps": 22,
     "deviceInfo": {"platform": "android", "osVersion": "13", "model": "SM-A546E"}, ...}
"""
import argparse
import glob
import json
from pathlib import Path


def analyze(logs_dir: Path, output: Path):
    samples = []
    for path in glob.glob(str(logs_dir / "*.jsonl")) + glob.glob(str(logs_dir / "*.log")):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    samples.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    if not samples:
        print(f"No valid JSON log entries found in {logs_dir}")
        return {}

    # Group by platform
    by_platform = {}
    for s in samples:
        key = s.get("deviceInfo", {}).get("platform", "unknown")
        by_platform.setdefault(key, []).append(s)

    report = {
        "total_samples": len(samples),
        "platforms": {},
    }
    for platform, group in by_platform.items():
        durations = [s["durationMs"] for s in group if "durationMs" in s]
        fps_values = [s["fps"] for s in group if s.get("fps")]
        report["platforms"][platform] = {
            "samples": len(group),
            "mean_duration_ms": round(sum(durations) / len(durations), 2) if durations else None,
            "max_duration_ms": max(durations) if durations else None,
            "min_duration_ms": min(durations) if durations else None,
            "mean_fps": round(sum(fps_values) / len(fps_values), 2) if fps_values else None,
            "models": list(set(s.get("deviceInfo", {}).get("model") for s in group if s.get("deviceInfo", {}).get("model"))),
        }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    print(f"Report saved to {output}")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--logs-dir", type=Path, default=Path("mobile/device_logs"))
    parser.add_argument("--output", type=Path, default=Path("reports/device_testing_report.json"))
    args = parser.parse_args()
    analyze(args.logs_dir, args.output)


if __name__ == "__main__":
    main()
