# AI Governance

**Status:** Engineering Complete — Release Candidate 1 (RC1) — Pilot Evaluation and Maintenance Mode.

This document defines how AI models for the Smart Consumable Scanner AI are developed, validated, deployed, monitored, and retired. It ensures that every model is traceable, measurable, and aligned with the project's safety and accuracy standards.

## 1. Model cards

Every model registered in `/model-registry` must include the following model card fields.

| Field | Description | Example |
|-------|-------------|---------|
| Model version | Unique semantic version | `0.6.0-rc1` |
| Model ID | Unique registry identifier | `scsa-2026-07-24-produce` |
| Dataset version | Version of the dataset used for training | `pilot-001` |
| Training date | ISO 8601 UTC timestamp | `2026-07-24T00:00:00Z` |
| Training configuration | Backbone, hyperparameters, augmentation policy | `efficientnet_b0`, lr=1e-4, 5-fold CV |
| Validation metrics | Per-class precision, recall, F1, accuracy, ECE | see below |
| Supported categories | List of product categories the model can classify | `["produce", "dairy"]` |
| Known limitations | Conditions, lighting, packaging types where performance is lower | low-light bruised apples, sealed opaque cans |
| Deployment date | When the model was promoted to active | `2026-07-24T12:00:00Z` |
| Rollback version | Previous active model ID/version | `scsa-2026-07-10-produce / 0.5.0` |
| Artifact path | Path or URL to the checkpoint | `s3://models/scsa-2026-07-24/model.pth` |
| Checksum | SHA-256 hash of the artifact | `a1b2c3...` |
| Approver | User who approved promotion | `admin-uuid` |

## 2. Validation metrics standard

For every model, the following metrics must be reported on a held-out test set that is disjoint from the training and validation folds.

### Required classification metrics

- Overall accuracy
- Macro-averaged precision, recall, F1
- Per-class precision, recall, F1
- Confusion matrix
- Expected Calibration Error (ECE)

### Required performance metrics

- Inference latency p50/p95/p99 on target hardware (CPU and GPU if applicable)
- Model size (MB) and memory footprint
- Mobile frame rate (FPS) on low-end, mid-range, and flagship devices

## 3. Model lifecycle

### Staging

1. Train candidate with `ai-service/datasets/train.py`.
2. Evaluate with `ai-service/scripts/evaluate_models.py` on held-out data.
3. Generate explainability artifacts with `ai-service/scripts/explain.py`.
4. Register candidate in `/model-registry` with status `staging`.

### Promotion

1. Compare candidate validation score to the active model.
2. If the score is lower, promotion is blocked unless `force=true` and a documented reason is provided.
3. `POST /model-registry/{model_id}/promote` archives the previous active model.
4. Record deployment date and rollback version.

### Monitoring

1. Track `/monitoring/operational` and `/monitoring/pilot` metrics weekly.
2. Investigate any spike in false positives, false negatives, or crash reports.
3. If a model degrades, roll back with `POST /model-registry/{model_id}/rollback`.

### Retirement

1. When a newer model supersedes an old one, set the old model status to `archived`.
2. Retain the artifact and model card for audit and reproducibility for at least 2 years.
3. Retired models must not be used for new inspections.

## 4. Dataset governance

See `docs/DATASET_STRATEGY.md` for full dataset standards. Key principles:

- Labelled data must be collected under controlled conditions with expert review.
- Each image must include category, condition, capture device, lighting, and date metadata.
- Data quality checks (blur, corruption, duplicates) must pass before training.
- Approved inspector overrides from the review workflow are the primary source of new labels.
- PII and location data must be handled according to POPIA/GDPR and project privacy policy.

## 5. Annotation and review workflow

1. Inspector captures a product and submits an override if they disagree with the AI.
2. Authorised reviewer inspects the image, metadata, and reason.
3. Reviewer sets an approved label (`approved_label`) and status `approved`.
4. Approved examples are exported with `GET /reviews/export` or `ai-service/scripts/build_feedback_dataset.py`.
5. Dataset curator merges approved examples into the next training dataset version.

## 6. Explainability requirements

Before a model is promoted, the following must be generated for at least one example per class:

- Grad-CAM overlay showing regions that influenced the prediction.
- Top-k class scores and confidence values.
- Reliability diagram and ECE.
- A sample human-readable explanation report.

## 7. Human-in-the-loop

The AI is always an inspection assistant, not the final decision-maker. Inspectors must be able to:

- Accept or override any AI assessment.
- Record the reason for every override.
- Attach additional photos.
- Request a second review from a supervisor.

## 8. Limitations and acceptable claims

- The AI evaluates observable external characteristics captured by a standard smartphone camera.
- It cannot determine the internal condition, odour, or chemical contamination of sealed or opaque products.
- Any claim about internal condition requires validated specialized hardware (e.g., NIR, hyperspectral) and a separate model card.
- Accuracy claims must be tied to a specific dataset version, test set, and model version.

## 9. Compliance and audit

- Every model promotion, rollback, and retirement is logged in `audit_logs`.
- Model cards and dataset versions are immutable once registered.
- `docs/VALIDATION_AND_REGULATORY.md` contains the regulatory summary for customer and regulator discussions.
