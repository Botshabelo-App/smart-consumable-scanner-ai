# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

"""Build an offline retraining dataset from approved backend review exports.

Usage:
    export BACKEND_URL=http://localhost:8000
    export BACKEND_TOKEN=<admin jwt>
    python ai-service/scripts/build_feedback_dataset.py --output ai-service/datasets/feedback

This script does NOT retrain models automatically. It copies approved review images
into a directory structure suitable for `ai-service/datasets/train.py` so an offline
retraining run can be performed and the new model tested before deployment.
"""
import argparse
import os
import shutil
import urllib.parse
import urllib.request
from pathlib import Path


def fetch_reviews(base_url: str, token: str):
    req = urllib.request.Request(
        f"{base_url}/reviews/export",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req) as resp:
        import json

        return json.load(resp)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="ai-service/datasets/feedback")
    parser.add_argument("--base-url", default=os.environ.get("BACKEND_URL", "http://localhost:8000"))
    parser.add_argument("--token", default=os.environ.get("BACKEND_TOKEN"))
    args = parser.parse_args()

    if not args.token:
        raise SystemExit("Set --token or BACKEND_TOKEN")

    reviews = fetch_reviews(args.base_url, args.token)
    if not reviews:
        print("No approved reviews to export.")
        return

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    for item in reviews:
        condition = item.get("approved_condition") or item.get("suggested_condition") or "unknown"
        src = item.get("image_path")
        if not src or not Path(src).exists():
            continue
        ext = Path(src).suffix or ".jpg"
        dst_dir = out / condition
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst = dst_dir / f"{item['scan_id']}{ext}"
        shutil.copy(src, dst)
        print(f"Copied {src} -> {dst}")

    print(f"Dataset prepared at {out}")


if __name__ == "__main__":
    main()
