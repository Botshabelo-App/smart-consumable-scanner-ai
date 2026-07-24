# Roadmap to Version 1.0.0 Production Release

This roadmap turns the Phase 3 enterprise MVP into a production-grade release.

## Current state (end of Phase 3)

- Real AI inference pipeline (YOLOv8, EfficientNet-B0, MobileNetV3, OpenCV).
- Backend with auth, RBAC, multi-organization, reports, analytics, reviews, and audit logs.
- Mobile app with camera, barcode scanning, dashboards, and localization scaffolding.
- Kubernetes, Nginx, Docker Compose, and EAS deployment configurations.
- Initial test results, evaluation metrics, and benchmarks documented.

## Milestones to v1.0.0

### 1. Dataset expansion & model validation

- Expand labelled dataset to ≥5,000 images covering all Phase 3 categories and conditions.
- Add data augmentation and class-balancing.
- Run per-class evaluation with `ai-service/scripts/evaluate_models.py`.
- Retrain or fine-tune the spoilage classifier on the expanded dataset.
- Freeze model versioning and checksums before release.

### 2. Infrastructure hardening

- Make PostgreSQL the default database.
- Replace local filesystem image/report storage with S3-compatible object storage.
- Add rate limiting, DDoS protection, and security headers.
- Patch all high/critical dependency vulnerabilities.
- Add CI/CD pipeline (lint, test, build, deploy).

### 3. Pilot programs

- Phase A: internal validation.
- Phase B: single-site friendly pilot (supermarket/school/warehouse).
- Phase C: government/municipal inspector pilot.
- Phase D: multi-organization scaled pilot.
- Collect feedback, review requests, and approved labels for retraining.

### 4. Mobile & offline improvements

- Stabilize barcode/QR scanning across devices and lighting conditions.
- Improve offline scan queue sync and conflict resolution.
- Add biometric or PIN app lock.
- Complete translations for all 11 South African languages.

### 5. On-device inference (optional for v1.0.0, required for offline-first v1.x)

- Export spoilage classifier to TFLite/ONNX using `ai-service/scripts/export_mobile_models.py`.
- Add optional on-device inference path in the mobile app.
- Sync results when online and fall back to server for unknown product classes.

### 6. Production readiness validation

- Load testing with `backend/scripts/benchmark_api.py` at expected concurrency.
- Penetration testing and security audit.
- Backup/restore and disaster-recovery testing.
- Documentation review and inspector training material.

### 7. Launch v1.0.0

- Tag release `v1.0.0`.
- Publish mobile apps to Play Store and App Store.
- Deploy production backend and AI service to managed Kubernetes.
- Onboard first paying/contracted organizations.

## Post-1.0.0 roadmap

- NIR, hyperspectral, and thermal camera integration.
- Bluetooth/USB pH, VOC, and gas sensor support.
- RFID/NFC tag reading for product traceability.
- IoT warehouse temperature/humidity correlation.
- Advanced analytics: predictive expiry, anomaly detection, and automated alerting.
