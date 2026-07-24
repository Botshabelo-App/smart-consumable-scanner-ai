# Changelog

All notable changes to the Smart Consumable Scanner AI project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased] — RC1 Maintenance Mode

### Added
- Maintenance Mode documentation (`docs/MAINTENANCE.md`).
- AI Governance doc (`docs/AI_GOVERNANCE.md`) with model cards and dataset standards.
- Long-Term Dataset Strategy (`docs/DATASET_STRATEGY.md`).
- Pilot monitoring report generators (`backend/scripts/pilot_weekly_report.py`, `backend/scripts/pilot_monthly_report.py`).
- `CHANGELOG.md`, `CONTRIBUTORS.md`, and `LESSONS_LEARNED.md`.

### Changed
- Official project status updated to **Release Candidate 1 (RC1) — Pilot Evaluation and Maintenance Mode**.
- Documentation cross-reviewed for consistency across README, release checklist, project status, roadmap, security audit, release readiness, pilot plan, validation/regulatory, and operations guide.

## [0.6.0] — 2026-07-24 — RC1 Pilot Candidate

### Added
- Pilot deployment profiles for all target organisation types (`/pilot-profiles`).
- Inspector human-in-the-loop accept/override workflow.
- Operational monitoring (`/monitoring/operational`) and pilot success metrics (`/monitoring/pilot`).
- AI model registry with promote/rollback and score-based promotion guard.
- `docs/RELEASE_CHECKLIST.md` and `docs/PROJECT_STATUS.md`.

### Changed
- Upgraded mobile dependencies to Expo SDK 57.0.8.
- Replaced `python-jose` with `PyJWT`.
- Added `slowapi` rate limiting and password validation.

## [0.5.0] — 2026-07-24 — Phase 5 AI Data Collection, Training & Validation

### Added
- Reproducible dataset pipeline (`ai-service/datasets/download_datasets.py`).
- Dataset quality validation (`ai-service/datasets/quality.py`).
- Reproducible training pipeline with stratified k-fold CV, early stopping, HPO, and experiment tracking (`ai-service/datasets/train.py`).
- Multi-backbone benchmark comparison (`ai-service/datasets/benchmark_backbones.py`).
- Explainability tooling: Grad-CAM, saliency maps, confidence calibration (`ai-service/scripts/explain.py`).
- Mobile performance profiler and device log analyzer.
- `docs/VALIDATION_AND_REGULATORY.md` and `docs/DEVICE_TESTING.md`.

## [0.4.0] — 2026-07-24 — Phase 4 Validation & Release Readiness

### Added
- Model evaluation script and reports (`ai-service/scripts/evaluate_models.py`).
- API performance benchmark (`backend/scripts/benchmark_api.py`).
- `docs/RELEASE_READINESS.md`, `docs/DEPLOYMENT_CHECKLIST.md`, `docs/PILOT_PLAN.md`, `docs/V1_ROADMAP.md`.

## [0.3.0] — 2026-07-24 — Phase 3 Enterprise Inspection Platform

### Added
- Product-first recognition with expanded category mapping.
- Barcode/QR scanning with Open Food Facts lookup and expiry-vs-AI discrepancy flagging.
- Manufacturer knowledge base.
- Enterprise PDF/CSV/Excel reports with QR code and signature.
- Analytics dashboards and multi-language i18n scaffolding for 11 SA languages.
- Enterprise admin (companies, branches, devices, inspectors, roles, audit).
- AI review workflow and offline retraining dataset export.

## [0.2.0] — 2026-07-24 — Phase 2 Production AI Development

### Added
- Real AI pipeline: YOLOv8 detection, EfficientNet-B0 classification, MobileNetV3-Small spoilage classifier, OpenCV packaging analysis.
- Dataset and training scaffolding, ONNX/TFLite export.
- Continuous camera capture, multi-angle capture, image quality validation.
- Dashboard with charts and GPS map.
- JWT, RBAC, encrypted token storage, audit logs, offline scan queue.
- Kubernetes, Nginx, Docker Compose, and EAS production configs.
- `docs/LIMITATIONS_AND_ROADMAP.md`.

## [0.1.0] — 2026-07-24 — Phase 1 Project Scaffold

### Added
- FastAPI backend with auth, users, scans, reports, and database.
- Python AI inference service with initial real classifier.
- React Native/Expo mobile app with scan, dashboard, history, and report screens.
- Docker Compose setup and initial documentation.
