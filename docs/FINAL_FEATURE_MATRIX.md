# Final Feature Matrix — Smart Consumable Scanner AI

**Status:** Engineering Complete — RC1 Maintenance Mode.

## Legend

- ✅ Implemented
- ⚠️ Partial / scaffolding only
- ⏳ Future (v1.1.0+)
- ❌ Not applicable

## Mobile application

| Feature | Status | Notes |
|---------|--------|-------|
| Live camera preview | ✅ | `expo-camera` with automatic capture and quality validation. |
| Real-time object detection | ✅ | Bounding box from backend AI service. |
| Automatic product classification | ✅ | Product category and name returned by AI service. |
| Image quality validation | ✅ | Blur/size checks before upload. |
| Barcode / QR scanning | ✅ | Reads codes and sends to backend for product lookup. |
| GPS location capture | ✅ | `expo-location`. |
| Offline scan queue | ✅ | Queues scans and syncs when online. |
| Inspector accept / override | ✅ | With reason and optional photos. |
| Dashboard | ✅ | Bar chart, confidence trend, map. |
| Inspection history | ✅ | Lists past scans and conditions. |
| Reports (PDF/CSV/Excel) | ✅ | Downloads generated reports from backend. |
| Multi-language UI | ⚠️ | i18n scaffolding for 11 SA languages; not all translations reviewed by native speakers. |
| On-device AI inference | ⏳ | Architecture supports it; server-side inference in RC1. |
| NFC / RFID scanning | ⏳ | Roadmap item. |
| Thermal / NIR camera | ⏳ | Roadmap item; requires specialised hardware validation. |

## Backend

| Feature | Status | Notes |
|---------|--------|-------|
| JWT authentication | ✅ | Access and refresh tokens. |
| Password policy | ✅ | Minimum 8 chars, one letter and one digit. |
| Role-based access control | ✅ | Admin, company_admin, inspector, reviewer, consumer. |
| Rate limiting | ✅ | `slowapi` on auth, scans, reports. |
| Audit logging | ✅ | Every action logged with user, resource, and IP. |
| Companies / branches / devices | ✅ | Multi-organisation support. |
| User management | ✅ | CRUD via admin endpoints; shared `user_service`. |
| Pilot profiles | ✅ | Configurable settings, branding, and workflows per organisation type. |
| Scan workflow | ✅ | Capture, AI analysis, discrepancy flagging, feedback. |
| Review queue | ✅ | Reviewer accept/reject with approved labels. |
| Reports | ✅ | PDF, CSV, Excel with QR code and signature. |
| Analytics | ✅ | Category, manufacturer, time-series, geographic dashboards. |
| Monitoring | ✅ | Operational and pilot success metrics endpoints. |
| Model registry | ✅ | Register, promote, rollback, score-based promotion guard. |
| Manufacturer KB | ✅ | CRUD and seed data. |
| Barcode / Open Food Facts integration | ✅ | Lookup and discrepancy flagging. |
| PostgreSQL support | ✅ | SQLAlchemy with PostgreSQL/SQLite. |

## AI service

| Feature | Status | Notes |
|---------|--------|-------|
| YOLOv8 object detection | ✅ | Detects product region and primary packaging. |
| EfficientNet-B0 classification | ✅ | Product category and name. |
| MobileNetV3-Small spoilage classifier | ✅ | Condition scoring. |
| OpenCV packaging/bruise/mould analysis | ✅ | Surface and packaging cues. |
| Explainable findings | ✅ | Top-k reasons returned in every scan. |
| Grad-CAM | ✅ | `ai-service/scripts/explain.py` generates overlays. |
| Confidence calibration / ECE | ✅ | Reliability diagrams and ECE reported. |
| ONNX export | ✅ | Best model exported where `onnx` is available. |
| Dataset downloader | ✅ | Public dataset ingestion script. |
| Dataset quality validation | ✅ | Blur, corruption, duplicate, class-balance checks. |
| Stratified k-fold training | ✅ | `ai-service/datasets/train.py`. |
| Hyperparameter search (Optuna) | ✅ | Optional HPO. |
| Multi-backbone benchmark | ✅ | EfficientNet, MobileNet, ConvNeXt, ViT. |
| Model registration helper | ✅ | `ai-service/scripts/register_model.py`. |
| On-device TFLite export | ⚠️ | `export_mobile_models.py` scaffolding; not validated on physical devices. |

## DevOps and deployment

| Feature | Status | Notes |
|---------|--------|-------|
| Docker Compose (dev) | ✅ | `docker-compose.yml`. |
| Docker Compose (prod) | ✅ | `docker-compose.prod.yml`. |
| Kubernetes manifests | ✅ | `k8s/` directory. |
| Nginx reverse proxy | ✅ | `nginx/` directory. |
| EAS build config | ✅ | `mobile/eas.json`. |
| CI/CD pipeline | ⏳ | GitHub Actions or similar to be added during v1.0.0 readiness. |

## Documentation

| Document | Status |
|----------|--------|
| README.md | ✅ |
| CHANGELOG.md | ✅ |
| CONTRIBUTORS.md | ✅ |
| LESSONS_LEARNED.md | ✅ |
| MAINTENANCE.md | ✅ |
| BRANCHING.md | ✅ |
| INTELLECTUAL_PROPERTY.md | ✅ |
| docs/PROJECT_STATUS.md | ✅ |
| docs/RELEASE_CHECKLIST.md | ✅ |
| docs/RELEASE_READINESS.md | ✅ |
| docs/PILOT_PLAN.md / PILOT_METRICS.md | ✅ |
| docs/SECURITY_AUDIT.md | ✅ |
| docs/VALIDATION_AND_REGULATORY.md | ✅ |
| docs/OPERATIONS_GUIDE.md | ✅ |
| docs/DEVICE_TESTING.md | ✅ |
| docs/ARCHITECTURE.md | ✅ |
| docs/API.md | ✅ |
| docs/DEPLOYMENT_CHECKLIST.md | ✅ |
| docs/LIMITATIONS_AND_ROADMAP.md | ✅ |
| docs/V1_ROADMAP.md | ✅ |
| docs/AI_GOVERNANCE.md | ✅ |
| docs/DATASET_STRATEGY.md | ✅ |
| docs/diagrams/* | ✅ |
| docs/business/* | ✅ |
| docs/FINAL_ENGINEERING_REPORT.md | ✅ |
| docs/FINAL_FEATURE_MATRIX.md | ✅ |

## Notable exclusions

The following are not in RC1 and are reserved for the v1.1 research backlog:

- Near-Infrared (NIR) camera support.
- Hyperspectral imaging.
- Thermal imaging.
- Bluetooth/USB sensor integration.
- ERP / WMS / retail POS integration.
- Federated learning.
- Inventory lifecycle prediction and shelf-life forecasting.

See `docs/NEXT_PHASE.md` for the research backlog.
