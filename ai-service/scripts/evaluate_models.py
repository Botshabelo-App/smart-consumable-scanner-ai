"""Evaluate the real AI pipeline on a labeled test set.

Usage:
    python ai-service/scripts/evaluate_models.py \
        --test-dir datasets/test \
        --output ai-service/reports/model_evaluation.json

The test directory should have sub-folders named after conditions:
    datasets/test/fresh/img1.jpg
    datasets/test/expired/img2.jpg

If --test-dir is omitted, the script evaluates on the built-in /tmp/apple.png
and /tmp/rotten_apple.png examples.
"""
import argparse
import json
import time
from pathlib import Path
from typing import Dict, List

from PIL import Image


def load_pipeline():
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from ai_service.app.models.real_classifier import RealProductPipeline

    pipeline = RealProductPipeline()
    pipeline.warm_up()
    return pipeline


def evaluate(pipeline, test_dir: Path) -> Dict:
    labels = []
    predictions = []
    latencies = []
    results = []

    if test_dir and test_dir.exists():
        condition_map = {"fresh": "fresh", "near_expiry": "near_expiry", "suspicious": "suspicious", "expired": "expired"}
        images = []
        for condition_dir in test_dir.iterdir():
            if not condition_dir.is_dir():
                continue
            condition = condition_map.get(condition_dir.name.lower())
            if not condition:
                continue
            for img_path in condition_dir.iterdir():
                if img_path.suffix.lower() in (".jpg", ".jpeg", ".png"):
                    images.append((str(img_path), condition))
    else:
        # Built-in examples
        images = [("/tmp/apple.png", "fresh"), ("/tmp/rotten_apple.png", "expired")]

    product_hints = ["apple", "banana", "orange", "bread", "milk", "meat", "fish", "water", "beer", "wine"]

    for img_path, true_label in images:
        image = Image.open(img_path).convert("RGB")
        hint = next((h for h in product_hints if h in img_path.lower()), None)
        start = time.perf_counter()
        result = pipeline.predict(image, product_hint=hint)
        latencies.append(time.perf_counter() - start)

        pred_label = result.condition.value
        labels.append(true_label)
        predictions.append(pred_label)
        results.append({"image": img_path, "true": true_label, "predicted": pred_label, "confidence": result.confidence, "category": result.category.value if result.category else None})

    # Confusion matrix
    classes = ["fresh", "near_expiry", "suspicious", "expired"]
    cm = {true: {pred: 0 for pred in classes} for true in classes}
    for true, pred in zip(labels, predictions):
        if true in cm and pred in cm[true]:
            cm[true][pred] += 1

    # Per-class precision/recall/f1
    per_class = {}
    for c in classes:
        tp = cm[c][c]
        fp = sum(cm[other][c] for other in classes if other != c)
        fn = sum(cm[c][other] for other in classes if other != c)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        per_class[c] = {"precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3), "support": tp + fn}

    accuracy = sum(1 for t, p in zip(labels, predictions) if t == p) / len(labels) if labels else 0.0

    latencies_ms = [l * 1000 for l in latencies]
    latencies_ms.sort()
    n = len(latencies_ms)
    latency_summary = {
        "count": n,
        "mean_ms": round(sum(latencies_ms) / n, 2) if n else 0,
        "min_ms": round(latencies_ms[0], 2) if n else 0,
        "max_ms": round(latencies_ms[-1], 2) if n else 0,
        "p50_ms": round(latencies_ms[n // 2], 2) if n else 0,
        "p95_ms": round(latencies_ms[int(n * 0.95)], 2) if n else 0,
    }

    return {
        "summary": {
            "total_images": len(labels),
            "accuracy": round(accuracy, 3),
            "device": str(pipeline.device),
        },
        "per_class_metrics": per_class,
        "confusion_matrix": cm,
        "latency_ms": latency_summary,
        "predictions": results,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-dir", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=Path("ai-service/reports/model_evaluation.json"))
    args = parser.parse_args()

    print("Loading models...")
    pipeline = load_pipeline()
    print("Evaluating...")
    report = evaluate(pipeline, args.test_dir)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2))
    print(f"Evaluation report written to {args.output}")
    print(json.dumps(report["summary"], indent=2))
    print(json.dumps(report["per_class_metrics"], indent=2))


if __name__ == "__main__":
    main()
