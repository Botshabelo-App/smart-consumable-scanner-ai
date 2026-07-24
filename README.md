# Smart Consumable Scanner AI

**Project status: Release Candidate 1 (RC1) — Pilot Evaluation Phase.**

This project is **not yet production-ready**. It is ready for controlled pilot deployments. Version 1.0.0 must only be released after the pilot success criteria, AI validation, security review, and release checklist in `docs/RELEASE_CHECKLIST.md` are completed and signed off.

A production-ready, cross-platform mobile application for detecting expired, spoiled, damaged, counterfeit, or near-expiry consumable products using AI and a smartphone camera.

## Goals

- Camera-first inspection for food, beverages, packaged goods, produce, meat, dairy, and more.
- AI analysis based on product condition, not only printed expiry dates.
- Offline-capable SQLite mode and online PostgreSQL mode.
- Professional report generation with PDF/CSV/Excel export, QR codes, and digital signatures.
- Role-based access for inspectors, managers, administrators, and consumers.
- Scalable architecture for future sensors (Bluetooth, NIR, thermal, barcode, RFID, NFC, IoT).

## What's implemented

- **Real computer-vision pipeline** in `ai-service/`: YOLOv8 object detection, EfficientNet-B0 product classification, MobileNetV3-Small fresh/spoiled spoilage classifier, and OpenCV-based packaging/bruise analysis.
- **Product-first recognition**: detect product, identify category, then assess freshness/spoilage with explainable `findings`.
- **Barcode and QR integration**: scan barcodes in-app, look up products via Open Food Facts, and compare printed expiry data with AI findings.
- **Manufacturer knowledge base**: `Company`, `Branch`, `Manufacturer`, `Product`, and `Barcode` models with CRUD and import from Open Food Facts.
- **Enterprise reports**: PDF/CSV/Excel reports with company, product, batch, barcode, AI findings, confidence, inspector, GPS, timestamp, QR code, and optional digital signature.
- **Analytics dashboard**: inspection breakdown, confidence trends, expired-by-category stats, manufacturer trends, geographic distribution, and time-series analytics.
- **Multi-language scaffolding**: `i18n-js` + `expo-localization` with translation files for all 11 South African official languages.
- **Enterprise administration**: company/branch/device/inspector/role management with RBAC.
- **Continuous AI improvement**: review workflow for inspector disagreements, approved-review export for offline retraining, and controlled model-deployment pipeline.
- **Security**: JWT auth, role-based endpoints, encrypted token storage with `expo-secure-store`, audit logs, offline scan queue, rate limiting, password policy, and PyJWT-based tokens.
- **Production deployment**: Kubernetes manifests, Nginx reverse-proxy config, and EAS production build config.
- **Pilot deployment & continuous learning (RC1)**: configurable pilot profiles for every target organisation type, inspector accept/override workflow with reasons, operational monitoring dashboards, AI model registry with promote/rollback, and pilot success metrics.

## Repository Structure

```text
.
├── backend           FastAPI API server, auth, database, reports, audit logs
├── ai-service        Python AI inference service (PyTorch / torchvision / YOLO)
├── mobile            React Native (Expo) mobile application
├── docs              Architecture, API, deployment, limitations/roadmap
├── k8s               Kubernetes manifests
├── nginx             Nginx reverse-proxy configuration
└── docker-compose.yml
```

## Quick Start

### 1. Start backend + AI service + database

```bash
docker-compose up --build
```

- API: http://localhost:8000
- AI service: http://localhost:8001
- API docs: http://localhost:8000/docs

### 2. Run the mobile app

```bash
cd mobile
npm install
npx expo start
```

Use the Expo Go app on Android/iOS, or run `i` / `a` in the terminal.

### 3. Seed manufacturer examples and pilot profiles

```bash
cd backend
DATABASE_URL=postgresql://... python scripts/seed_manufacturers.py
DATABASE_URL=postgresql://... python scripts/seed_pilot_profiles.py
```

## Training your own models

```bash
cd ai-service/datasets
python prepare_hf.py --dataset Project-AgML/fresh_rotten_fruit_classification --output ../data
python train.py --data-dir ../data/raw --output-dir ../checkpoints
```

