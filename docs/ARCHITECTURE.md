# Architecture

## Overview

Smart Consumable Scanner AI is composed of three primary deployable units:

1. **Mobile App** (`mobile/`) — React Native + Expo cross-platform app.
2. **Backend API** (`backend/`) — FastAPI monolith for auth, scan storage, reporting, dashboards.
3. **AI Inference Service** (`ai-service/`) — Python microservice for image analysis using TensorFlow/PyTorch/OpenCV.

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Mobile    │────▶│   Backend    │────▶│ AI Service  │
│  (Expo/RN)  │     │  (FastAPI)   │     │  (FastAPI)  │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ PostgreSQL   │
                    │ SQLite       │
                    │ (offline)    │
                    └──────────────┘
```

## Component Responsibilities

### Mobile App

- Live camera preview (`expo-camera`).
- Capture high-resolution frames.
- GPS tagging (`expo-location`).
- Upload image + metadata to backend.
- Display AI result with emoji-coded condition.
- Generate and download reports.
- Offline queue support (future).

### Backend

- User registration/login with JWT.
- Role-based user model.
- Persist scans, products, reports.
- Orchestrate AI analysis by calling `ai-service`.
- Generate PDF, CSV, Excel reports.
- Provide dashboard statistics.
- Support both PostgreSQL (production) and SQLite (offline/development).

### AI Service

- Accept image uploads.
- Preprocess / resize images.
- Run classification with TensorFlow or PyTorch when installed, otherwise a deterministic dummy classifier.
- Return structured `ScanResult` (condition, confidence, findings, category, etc.).
- Pluggable for future NIR/hyperspectral/thermal inputs.

## Data Model

- **User** — email, full name, role, organization, hashed password.
- **Scan** — product metadata, AI condition, confidence, GPS, image path, inspector.
- **Report** — report ID, linked scan, format, file URL, notes, digital signature (future).

## Future Expansion

The architecture is intentionally modular so the following can be added without rewriting core logic:

- External sensors via Bluetooth/USB (AI service accepts additional input channels).
- NIR, hyperspectral, and thermal cameras (same inference pipeline, different preprocessors).
- Barcode/QR code scanning (mobile side, send decoded data to backend for batch lookup).
- RFID/NFC tags (mobile side, map to product metadata).
- IoT warehouse monitoring (backend can ingest sensor telemetry via a new ingestion endpoint).
