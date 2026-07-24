# Architecture

## Overview

Smart Consumable Scanner AI is composed of three primary deployable units:

1. **Mobile App** (`mobile/`) — React Native + Expo cross-platform app.
2. **Backend API** (`backend/`) — FastAPI monolith for auth, scan storage, reporting, dashboards, audit logs.
3. **AI Inference Service** (`ai-service/`) — Python microservice for image analysis using YOLO, EfficientNet, MobileNetV3, and OpenCV.

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

- Live camera preview (`expo-camera`) with continuous capture and multiple scan angles.
- Image quality validation before upload.
- GPS tagging (`expo-location`).
- Upload image + metadata to backend.
- Display AI result with color-coded condition and explainable `findings`.
- Generate and download reports.
- Encrypted local token storage (`expo-secure-store`) and offline scan queue.

### Backend

- User registration/login with JWT.
- Role-based user model and endpoint guards.
- Persist scans, products, reports, and audit logs.
- Orchestrate AI analysis by calling `ai-service`.
- Generate PDF, CSV, Excel reports.
- Provide dashboard statistics.
- Support both PostgreSQL (production) and SQLite (offline/development).

### AI Service

- Accept image uploads.
- Detect products with **YOLOv8** object detection.
- Classify product category with **EfficientNet-B0** (ImageNet-pretrained).
- Assess fresh/spoiled condition for exposed produce with a **MobileNetV3-Small** spoilage classifier.
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
EfficientNet-B0 classification  ──►  product name + category
    │
    ▼
MobileNetV3-Small spoilage score  ──►  P(spoiled)
    │
    ▼
OpenCV packaging/shape/color analysis  ──►  bruising, mold, swelling, damage
    │
    ▼
Explainable findings + final condition + confidence
```

## Data Model

- **User** — email, full name, role, organization, hashed password.
- **Scan** — product metadata, AI condition, confidence, packaging type, findings, expiry risk, GPS, image path, inspector.
- **Report** — report ID, linked scan, format, file URL, notes.
- **AuditLog** — user actions (login, scan, report) for compliance.

## Future Expansion

The architecture is intentionally modular so the following can be added without rewriting core logic:

- External sensors via Bluetooth/USB (AI service accepts additional input channels).
- NIR, hyperspectral, and thermal cameras (same inference pipeline, different preprocessors).
- Barcode/QR code scanning (mobile side, send decoded data to backend for batch lookup).
- RFID/NFC tags (mobile side, map to product metadata).
- IoT warehouse monitoring (backend can ingest sensor telemetry via a new ingestion endpoint).
- On-device TensorFlow Lite / ONNX Runtime inference for offline use.
