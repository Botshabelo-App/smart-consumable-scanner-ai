# Long-Term Dataset Strategy

**Status:** Release Candidate 1 (RC1) — Pilot Evaluation and Maintenance Mode.

This document describes how training data is collected, annotated, reviewed, quality-checked, and used for model retraining and retirement.

## 1. Dataset collection standards

### Source categories

Collect images for every supported product category and condition:

- **Food:** beef, chicken, fish, pork, lamb, dairy, eggs, bread, fruits, vegetables, frozen food, packaged food, canned food.
- **Drinks:** water, juice, milk, beer, whiskey, wine, soft drinks, energy drinks, coffee, tea.
- **Other consumables:** cooking oil, sauces, baby food, flour, rice, sugar, powder products.

### Conditions to capture

Each category should include examples representing:

- Fresh
- Near expiry
- Expired
- Damaged packaging
- Different lighting (natural, fluorescent, dim, direct sunlight)
- Different camera models and smartphones
- Different viewing angles (top, side, front, close-up)
- Different manufacturers and packaging types

### Metadata requirements

Every image must be accompanied by:

- `product_category`
- `condition` (ground-truth label)
- `capture_device` (phone model)
- `lighting`
- `angle`
- `date_captured`
- `annotator_id`
- `reviewer_id` (for approved overrides)
- `dataset_version`

## 2. Annotation standards

- Annotations are made by trained domain experts or inspectors.
- Each image is labelled with the most specific condition visible.
- Disagreements between annotators are escalated to a senior reviewer.
- Override feedback from the mobile app is treated as a label candidate and must be reviewed before inclusion.

## 3. Expert review workflow

1. Inspector submits override through mobile app (`POST /scans/{id}/feedback`).
2. Reviewer examines the image, metadata, and reason in the review queue (`GET /reviews?status=pending`).
3. Reviewer assigns an `approved_label` and marks the request `approved` or `rejected`.
4. Approved examples are exported to `ai-service/datasets/feedback/`.
5. Dataset curator merges approved examples into the next `dataset_version`.

## 4. Data quality requirements

Before any dataset is used for training:

- Run `ai-service/datasets/quality.py` to detect duplicates, blur, corruption, and class imbalance.
- Ensure no image appears in both training and test sets.
- Minimum per-class samples: 100 for pilot, 500 for production candidate.
- Document rejected images and reasons.

## 5. Privacy considerations

- Remove or blur faces, licence plates, and any non-product PII.
- Store GPS coordinates with appropriate precision and access controls.
- Comply with POPIA and GDPR for personal data.
- Obtain consent where human subjects appear incidentally.

## 6. Model retraining policy

- Retraining is triggered quarterly or after accumulating ≥500 new approved labels.
- New datasets must be versioned (e.g., `pilot-001`, `pilot-002`).
- Use stratified k-fold cross-validation and a held-out test set.
- Compare the new model's validation score to the active model before promotion.
- Retrain only offline; no automatic production model updates.

## 7. Model retirement policy

- A model is retired when a newer model is promoted and has been stable for at least 30 days.
- Retired models are archived, not deleted, for audit and reproducibility.
- Datasets associated with retired models are retained for the same period.

## 8. Dataset growth targets

| Phase | Target | Notes |
|-------|--------|-------|
| RC1 pilot | 500–1,000 labelled images | Cover produce, dairy, packaged goods, beverages at pilot sites. |
| RC2 | 2,000–5,000 images | Add meat, frozen, canned categories. |
| v1.0.0 candidate | ≥5,000 images per category group | Produce, meat/dairy, packaged/beverages, other consumables. |
| v2.x | 50,000+ images with sensor fusion | Include NIR/hyperspectral/thermal where available. |

## 9. Tools

- `ai-service/datasets/download_datasets.py` — public dataset ingestion.
- `ai-service/datasets/quality.py` — quality validation.
- `ai-service/datasets/train.py` — training pipeline.
- `ai-service/scripts/evaluate_models.py` — evaluation.
- `ai-service/scripts/explain.py` — explainability artifacts.
- `backend/scripts/pilot_summary.py` — weekly pilot summary.
