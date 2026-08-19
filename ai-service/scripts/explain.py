# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

"""Explainability utilities for the product/condition classifier.

Generates:
- Grad-CAM heatmaps and overlays
- Top-k prediction explanations
- Confidence calibration (reliability) diagrams

Usage:
    cd ai-service
    python scripts/explain.py --checkpoint experiments/exp01/model.pth --image /tmp/apple.png --output reports/explain/apple
"""
import argparse
import importlib.util
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn.functional as F
import torchvision.transforms as T
from PIL import Image

# Load the local dataset training module by path to avoid the name clash with
# the Hugging Face 'datasets' package.
_DATASET_TRAIN_PATH = Path(__file__).resolve().parents[1] / "datasets" / "train.py"
_spec = importlib.util.spec_from_file_location("dataset_train", _DATASET_TRAIN_PATH)
_dataset_train = importlib.util.module_from_spec(_spec)
sys.modules["dataset_train"] = _dataset_train
_spec.loader.exec_module(_dataset_train)
build_model = _dataset_train.build_model
get_transforms = _dataset_train.get_transforms
ProductConditionDataset = _dataset_train.ProductConditionDataset


def load_model(checkpoint_path: Path, device):
    checkpoint = torch.load(checkpoint_path, map_location=device)
    classes = checkpoint["classes"]
    backbone = checkpoint.get("backbone", "efficientnet_b0")
    model = build_model(len(classes), backbone).to(device)
    model.load_state_dict(checkpoint["model"])
    model.eval()
    return model, classes, backbone


def get_target_layer(model, backbone):
    if backbone == "efficientnet_b0":
        return model.features[-1]
    if backbone == "mobilenet_v3_small":
        return model.features[-1]
    if backbone == "convnext_tiny":
        return model.features[-1]
    if backbone == "vit_b_16":
        # ViT has no conv layers; use encoder block attention
        return model.encoder.layers[-1].ln_1
    raise ValueError(f"No target layer mapping for {backbone}")


def generate_gradcam(model, image_tensor, target_class, target_layer, device):
    try:
        from pytorch_grad_cam import GradCAM
        from pytorch_grad_cam.utils.image import show_cam_on_image
        from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget
    except ImportError:
        print("pytorch_grad_cam not installed; install grad-cam package.")
        return None, None

    cam = GradCAM(model=model, target_layers=[target_layer])
    targets = [ClassifierOutputTarget(target_class)]
    grayscale_cam = cam(input_tensor=image_tensor.to(device), targets=targets)
    heatmap = grayscale_cam[0, :]

    # Normalize image for overlay
    img_np = image_tensor[0].cpu().permute(1, 2, 0).numpy()
    img_np = (img_np - img_np.min()) / (img_np.max() - img_np.min() + 1e-8)
    overlay = show_cam_on_image(img_np, heatmap, use_rgb=True, image_weight=0.6)
    return heatmap, overlay


def explain_image(checkpoint: Path, image_path: Path, output_dir: Path, device_name: str = "cpu"):
    device = torch.device(device_name)
    model, classes, backbone = load_model(checkpoint, device)
    transform, _ = get_transforms(backbone)

    image = Image.open(image_path).convert("RGB")
    tensor = transform(image).unsqueeze(0)

    with torch.no_grad():
        logits = model(tensor.to(device))
        probs = F.softmax(logits, dim=1).cpu()[0]

    topk = torch.topk(probs, min(5, len(classes)))
    explanation = {
        "image": str(image_path),
        "checkpoint": str(checkpoint),
        "backbone": backbone,
        "predictions": [
            {"class": classes[idx], "probability": round(probs[idx].item(), 4)}
            for idx in topk.indices.tolist()
        ],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "explanation.json").write_text(
        __import__("json").dumps(explanation, indent=2)
    )

    # Save original and overlay
    image.save(output_dir / "input.jpg")
    target_class = topk.indices[0].item()
    target_layer = get_target_layer(model, backbone)
    heatmap, overlay = generate_gradcam(model, tensor, target_class, target_layer, device)
    if overlay is not None:
        Image.fromarray(overlay).save(output_dir / "gradcam_overlay.jpg")
        plt.imsave(output_dir / "gradcam_heatmap.jpg", heatmap, cmap="jet")

    # Bar chart of top-k
    labels = [classes[i] for i in topk.indices.tolist()]
    values = [probs[i].item() for i in topk.indices.tolist()]
    plt.figure(figsize=(8, 4))
    plt.barh(labels[::-1], values[::-1])
    plt.xlabel("Probability")
    plt.title("Top predictions")
    plt.tight_layout()
    plt.savefig(output_dir / "topk_probabilities.png")
    plt.close()

    print(f"Explanation saved to {output_dir}")
    print(__import__("json").dumps(explanation, indent=2))


