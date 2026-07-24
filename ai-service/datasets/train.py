"""Train a category + condition classifier from prepared images."""

import argparse
import json
import random
from pathlib import Path

import torch
import torch.nn as nn
import torchvision.transforms as T
from PIL import Image
from torch.utils.data import DataLoader, Dataset, random_split
from torchvision import models
from tqdm import tqdm


class ProductConditionDataset(Dataset):
    def __init__(self, root: Path, transform):
        self.transform = transform
        self.samples: list[tuple[Path, int]] = []
        self.classes: list[str] = []
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
                    if img_path.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                        self.samples.append((img_path, class_idx))

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
        m.classifier = nn.Sequential(nn.Linear(in_features, num_classes))
    else:
        raise ValueError(f"Unknown backbone: {backbone}")
    return m


def export_onnx(model: nn.Module, output_path: Path, device: torch.device) -> None:
    model.eval()
    dummy = torch.randn(1, 3, 224, 224, device=device)
    torch.onnx.export(model, dummy, str(output_path), opset_version=11,
                      input_names=["input"], output_names=["output"],
                      dynamic_axes={"input": {0: "batch"}, "output": {0: "batch"}})


def train(data_dir: Path, output_dir: Path, epochs: int = 20, batch_size: int = 32,
          lr: float = 1e-4, backbone: str = "efficientnet_b0") -> None:
    random.seed(42)
    torch.manual_seed(42)

    transform = T.Compose([
        T.Resize((224, 224)),
        T.RandomHorizontalFlip(),
        T.RandomRotation(15),
        T.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        T.ToTensor(),
        T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    val_transform = T.Compose([
        T.Resize((224, 224)),
        T.ToTensor(),
        T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    full_dataset = ProductConditionDataset(data_dir, transform)
    if not full_dataset.samples:
        raise RuntimeError(f"No images found in {data_dir}. Run prepare_hf.py first.")

    n_val = max(1, int(len(full_dataset) * 0.2))
    n_train = len(full_dataset) - n_val
    train_ds, val_ds = random_split(full_dataset, [n_train, n_val])
    val_ds.dataset.transform = val_transform  # type: ignore

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=2)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model(len(full_dataset.classes), backbone).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    output_dir.mkdir(parents=True, exist_ok=True)
    best_loss = float("inf")

    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        for x, y in tqdm(train_loader, desc=f"Epoch {epoch + 1}/{epochs}"):
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            out = model(x)
            loss = criterion(out, y)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

        model.eval()
        val_loss = 0.0
        correct = 0
        total = 0
        with torch.no_grad():
            for x, y in val_loader:
                x, y = x.to(device), y.to(device)
                out = model(x)
                val_loss += criterion(out, y).item()
                preds = out.argmax(dim=1)
                correct += (preds == y).sum().item()
                total += y.size(0)

        print(f"Epoch {epoch + 1}: train_loss={train_loss / len(train_loader):.4f}, "
              f"val_loss={val_loss / len(val_loader):.4f}, val_acc={correct / total:.4f}")

        if val_loss < best_loss:
            best_loss = val_loss
            torch.save({"classes": full_dataset.classes, "model": model.state_dict(), "backbone": backbone},
                       output_dir / "model.pth")

    # Export best model
    export_onnx(model, output_dir / "model.onnx", device)
    (output_dir / "classes.json").write_text(json.dumps(full_dataset.classes))
    print(f"Saved checkpoint and ONNX export to {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="../data/raw")
    parser.add_argument("--output-dir", default="../checkpoints")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--backbone", default="efficientnet_b0",
                        choices=["efficientnet_b0", "mobilenet_v3_small"])
    args = parser.parse_args()
    train(Path(args.data_dir), Path(args.output_dir), args.epochs, args.batch_size, args.lr, args.backbone)
