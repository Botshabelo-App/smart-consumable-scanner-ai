"""Benchmark AI service model inference latency and model sizes.

Usage:
    python ai-service/scripts/benchmark_models.py --image /tmp/apple.png --runs 20
"""
import argparse
import json
import statistics
import time
from pathlib import Path

import torch
from PIL import Image


def load_pipeline():
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from ai_service.app.models.real_classifier import RealProductPipeline

    pipeline = RealProductPipeline()
    start = time.perf_counter()
    pipeline.warm_up()
    load_time = time.perf_counter() - start
    return pipeline, load_time


def count_parameters(models):
    total = 0
    for model in models:
        if model is not None:
            total += sum(p.numel() for p in model.parameters())
    return total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", default="/tmp/apple.png")
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument("--output", type=Path, default=Path("ai-service/reports/model_benchmark.json"))
    args = parser.parse_args()

    print("Loading models...")
    pipeline, load_time = load_pipeline()

    image = Image.open(args.image).convert("RGB")
    latencies = []
    print(f"Running {args.runs} model-only inference calls...")
    for i in range(args.runs):
        start = time.perf_counter()
        result = pipeline.predict(image, product_hint="apple")
        latencies.append((time.perf_counter() - start) * 1000)
    latencies.sort()
    n = len(latencies)

    params = count_parameters([pipeline.imagenet_model, pipeline.spoilage_model, pipeline.yolo])
    checkpoint_dir = Path(__file__).resolve().parents[1] / "checkpoints"
    model_files = sorted(checkpoint_dir.glob("*.pth")) if checkpoint_dir.exists() else []
    model_size_mb = round(sum(p.stat().st_size for p in model_files) / (1024 * 1024), 2) if model_files else 0.0

    yolo_path = Path("yolov8n.pt")
    yolo_size_mb = round(yolo_path.stat().st_size / (1024 * 1024), 2) if yolo_path.exists() else 0.0

    report = {
        "device": str(pipeline.device),
        "model_load_time_sec": round(load_time, 2),
        "total_trainable_parameters": params,
        "checkpoint_size_mb": model_size_mb,
        "yolo_size_mb": yolo_size_mb,
        "runs": n,
        "image": args.image,
        "mean_ms": round(statistics.mean(latencies), 2),
        "min_ms": round(latencies[0], 2),
        "max_ms": round(latencies[-1], 2),
        "p50_ms": round(latencies[n // 2], 2),
        "p95_ms": round(latencies[int(n * 0.95)], 2) if n >= 20 else round(latencies[-1], 2),
        "throughput_rps": round(1000 / statistics.mean(latencies), 2),
        "sample_result": {
            "condition": result.condition.value,
            "confidence": result.confidence,
            "category": result.category.value if result.category else None,
            "findings": result.findings,
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2))
    print("\nModel benchmark report:")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
