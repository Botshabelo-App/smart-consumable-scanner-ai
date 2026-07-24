"""Reproducible training pipeline for product + condition classification.

Supports:
- K-fold stratified cross-validation
- Early stopping
- Multiple backbones (EfficientNet, MobileNet, ConvNeXt, ViT)
- Hyperparameter search with Optuna
- Experiment tracking (metrics + config JSON)
- ONNX export of the best model

Usage:
    cd ai-service/datasets
    python train.py --data-dir ../data/raw --output-dir ../experiments/exp01 --epochs 20 --backbone efficientnet_b0

Hyperparameter search:
    python train.py --data-dir ../data/raw --output-dir ../experiments/hpo --hpo --hpo-trials 20
"""
import argparse
import json
import random
import shutil
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torchvision.transforms as T
from PIL import Image
from sklearn.model_selection import StratifiedKFold
from torch.utils.data import DataLoader, Dataset, Subset
from torchvision import models
from tqdm import tqdm


def set_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


class ProductConditionDataset(Dataset):
    def __init__(self, root: Path, transform, paths=None, labels=None, classes=None):
        self.root = root
        self.transform = transform
        self.samples: list[tuple[Path, int]] = []
        self.classes: list[str] = classes or []

        if paths is not None and labels is not None:
            self.samples = list(zip(paths, labels))
            if not self.classes:
                for label in sorted(set(labels)):
                    class_name = self._label_name_from_idx(root, label)
                    self.classes.append(class_name)
            return

        for cat_dir in sorted(root.iterdir()):
            if not cat_dir.is_dir():
                continue
            for cond_dir in sorted(cat_dir.iterdir()):
                if not cond_dir.is_dir():
                    continue
                label = f"{cat_dir.name}_{cond_dir.name}"
                if label not in self.classes:
                    self.classes.append(label)
                class_idx = self.classes.index(label)
                for img_path in cond_dir.glob("*"):
                    if img_path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
                        self.samples.append((img_path, class_idx))

    def _label_name_from_idx(self, root: Path, idx: int) -> str:
        # reconstruct class order used by full dataset discovery
        labels = []
        for cat_dir in sorted(root.iterdir()):
            if not cat_dir.is_dir():
                continue
            for cond_dir in sorted(cat_dir.iterdir()):
                if not cond_dir.is_dir():
                    continue
                label = f"{cat_dir.name}_{cond_dir.name}"
                if label not in labels:
                    labels.append(label)
        return labels[idx]

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        path, label = self.samples[idx]
        image = Image.open(path).convert("RGB")
        return self.transform(image), label


def build_model(num_classes: int, backbone: str = "efficientnet_b0") -> nn.Module:
    if backbone == "efficientnet_b0":
        m = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.IMAGENET1K_V1)
        in_features = m.classifier[1].in_features
        m.classifier = nn.Sequential(nn.Dropout(0.2), nn.Linear(in_features, num_classes))
    elif backbone == "mobilenet_v3_small":
        m = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.IMAGENET1K_V1)
        in_features = m.classifier[0].in_features
        m.classifier = nn.Linear(in_features, num_classes)
    elif backbone == "convnext_tiny":
        m = models.convnext_tiny(weights=models.ConvNeXt_Tiny_Weights.IMAGENET1K_V1)
        in_features = m.classifier[2].in_features
        m.classifier[2] = nn.Linear(in_features, num_classes)
    elif backbone == "vit_b_16":
        m = models.vit_b_16(weights=models.ViT_B_16_Weights.IMAGENET1K_V1)
        in_features = m.heads.head.in_features
        m.heads.head = nn.Linear(in_features, num_classes)
    else:
        raise ValueError(f"Unknown backbone: {backbone}")
    return m


