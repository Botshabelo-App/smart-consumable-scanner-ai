# Dataset pipeline

This pipeline prepares consumable product images for training, validation, and fine-tuning the inspection models.

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
```

Each leaf folder is named after a `ProductCategory`/`Condition` combination. The training script creates class folders automatically from this structure.

## Public datasets used

- **Project-AgML/fresh_rotten_fruit_classification** (Hugging Face) — 8 fruit/vegetable types labeled `Fresh*` and `Rotten*`.
- **Project-AgML/FruitVision_quality_classification** (Hugging Face) — fresh, rotten, and formalin-mixed fruit images.
- **marcusklasson/GroceryStoreDataset** (GitHub) — smartphone-captured grocery images for product recognition.

## Download and prepare public datasets

```bash
cd ai-service/datasets
python download_datasets.py --output ../data --max-samples 1000
```

Omit `--max-samples` to download the full public datasets (recommended for training).

## Dataset quality validation

```bash
cd ai-service/datasets
python quality.py --data-dir ../data/raw --output ../reports/dataset_quality.json
```

This detects corrupted, blurred, and duplicate images and reports class distribution.

## Train a classifier

```bash
cd ai-service/datasets
python train.py --data-dir ../data/raw --output-dir ../experiments/exp01 --epochs 20 --backbone efficientnet_b0
```

Training supports:

- 5-fold stratified cross-validation (`--folds 5`)
- Early stopping (`--patience`)
- Multiple backbones: `efficientnet_b0`, `mobilenet_v3_small`, `convnext_tiny`, `vit_b_16`
- Hyperparameter search with Optuna (`--hpo --hpo-trials 20`)
- ONNX export of the best model (requires `onnx` package)
- Experiment tracking JSON (`experiment.json`)

## Compare backbones

```bash
cd ai-service/datasets
python benchmark_backbones.py --data-dir ../data/raw --output-dir ../reports --epochs 10 --folds 3
```

This runs the training pipeline on each supported backbone and writes `../reports/backbone_benchmark.json`.

## Explainability and calibration

After training a model, generate Grad-CAM visualisations and a reliability diagram:

```bash
cd ai-service
python scripts/explain.py explain --checkpoint experiments/exp01/model.pth --image /tmp/apple.png --output reports/explain/apple
python scripts/explain.py calibrate --checkpoint experiments/exp01/model.pth --data-dir data/raw --output reports/reliability_diagram.png
```

## On-device models

The `scripts/export_mobile_models.py` script converts the trained PyTorch checkpoint to ONNX and TFLite so the React Native mobile app can run inference locally where practical. The first production release keeps server-side inference as the default and uses on-device models as an optional offline fallback.