def calibrate(checkpoint: Path, data_dir: Path, output: Path, device_name: str = "cpu", n_bins: int = 10):
    """Generate a reliability diagram for the model on a labelled dataset."""
    device = torch.device(device_name)
    model, classes, backbone = load_model(checkpoint, device)
    _, val_transform = get_transforms(backbone)
    dataset = ProductConditionDataset(data_dir, val_transform)
    if not dataset.samples:
        raise RuntimeError(f"No images in {data_dir}")

    loader = torch.utils.data.DataLoader(dataset, batch_size=32, shuffle=False, num_workers=0)
    all_probs = []
    all_labels = []
    with torch.no_grad():
        for x, y in loader:
            x = x.to(device)
            logits = model(x)
            probs = F.softmax(logits, dim=1).cpu()
            all_probs.append(probs)
            all_labels.append(y)

    all_probs = torch.cat(all_probs)
    all_labels = torch.cat(all_labels)
    confidences, predictions = all_probs.max(dim=1)
    confidences = confidences.numpy()
    predictions = predictions.numpy()
    labels = all_labels.numpy()
    correct = (predictions == labels).astype(int)

    bin_edges = np.linspace(0, 1, n_bins + 1)
    bin_lowers = bin_edges[:-1]
    bin_uppers = bin_edges[1:]
    bin_accs = []
    bin_confs = []
    for low, up in zip(bin_lowers, bin_uppers):
        mask = (confidences > low) & (confidences <= up)
        if mask.sum() == 0:
            bin_accs.append(0.0)
            bin_confs.append((low + up) / 2)
        else:
            bin_accs.append(correct[mask].mean())
            bin_confs.append(confidences[mask].mean())

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot([0, 1], [0, 1], "--", label="Perfect calibration")
    ax.plot(bin_confs, bin_accs, "-o", label="Model")
    ax.set_xlabel("Confidence")
    ax.set_ylabel("Accuracy")
    ax.set_title("Reliability Diagram")
    ax.legend()
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output)
    plt.close()

    ece = np.mean(np.abs(np.array(bin_accs) - np.array(bin_confs)))
    print(f"Expected Calibration Error (ECE): {ece:.4f}")
    print(f"Reliability diagram saved to {output}")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p1 = sub.add_parser("explain", help="Explain a single image")
    p1.add_argument("--checkpoint", type=Path, required=True)
    p1.add_argument("--image", type=Path, required=True)
    p1.add_argument("--output", type=Path, default=Path("reports/explain"))
    p1.add_argument("--device", default="cpu")

    p2 = sub.add_parser("calibrate", help="Generate reliability diagram")
    p2.add_argument("--checkpoint", type=Path, required=True)
    p2.add_argument("--data-dir", type=Path, required=True)
    p2.add_argument("--output", type=Path, default=Path("reports/reliability_diagram.png"))
    p2.add_argument("--device", default="cpu")
    p2.add_argument("--n-bins", type=int, default=10)

    args = parser.parse_args()
    if args.command == "explain":
        explain_image(args.checkpoint, args.image, args.output, args.device)
    elif args.command == "calibrate":
        calibrate(args.checkpoint, args.data_dir, args.output, args.device, args.n_bins)


if __name__ == "__main__":
    main()
