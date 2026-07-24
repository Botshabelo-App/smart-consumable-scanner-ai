"""Train and compare multiple backbone architectures for product/condition classification.

Usage:
    cd ai-service/datasets
    python benchmark_backbones.py --data-dir ../data/raw --output-dir ../reports --epochs 5 --folds 3
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from train import run_experiment


BACKBONES = ["mobilenet_v3_small", "efficientnet_b0", "convnext_tiny"]


def benchmark(data_dir: Path, output_dir: Path, epochs: int = 5, folds: int = 3, batch_size: int = 32, lr: float = 1e-4):
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for backbone in BACKBONES:
        print(f"\n===== Benchmarking {backbone} =====")
        exp_dir = output_dir / backbone
        config = {
            "backbone": backbone,
            "epochs": epochs,
            "folds": folds,
            "batch_size": batch_size,
            "lr": lr,
            "patience": 5,
            "weight_decay": 1e-4,
            "seed": 42,
        }
        report = run_experiment(data_dir, exp_dir, config)
        results.append({
            "backbone": backbone,
            "mean_val_acc": report["summary"]["mean_val_acc"],
            "std_val_acc": report["summary"]["std_val_acc"],
            "mean_val_loss": report["summary"]["mean_best_val_loss"],
            "num_samples": report["num_samples"],
            "num_classes": report["num_classes"],
            "experiment_dir": str(exp_dir),
        })

    results.sort(key=lambda x: x["mean_val_acc"], reverse=True)
    summary = {"backbones": results, "best": results[0] if results else None}
    (output_dir / "backbone_benchmark.json").write_text(json.dumps(summary, indent=2))
    print("\nBenchmark summary:")
    print(json.dumps(results, indent=2))
    print(f"Saved to {output_dir / 'backbone_benchmark.json'}")
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("../data/raw"))
    parser.add_argument("--output-dir", type=Path, default=Path("../reports"))
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--folds", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-4)
    args = parser.parse_args()
    benchmark(args.data_dir, args.output_dir, args.epochs, args.folds, args.batch_size, args.lr)


if __name__ == "__main__":
    main()
