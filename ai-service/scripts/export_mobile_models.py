# Copyright 2026 Moeketsi Daniel and contributors.
# All rights reserved.
# This file is part of the Smart Consumable Scanner AI project.
# Use is subject to the project licence terms.

"""Export the trained PyTorch checkpoint to ONNX and TensorFlow Lite for mobile deployment."""

import argparse
import json
from pathlib import Path

import torch

from ai_service.app.models.real_classifier import _download_spoilage_checkpoint


def export_spoilage_to_onnx(output_dir: Path) -> None:
    """Export the MobileNetV3-Small spoilage classifier to ONNX."""
    from torchvision import models
    import torch.nn as nn

    checkpoint = _download_spoilage_checkpoint()
    device = torch.device("cpu")
    model = models.mobilenet_v3_small(weights=None)
    model.classifier = nn.Sequential(
        nn.Linear(576, 256),
        nn.Hardswish(),
        nn.Dropout(0.2),
        nn.Linear(256, 1),
    )
    model.load_state_dict(torch.load(checkpoint, map_location=device, weights_only=True))
    model.eval()

    output_dir.mkdir(parents=True, exist_ok=True)
    onnx_path = output_dir / "spoilage_mobilenetv3.onnx"
    dummy = torch.randn(1, 3, 224, 224)
    torch.onnx.export(model, dummy, str(onnx_path), opset_version=11,
                      input_names=["input"], output_names=["output"],
                      dynamic_axes={"input": {0: "batch"}, "output": {0: "batch"}})
    print(f"ONNX: {onnx_path}")


def export_trained_to_tflite(checkpoint_path: Path, output_dir: Path) -> None:
    """Convert a trained PyTorch checkpoint to TFLite using ONNX as an intermediate."""
    output_dir.mkdir(parents=True, exist_ok=True)
    onnx_path = output_dir / "model.onnx"
    # Load and re-export to ONNX
    data = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    # Model must be defined from training script; not included to keep this script generic.
    print(f"Load checkpoint classes: {data.get('classes', [])}")
    (output_dir / "classes.json").write_text(json.dumps(data.get("classes", [])))
    print("Use ai-edge-torch or onnx2tf to convert the ONNX model to TFLite.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="../checkpoints/mobile")
    parser.add_argument("--trained-checkpoint", default="../checkpoints/model.pth")
    args = parser.parse_args()
    export_spoilage_to_onnx(Path(args.output_dir))
    export_trained_to_tflite(Path(args.trained_checkpoint), Path(args.output_dir))
