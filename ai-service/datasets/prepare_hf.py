"""Download a Hugging Face image dataset and organize it by category and condition."""

import argparse
import re
from pathlib import Path

from ai_service.schemas import Condition, ProductCategory


def normalize_condition(label: str) -> Condition:
    lower = label.lower()
    if "fresh" in lower or "good" in lower:
        return Condition.FRESH
    if "rotten" in lower or "stale" in lower or "expired" in lower or "bad" in lower:
        return Condition.EXPIRED
    if "mold" in lower or "spoil" in lower:
        return Condition.EXPIRED
    return Condition.SUSPICIOUS


def normalize_category(label: str) -> ProductCategory:
    lower = label.lower()
    for key, cat in [
        ("milk", ProductCategory.DAIRY),
        ("cheese", ProductCategory.DAIRY),
        ("yogurt", ProductCategory.DAIRY),
        ("beef", ProductCategory.MEAT),
        ("chicken", ProductCategory.MEAT),
        ("pork", ProductCategory.MEAT),
        ("fish", ProductCategory.SEAFOOD),
        ("bread", ProductCategory.FOOD),
        ("frozen", ProductCategory.FROZEN),
        ("water", ProductCategory.BEVERAGE),
        ("juice", ProductCategory.BEVERAGE),
        ("beer", ProductCategory.BEVERAGE),
        ("wine", ProductCategory.BEVERAGE),
        ("oil", ProductCategory.OTHER),
        ("canned", ProductCategory.PACKAGED),
        ("packaged", ProductCategory.PACKAGED),
    ]:
        if key in lower:
            return cat
    # Fruits and vegetables default to produce
    return ProductCategory.PRODUCE


def parse_label(label: str) -> tuple[ProductCategory, Condition, str]:
    """Infer category, condition and product name from a dataset label."""
    lower = label.lower().replace("_", " ")
    cond = normalize_condition(lower)
    cat = normalize_category(lower)
    name = re.sub(r"^(fresh|rotten|stale|expired|spoiled|good)\s+", "", lower, flags=re.I).strip()
    return cat, cond, name


def prepare_hf_dataset(dataset_name: str, output_dir: Path, split: str = "train") -> None:
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise RuntimeError("Please install 'datasets' (huggingface datasets library) first.") from exc

    ds = load_dataset(dataset_name, split=split)
    output_dir = output_dir / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)

    for i, example in enumerate(ds):
        image = example["image"]
        label = example.get("label", "unknown")
        cat, cond, name = parse_label(str(label))
        target = output_dir / cat.value / cond.value
        target.mkdir(parents=True, exist_ok=True)
        ext = "png" if image.mode == "RGBA" else "jpg"
        filename = f"{name.replace(' ', '_')}_{i:06d}.{ext}"
        image.save(target / filename)

    print(f"Saved {len(ds)} images to {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="Project-AgML/fresh_rotten_fruit_classification")
    parser.add_argument("--output", default="../data")
    parser.add_argument("--split", default="train")
    args = parser.parse_args()
    prepare_hf_dataset(args.dataset, Path(args.output), args.split)