## Continuous improvement workflow

1. Inspectors request a review from the mobile app when they disagree with an AI prediction.
2. Authorized reviewers approve or reject the request and set the correct label.
3. Export approved examples for offline retraining:

```bash
cd ai-service
BACKEND_URL=http://localhost:8000 BACKEND_TOKEN=<admin-token> \
  python scripts/build_feedback_dataset.py --output datasets/feedback
```

4. Run `datasets/train.py` on the feedback dataset, validate the new model, then deploy the updated `ai-service` image.

## Production build

### Mobile

```bash
cd mobile
npx eas build --platform android --profile production
npx eas build --platform ios --profile production
```

### Kubernetes

```bash
kubectl apply -f k8s/
```

Update `k8s/backend.yaml` and `k8s/postgres.yaml` with strong secrets before deploying.

## Limitations and sensor roadmap

See [docs/LIMITATIONS_AND_ROADMAP.md](docs/LIMITATIONS_AND_ROADMAP.md) for what the smartphone camera can realistically detect and how NIR, hyperspectral, thermal, Bluetooth, RFID, NFC, and IoT sensors can be integrated in future releases.

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## API

See [docs/API.md](docs/API.md).

## Release readiness, deployment, pilot, and roadmap

- [docs/RELEASE_READINESS.md](docs/RELEASE_READINESS.md) — test results, model metrics, benchmarks, limitations, and v1.0.0 roadmap.
- [docs/DEPLOYMENT_CHECKLIST.md](docs/DEPLOYMENT_CHECKLIST.md) — step-by-step production deployment checklist.
- [docs/PILOT_PLAN.md](docs/PILOT_PLAN.md) — recommended phased pilot plan and pilot-readiness checklist.
- [docs/V1_ROADMAP.md](docs/V1_ROADMAP.md) — detailed roadmap to Version 1.0.0.
- [docs/VALIDATION_AND_REGULATORY.md](docs/VALIDATION_AND_REGULATORY.md) — validation methodology, dataset description, limitations, and risk assessment.
- [docs/DEVICE_TESTING.md](docs/DEVICE_TESTING.md) — real device testing protocol and `PerformanceProfiler` usage.
- [docs/SECURITY_AUDIT.md](docs/SECURITY_AUDIT.md) — RC1 security audit findings and remediations.
- [docs/OPERATIONS_GUIDE.md](docs/OPERATIONS_GUIDE.md) — user, inspector, admin, deployment, DR, and AI model management guides.
- [docs/PILOT_METRICS.md](docs/PILOT_METRICS.md) — measurable pilot success criteria and go/no-go gates.
- [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md) — final sign-off checklist for Version 1.0.0.
- [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md) — current RC1 Maintenance Mode status and release path.
- [docs/AI_GOVERNANCE.md](docs/AI_GOVERNANCE.md) — model cards, validation, promotion, and retirement policy.
- [docs/DATASET_STRATEGY.md](docs/DATASET_STRATEGY.md) — long-term dataset collection, annotation, and retraining policy.
- [docs/MAINTENANCE.md](docs/MAINTENANCE.md) — Maintenance Mode rules, allowed changes, and weekly/monthly tasks.
- [docs/diagrams/README.md](docs/diagrams/README.md) — system, database, sequence, AI, mobile, backend, deployment, and security architecture diagrams.
- [docs/business/README.md](docs/business/README.md) — executive overview, product brochure, technical white paper, pilot proposal, implementation and training guides, FAQ.
- [BRANCHING.md](BRANCHING.md) — branch freeze, versioning, and release policy.
- [INTELLECTUAL_PROPERTY.md](INTELLECTUAL_PROPERTY.md) — copyright, ownership, trademarks, third-party licences.
- [CHANGELOG.md](CHANGELOG.md), [CONTRIBUTORS.md](CONTRIBUTORS.md), [LESSONS_LEARNED.md](LESSONS_LEARNED.md).

## License

Proprietary — all rights reserved. See [INTELLECTUAL_PROPERTY.md](INTELLECTUAL_PROPERTY.md) for copyright, third-party licences, and open-source attributions.