def get_transforms(backbone: str):
    size = 224
    if backbone == "vit_b_16":
        size = 224  # ViT-B/16 expects 224
    train = T.Compose([
        T.Resize((size, size)),
        T.RandomHorizontalFlip(),
        T.RandomRotation(15),
        T.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        T.ToTensor(),
        T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    val = T.Compose([
        T.Resize((size, size)),
        T.ToTensor(),
        T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    return train, val


def export_onnx(model: nn.Module, output_path: Path, device: torch.device, size: int = 224) -> None:
    try:
        import onnx  # noqa: F401
    except ImportError:
        print("  ONNX not installed; skipping ONNX export.")
        return
    model.eval()
    dummy = torch.randn(1, 3, size, size, device=device)
    torch.onnx.export(model, dummy, str(output_path), opset_version=13,
                      input_names=["input"], output_names=["output"],
                      dynamic_axes={"input": {0: "batch"}, "output": {0: "batch"}})


def evaluate(model: nn.Module, loader: DataLoader, criterion, device):
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            out = model(x)
            total_loss += criterion(out, y).item()
            preds = out.argmax(dim=1)
            correct += (preds == y).sum().item()
            total += y.size(0)
    return total_loss / max(len(loader), 1), correct / max(total, 1)


def train_fold(train_idx, val_idx, full_dataset, classes, config, device, output_dir):
    train_transform, val_transform = get_transforms(config["backbone"])
    train_subset = ProductConditionDataset(full_dataset.root, train_transform,
                                           paths=[full_dataset.samples[i][0] for i in train_idx],
                                           labels=[full_dataset.samples[i][1] for i in train_idx],
                                           classes=classes)
    val_subset = ProductConditionDataset(full_dataset.root, val_transform,
                                         paths=[full_dataset.samples[i][0] for i in val_idx],
                                         labels=[full_dataset.samples[i][1] for i in val_idx],
                                         classes=classes)

    train_loader = DataLoader(train_subset, batch_size=config["batch_size"], shuffle=True, num_workers=0)
    val_loader = DataLoader(val_subset, batch_size=config["batch_size"], shuffle=False, num_workers=0)

    model = build_model(len(classes), config["backbone"]).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=config["lr"], weight_decay=config.get("weight_decay", 1e-4))
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=3, factor=0.5)
    criterion = nn.CrossEntropyLoss()

    best_val_loss = float("inf")
    best_state = None
    epochs_no_improve = 0
    history = []

    for epoch in range(config["epochs"]):
        model.train()
        train_loss = 0.0
        for x, y in tqdm(train_loader, desc=f"Epoch {epoch + 1}/{config['epochs']}", leave=False):
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            out = model(x)
            loss = criterion(out, y)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

        train_loss /= max(len(train_loader), 1)
        val_loss, val_acc = evaluate(model, val_loader, criterion, device)
        scheduler.step(val_loss)
        history.append({"epoch": epoch + 1, "train_loss": train_loss, "val_loss": val_loss, "val_acc": val_acc})

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_state = model.state_dict()
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1

        if epochs_no_improve >= config["patience"]:
            print(f"  Early stopping at epoch {epoch + 1}")
            break

    # Restore best state
    if best_state:
        model.load_state_dict(best_state)
    return model, history, best_val_loss


def run_experiment(data_dir: Path, output_dir: Path, config: dict):
    set_seed(config.get("seed", 42))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    output_dir.mkdir(parents=True, exist_ok=True)

    train_transform, _ = get_transforms(config["backbone"])
    full_dataset = ProductConditionDataset(data_dir, train_transform)
    if not full_dataset.samples:
        raise RuntimeError(f"No images found in {data_dir}. Run download_datasets.py first.")

    labels = [s[1] for s in full_dataset.samples]
    classes = full_dataset.classes
    skf = StratifiedKFold(n_splits=config["folds"], shuffle=True, random_state=config.get("seed", 42))

    fold_results = []
    best_fold_model = None
    best_fold_loss = float("inf")

    for fold, (train_idx, val_idx) in enumerate(skf.split(np.zeros(len(labels)), labels)):
        print(f"\n=== Fold {fold + 1}/{config['folds']} ===")
        model, history, fold_loss = train_fold(train_idx, val_idx, full_dataset, classes, config, device, output_dir)
        val_eval_subset = ProductConditionDataset(data_dir, get_transforms(config["backbone"])[1],
                                                  paths=[full_dataset.samples[i][0] for i in val_idx],
                                                  labels=[full_dataset.samples[i][1] for i in val_idx],
                                                  classes=classes)
        _, val_acc = evaluate(model, DataLoader(val_eval_subset,
            batch_size=config["batch_size"], shuffle=False, num_workers=0
        ), nn.CrossEntropyLoss(), device)
        fold_results.append({"fold": fold + 1, "best_val_loss": fold_loss, "val_acc": val_acc, "history": history})
        if fold_loss < best_fold_loss:
            best_fold_loss = fold_loss
            best_fold_model = model

    # Save best model
    if best_fold_model:
        best_fold_model.eval()
        size = 224 if config["backbone"] != "vit_b_16" else 224
        export_onnx(best_fold_model, output_dir / "model.onnx", device, size=size)
        torch.save({"classes": classes, "model": best_fold_model.state_dict(), "backbone": config["backbone"], "config": config},
                   output_dir / "model.pth")
        (output_dir / "classes.json").write_text(json.dumps(classes))

    report = {
        "config": config,
        "device": str(device),
        "num_classes": len(classes),
        "num_samples": len(full_dataset.samples),
        "folds": fold_results,
        "summary": {
            "mean_val_acc": round(float(np.mean([f["val_acc"] for f in fold_results])), 4),
            "std_val_acc": round(float(np.std([f["val_acc"] for f in fold_results])), 4),
            "mean_best_val_loss": round(float(np.mean([f["best_val_loss"] for f in fold_results])), 4),
        },
    }
    (output_dir / "experiment.json").write_text(json.dumps(report, indent=2))
    print("\nExperiment summary:")
    print(json.dumps(report["summary"], indent=2))
    print(f"Saved to {output_dir}")
    return report


def objective(trial, data_dir: Path, output_dir: Path, base_config: dict):
    config = base_config.copy()
    config["lr"] = trial.suggest_float("lr", 1e-5, 1e-3, log=True)
    config["batch_size"] = trial.suggest_categorical("batch_size", [16, 32, 64])
    config["backbone"] = trial.suggest_categorical("backbone", ["efficientnet_b0", "mobilenet_v3_small", "convnext_tiny"])
    config["weight_decay"] = trial.suggest_float("weight_decay", 1e-6, 1e-2, log=True)

    trial_output = output_dir / f"trial_{trial.number}"
    report = run_experiment(data_dir, trial_output, config)
    return report["summary"]["mean_val_acc"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("../data/raw"))
    parser.add_argument("--output-dir", type=Path, default=Path("../experiments/exp01"))
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--patience", type=int, default=5)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--backbone", default="efficientnet_b0",
                        choices=["efficientnet_b0", "mobilenet_v3_small", "convnext_tiny", "vit_b_16"])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--hpo", action="store_true", help="Run Optuna hyperparameter search")
    parser.add_argument("--hpo-trials", type=int, default=20)
    args = parser.parse_args()

    config = {
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "lr": args.lr,
        "weight_decay": args.weight_decay,
        "patience": args.patience,
        "folds": args.folds,
        "backbone": args.backbone,
        "seed": args.seed,
    }

    if args.hpo:
        import optuna
        shutil.rmtree(args.output_dir, ignore_errors=True)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        study = optuna.create_study(direction="maximize")
        study.optimize(lambda trial: objective(trial, args.data_dir, args.output_dir, config), n_trials=args.hpo_trials)
        best = study.best_trial
        (args.output_dir / "best_hpo_config.json").write_text(json.dumps({
            "best_val_acc": best.value,
            "params": best.params,
        }, indent=2))
        print("Best HPO config:", best.params, "val_acc", best.value)
    else:
        run_experiment(args.data_dir, args.output_dir, config)


if __name__ == "__main__":
    main()
