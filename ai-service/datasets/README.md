# Dataset pipeline

This pipeline prepares consumable product images for training and fine-tuning the inspection models.

## Expected folder layout

```
data/
  raw/
    produce/
      fresh/
        apple_001.jpg
        banana_001.jpg
        ...
      expired/
        rotten_apple_001.jpg
        ...
    dairy/
      fresh/
        milk_001.jpg
        ...
      expired/
        spoiled_milk_001.jpg
        ...
```

Each leaf folder is named after a `ProductCategory`/`Condition` combination. The training script creates class folders automatically from this structure.

## Public datasets used

- **Project-AgML/fresh_rotten_fruit_classification** (Hugging Face) — 8 fruit/vegetable types labeled `Fresh*` and `Rotten*`.
- Additional datasets can be added by placing images in `data/raw/<category>/<condition>/`.

## Prepare a Hugging Face dataset

```bash
cd datasets
python prepare_hf.py --dataset Project-AgML/fresh_rotten_fruit_classification --output ../data/raw
```

## Train a new classification model

```bash
cd datasets
python train.py --data-dir ../data/raw --epochs 20 --output-dir ../checkpoints
```

The training script uses transfer learning on `torchvision.efficientnet_b0` by default. It saves:

- `model.pth` — best PyTorch checkpoint
- `model.onnx` — ONNX export
- `model.tflite` — TensorFlow Lite export (optional, requires TensorFlow)

## On-device models

The `scripts/export_mobile_models.py` script converts the trained PyTorch checkpoint to ONNX and TFLite so the React Native mobile app can run inference locally where practical. The first production release keeps server-side inference as the default and uses on-device models as an optional offline fallback.
