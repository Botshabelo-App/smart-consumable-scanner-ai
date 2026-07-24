"""Reproducible public dataset downloader for Phase 5.

Usage:
    cd ai-service/datasets
    python download_datasets.py --output ../data --max-samples 1000

This downloads and standardizes several public datasets into:
    data/raw/<product_category>/<condition>/<product_name>_<id>.jpg

Supported sources:
    - Project-AgML/fresh_rotten_fruit_classification
    - Project-AgML/FruitVision_quality_classification
    - marcusklasson/GroceryStoreDataset (zip)
"""
import argparse
import io
import re
import shutil
import sys
import zipfile
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ai_service.schemas import Condition, ProductCategory

from prepare_hf import parse_label

DEFAULT_DATASETS = [
    ("Project-AgML/fresh_rotten_fruit_classification", "train"),
    ("Project-AgML/FruitVision_quality_classification", "train"),
]

GROCERYSTORE_ZIP = "https://github.com/marcusklasson/GroceryStoreDataset/archive/refs/heads/master.zip"


def normalize_fruitvision(label: str) -> tuple[ProductCategory, Condition, str]:
    """FruitVision labels are like 'Fresh', 'Rotten', 'Formalin-mixed'."""
    lower = label.lower().replace("_", " ")
    if "fresh" in lower:
        cond = Condition.FRESH
    elif "rotten" in lower or "expired" in lower:
        cond = Condition.EXPIRED
    elif "formalin" in lower or "mixed" in lower or "suspicious" in lower:
        cond = Condition.SUSPICIOUS
    else:
        cond = Condition.SUSPICIOUS
    # FruitVision coarse category is not in label; default to produce
    return ProductCategory.PRODUCE, cond, "fruit"


def download_huggingface(dataset_name: str, split: str, output_dir: Path, max_samples: int | None = None) -> int:
    from datasets import load_dataset

    print(f"Downloading Hugging Face dataset {dataset_name} (split={split}, max={max_samples or 'all'})...")
    ds = load_dataset(dataset_name, split=split, streaming=True)
    if max_samples:
        ds = ds.take(max_samples)

    label_names = None
    if hasattr(ds, "features") and "label" in ds.features:
        label_feature = ds.features["label"]
        if hasattr(label_feature, "names"):
            label_names = label_feature.names

    out = output_dir / "raw"
    out.mkdir(parents=True, exist_ok=True)
    count = 0
    for i, example in enumerate(ds):
        image = example["image"]
        raw_label = example.get("label", "unknown")
        if label_names and isinstance(raw_label, int):
            label_str = label_names[raw_label]
        else:
            label_str = str(raw_label)

        if "fruitvision" in dataset_name.lower():
            cat, cond, prod_name = normalize_fruitvision(label_str)
        else:
            cat, cond, prod_name = parse_label(label_str)

        target = out / cat.value / cond.value
        target.mkdir(parents=True, exist_ok=True)
        ext = "png" if image.mode == "RGBA" else "jpg"
        filename = f"{prod_name.replace(' ', '_')}_{i:06d}.{ext}"
        image.save(target / filename)
        count += 1
    print(f"  -> saved {count} images from {dataset_name}")
    return count


def download_grocerystore(output_dir: Path, max_samples: int | None = None) -> int:
    print(f"Downloading GroceryStoreDataset from {GROCERYSTORE_ZIP} ...")
    with urlopen(GROCERYSTORE_ZIP) as resp:
        zf = zipfile.ZipFile(io.BytesIO(resp.read()))

    temp = output_dir / ".tmp_grocerystore"
    temp.mkdir(parents=True, exist_ok=True)
    zf.extractall(temp)

    root = next(temp.iterdir())  # GroceryStoreDataset-master
    dataset_dir = root / "dataset"
    if not dataset_dir.exists():
        print("  WARNING: expected 'dataset' folder not found; skipping GroceryStoreDataset")
        shutil.rmtree(temp, ignore_errors=True)
        return 0

    # classes.csv: index, fine_name, coarse_name, iconic_path, desc_path
    classes_file = dataset_dir / "classes.csv"
    class_map = {}
    if classes_file.exists():
        for line in classes_file.read_text().strip().splitlines()[1:]:
            parts = line.split(",")
            if len(parts) >= 3:
                idx = int(parts[0])
                fine = parts[1].strip().lower().replace("_", " ")
                coarse = parts[2].strip().lower().replace("_", " ")
                class_map[idx] = (fine, coarse)

    out = output_dir / "raw"
    count = 0
    for split in ["train.txt", "val.txt", "test.txt"]:
        split_file = dataset_dir / split
        if not split_file.exists():
            continue
        for line in split_file.read_text().strip().splitlines():
            parts = line.split()
            if len(parts) < 2:
                continue
            img_rel = parts[0]
            fine_idx = int(parts[1])
            fine, coarse = class_map.get(fine_idx, ("unknown", "unknown"))
            # Grocery store images are assumed fresh/unknown condition
            cat, _, name = parse_label(coarse)
            cond = Condition.FRESH
            src = dataset_dir / img_rel
            if not src.exists():
                continue
            target = out / cat.value / cond.value
            target.mkdir(parents=True, exist_ok=True)
            ext = Path(src).suffix or ".jpg"
            filename = f"{name.replace(' ', '_')}_{count:06d}{ext}"
            shutil.copy(src, target / filename)
            count += 1
            if max_samples and count >= max_samples:
                break
        if max_samples and count >= max_samples:
            break

    shutil.rmtree(temp, ignore_errors=True)
    print(f"  -> saved {count} images from GroceryStoreDataset")
    return count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("../data"))
    parser.add_argument("--max-samples", type=int, default=None, help="Max images per Hugging Face dataset")
    parser.add_argument("--skip-grocery", action="store_true", help="Skip GroceryStoreDataset zip download")
    args = parser.parse_args()

    total = 0
    for name, split in DEFAULT_DATASETS:
        try:
            total += download_huggingface(name, split, args.output, args.max_samples)
        except Exception as exc:
            print(f"  ERROR downloading {name}: {exc}")

    if not args.skip_grocery:
        try:
            total += download_grocerystore(args.output, args.max_samples)
        except Exception as exc:
            print(f"  ERROR downloading GroceryStoreDataset: {exc}")

    print(f"\nTotal images downloaded: {total}")
    print(f"Output directory: {args.output / 'raw'}")


if __name__ == "__main__":
    main()
