"""Register a trained checkpoint from `ai-service/datasets/train.py` in the backend model registry.

Usage:
    BACKEND_URL=http://localhost:8000 BACKEND_TOKEN=<admin-token> \
      python scripts/register_model.py \
      --model-id scsa-2026-07-24 \
      --version 0.6.0-rc1 \
      --dataset-version pilot-001 \
      --experiment-dir ../experiments/exp01 \
      --promote
"""
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests


def _checksum(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument("--experiment-dir", type=Path, required=True)
    parser.add_argument("--artifact-path")
    parser.add_argument("--promote", action="store_true")
    args = parser.parse_args()

    backend = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")
    token = os.environ.get("BACKEND_TOKEN")
    if not token:
        print("BACKEND_TOKEN is required", file=sys.stderr)
        sys.exit(1)

    experiment = args.experiment_dir / "experiment.json"
    if not experiment.exists():
        print(f"Experiment file not found: {experiment}", file=sys.stderr)
        sys.exit(1)

    report = json.loads(experiment.read_text())
    summary = report.get("summary", {})
    metrics = {
        "mean_val_acc": summary.get("mean_val_acc"),
        "std_val_acc": summary.get("std_val_acc"),
        "mean_best_val_loss": summary.get("mean_best_val_loss"),
        "backbone": report.get("config", {}).get("backbone"),
    }

    model_file = args.experiment_dir / "model.pth"
    if not model_file.exists():
        print(f"Model file not found: {model_file}", file=sys.stderr)
        sys.exit(1)

    artifact_path = args.artifact_path or str(model_file.resolve())
    checksum = _checksum(model_file)
    classes = json.loads((args.experiment_dir / "classes.json").read_text()) if (args.experiment_dir / "classes.json").exists() else []

    payload = {
        "model_id": args.model_id,
        "version": args.version,
        "dataset_version": args.dataset_version,
        "training_date": datetime.now(timezone.utc).isoformat(),
        "validation_metrics": metrics,
        "supported_categories": classes,
        "artifact_path": artifact_path,
        "checksum": checksum,
        "status": "staging",
    }

    headers = {"Authorization": f"Bearer {token}"}
    r = requests.post(f"{backend}/model-registry/", json=payload, headers=headers, timeout=30)
    if r.status_code not in (200, 201):
        print(f"Registration failed: {r.status_code} {r.text}", file=sys.stderr)
        sys.exit(1)
    print("Registered model:", r.json()["id"])

    if args.promote:
        pr = requests.post(f"{backend}/model-registry/{args.model_id}/promote", headers=headers, timeout=30)
        if pr.status_code not in (200, 201):
            print(f"Promotion failed: {pr.status_code} {pr.text}", file=sys.stderr)
            sys.exit(1)
        print("Promoted model:", pr.json())


if __name__ == "__main__":
    main()
