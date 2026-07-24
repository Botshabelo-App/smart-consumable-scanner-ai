"""Dataset quality validation tools.

Usage:
    cd ai-service/datasets
    python quality.py --data-dir ../data/raw --output ../reports/dataset_quality.json

Checks:
    - Corrupted / unreadable images
    - Blurred images (Laplacian variance)
    - Duplicate images (perceptual hash)
    - Folder structure and annotations
    - Class distribution statistics
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def _hash_image(path: Path, hasher):
    try:
        img = Image.open(path).convert("RGB").resize((128, 128))
        if hasher:
            return hasher(img)
        # Fallback: average downsampling + mean hash
        arr = np.array(img.resize((16, 16)).convert("L"))
        return arr.tobytes()
    except Exception:
        return None


def _is_blur(path: Path, threshold: float = 80.0) -> tuple[bool, float]:
    """Return (is_blur, normalized_variance). Variance is normalized to a 224x224 reference."""
    try:
        img = cv2.imread(str(path))
        if img is None:
            return False, 0.0
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        var = cv2.Laplacian(gray, cv2.CV_64F).var()
        # Normalize to 224x224 reference so threshold is independent of resolution
        normalized_var = var * (224 * 224) / max(h * w, 1)
        return normalized_var < threshold, round(normalized_var, 2)
    except Exception:
        return False, 0.0


def validate_dataset(data_dir: Path, output: Path, blur_threshold: float = 80.0):
    try:
        import imagehash

        hasher = imagehash.average_hash
    except ImportError:
        print("imagehash not installed; using simple byte hash for duplicate detection.")
        hasher = None

    issues = []
    stats = {"total_images": 0, "corrupted": 0, "blurred": 0, "duplicates": 0, "per_class": {}}
    hashes: dict = {}
    seen: dict = {}

    images = sorted(data_dir.rglob("*.*"))
    for img_path in images:
        if img_path.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
            continue

        rel = img_path.relative_to(data_dir)
        parts = list(rel.parts)
        if len(parts) < 3:
            issues.append({"file": str(rel), "issue": "unexpected_path", "message": "Expected raw/<category>/<condition>/<file>"})
            continue

        category = parts[0]
        condition = parts[1]
        class_key = f"{category}/{condition}"
        stats["per_class"][class_key] = stats["per_class"].get(class_key, 0) + 1
        stats["total_images"] += 1

        # Corruption / readability
        try:
            with Image.open(img_path) as im:
                im.load()
        except Exception as exc:
            stats["corrupted"] += 1
            issues.append({"file": str(rel), "issue": "corrupted", "message": str(exc)})
            continue

        # Blur
        is_blur, var = _is_blur(img_path, blur_threshold)
        if is_blur:
            stats["blurred"] += 1
            issues.append({"file": str(rel), "issue": "blurred", "laplacian_variance": round(var, 2)})

        # Duplicate detection
        h = _hash_image(img_path, hasher)
        if h is not None:
            if h in seen:
                stats["duplicates"] += 1
                issues.append({"file": str(rel), "issue": "duplicate", "duplicate_of": seen[h]})
            else:
                seen[h] = str(rel)

    report = {
        "data_dir": str(data_dir),
        "blur_threshold": blur_threshold,
        "summary": stats,
        "issues": issues,
        "recommendations": [],
    }

    if stats["corrupted"]:
        report["recommendations"].append("Remove or re-acquire corrupted images.")
    if stats["blurred"]:
        report["recommendations"].append("Review blurred images and re-capture if important.")
    if stats["duplicates"]:
        report["recommendations"].append("Remove duplicate images to avoid data leakage.")
    if min(stats["per_class"].values() or [0]) < 10:
        report["recommendations"].append("Some classes have fewer than 10 images; collect more samples for robust validation.")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2))
    print(json.dumps(report["summary"], indent=2))
    print(f"Quality report written to {output}")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("../data/raw"))
    parser.add_argument("--output", type=Path, default=Path("../reports/dataset_quality.json"))
    parser.add_argument("--blur-threshold", type=float, default=0.5)
    args = parser.parse_args()
    validate_dataset(args.data_dir, args.output, args.blur_threshold)


if __name__ == "__main__":
    main()
