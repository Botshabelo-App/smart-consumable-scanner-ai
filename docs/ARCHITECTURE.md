# Architecture

**Status:** Engineering Complete — Release Candidate 1 (RC1) — Pilot Evaluation and Maintenance Mode.

## Overview

Smart Consumable Scanner AI is composed of three primary deployable units:

1. **Mobile App** (`mobile/`) — React Native + Expo cross-platform app.
2. **Backend API** (`backend/`) — FastAPI monolith for auth, scan storage, reporting, dashboards, audit logs, and enterprise admin.
3. **AI Inference Service** (`ai-service/`) — Python microservice for real image analysis using YOLO, EfficientNet, MobileNetV3, and OpenCV.

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Mobile    │────▶│   Backend    │────▶│ AI Service  │
│  (Expo/RN)  │     │  (FastAPI)   │     │  (FastAPI) │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ PostgreSQL  │
                    │ SQLite      │
                    │ (offline)   │
                    └──────────────┘
```

## Component Responsibilities

### Mobile App

- Live camera preview (`expo-camera`) with continuous capture, multiple scan angles, and in-app barcode/QR scanning.
- Image quality validation before upload.
- GPS tagging (`expo-location`).
- Upload image + metadata (barcode, batch, expiry, company/branch/device) to backend.
- Display AI result with color-coded condition, explainable `findings`, and AI-vs-label discrepancy warnings.
- Generate and download PDF/CSV/Excel reports.
- Request AI review when the inspector disagrees with the prediction.
- Encrypted local token storage (`expo-secure-store`) and offline scan queue.
- Multi-language support via `i18n-js` and `expo-localization`.

### Backend

- User registration/login with JWT.
- Role-based user model and endpoint guards.
- Multi-organization support: companies, branches, devices, inspectors.
- Manufacturer and product knowledge base with barcode lookup (Open Food Facts).
- Persist scans, products, reports, review requests, and audit logs.
- Orchestrate AI analysis by calling `ai-service`.
- Cross-check printed expiry dates with AI-detected condition and flag discrepancies for review.
- Generate PDF, CSV, Excel reports with QR code and optional digital signature.
- Provide dashboard and analytics endpoints.
- Support both PostgreSQL (production) and SQLite (offline/development).

### AI Service

- Accept image uploads.
- **Product-first recognition**:
  - YOLOv8 object detection.
  - EfficientNet-B0 product classification.
  - Map visual labels and optional barcode/hints to product name and category.
- Assess fresh/spoiled condition for exposed produce with a MobileNetV3-Small spoilage classifier.
- Analyze packaging condition with OpenCV contour and texture analysis.
- Return a structured `ScanResult` with `condition`, `confidence`, `findings`, `category`, `packaging_type`, etc.
- Document camera limitations for sealed/opaque products.
- Pluggable for future NIR/hyperspectral/thermal inputs and on-device TFLite/ONNX exports.

## AI Pipeline

```
Input image
    │
    ▼
YOLOv8 product detection  ──►  crop product region
    │
    ▼
EfficientNet-B0 product classification + barcode/hint lookup  ──►  product name + category
    │
    ▼
MobileNetV3-Small spoilage score  ──►  P(spoiled)
    │
    ▼
OpenCV packaging / color / texture analysis  ──►  bruising, mold, swelling, damage
    │
    ▼
Explainable findings + final condition + confidence
```

## Data Model

- **User** — email, full name, role, company/branch, organization, hashed password.
- **Company** — name, registration, contact details.
- **Branch** — company, name, location, GPS.
- **Device** — branch, name, platform, serial identifier.
- **Manufacturer** — name, country, website.
- **Product** — company/manufacturer, name, category, packaging type, default shelf life.
- **Barcode** — product, code, batch, production/expiry dates, source.
- **Scan** — product metadata, AI condition, confidence, packaging type, findings, expiry risk, barcode, batch, dates, discrepancy, GPS, image path, inspector.
- **Report** — report ID, linked scan, format, file URL, notes, signature.
- **ReviewRequest** — scan, suggested condition, reviewer notes, status, approved label, reviewer.
- **AuditLog** — user actions (login, scan, report, review) for compliance.

## Continuous Improvement Workflow

1. Inspector submits a `ReviewRequest` with a suggested condition.
2. An authorized reviewer updates the request with `status` (`approved`/`rejected`) and an `approved_label`.
3. Admins export approved reviews via `/reviews/export`.
4. `ai-service/scripts/build_feedback_dataset.py` copies approved images into `datasets/feedback/<condition>/`.
5. Data scientists run `datasets/train.py` offline, validate the model, and deploy a new `ai-service` image.

## Future Expansion

The architecture is intentionally modular so the following can be added without rewriting core logic:

- External sensors via Bluetooth/USB (AI service accepts additional input channels).
- NIR, hyperspectral, and thermal cameras (same inference pipeline, different preprocessors).
- Barcode/QR code scanning (mobile side, send decoded data to backend for batch lookup).
- RFID/NFC tags (mobile side, map to product metadata).
- IoT warehouse monitoring (backend can ingest sensor telemetry via a new ingestion endpoint).
- On-device TensorFlow Lite / ONNX Runtime inference for offline use.
