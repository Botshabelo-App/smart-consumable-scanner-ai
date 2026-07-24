# Final Engineering Report — Smart Consumable Scanner AI

**Date:** 2026-07-24  
**Project status:** Engineering Complete — Release Candidate 1 (RC1) — Pilot Evaluation and Maintenance Mode  
**Repository:** `Botshabelo-App/smart-consumable-scanner-ai`  
**Approved baseline tags:** `RC1-Stable`, `Pilot-1`, `Engineering-Complete-RC1`

## 1. Executive summary

The Smart Consumable Scanner AI engineering phase is complete. The repository contains a working cross-platform mobile application, a FastAPI backend, a Python AI inference service, a reproducible dataset and training pipeline, enterprise reporting, audit logging, RBAC, model registry, monitoring, and pilot-support tooling. All features have been implemented using real AI inference. No functionality is simulated or hardcoded.

The project is intentionally **not** released as Version 1.0.0. It is frozen as the RC1 Engineering Baseline while real-world pilot deployments, expert-labelled dataset collection, and independent AI validation take place.

## 2. Completed functionality

See `docs/FINAL_FEATURE_MATRIX.md` for the full feature list. Key deliverables include:

- Mobile app (React Native + Expo) with camera capture, barcode/QR scanning, GPS, offline queue, dashboards, and inspector accept/override workflow.
- FastAPI backend with JWT auth, RBAC, companies/branches/devices, scans, reports, analytics, reviews, audit logs, model registry, monitoring, and pilot profiles.
- AI service with YOLOv8 detection, EfficientNet-B0 product classification, MobileNetV3-Small spoilage analysis, OpenCV packaging analysis, and Grad-CAM explainability.
- Dataset pipeline: public dataset downloader, quality checks, stratified CV training, multi-backbone benchmarking, and ONNX export.
- Reporting: PDF, CSV, and Excel reports with QR code and signature.
- Deployment: Docker Compose, Kubernetes manifests, Nginx config, and EAS build config.

## 3. Architecture summary

See `docs/diagrams/` for system, database, sequence, AI, mobile, backend, deployment, and security architecture diagrams.

The architecture is composed of three deployable units:

1. **Mobile app** — React Native + Expo.
2. **Backend** — FastAPI + SQLAlchemy + PostgreSQL/SQLite + `slowapi` rate limiting.
3. **AI service** — Python + PyTorch + YOLOv8 + torchvision.

Communication is via HTTPS/REST. The backend stores images and reports in object storage or a shared volume. The AI service loads the active model from the model registry.

## 4. AI capabilities

- Detect and classify food, drinks, packaged goods, meat, dairy, produce, and other consumables.
- Score condition as fresh, near expiry, suspicious, expired, or damaged packaging.
- Explain predictions with top-k findings and Grad-CAM overlays.
- Calibrate confidence and report Expected Calibration Error (ECE).
- Compare printed expiry dates (via barcode/QR) with AI-detected condition and flag discrepancies for human review.

## 5. Current technical limitations

- The smartphone camera can only assess observable external characteristics.
- It cannot determine internal spoilage, odour, or chemical contamination of sealed or opaque products.
- Model accuracy has only been demonstrated on small public datasets and must be validated on larger, representative, expert-labelled pilot data before production claims.
- AI inference currently runs server-side; an optional on-device path is planned for post-1.0.0.

See `docs/KNOWN_LIMITATIONS.md` for the complete list.

## 6. Security status

- Branch protection enabled on `main`.
- `python-jose` removed and replaced with `PyJWT`.
- `fastapi`, `starlette`, `python-multipart`, `pydantic`, `pyjwt`, `pillow`, `pytest`, and `setuptools` upgraded to non-vulnerable versions.
- `pip-audit` reports **0** vulnerabilities.
- `npm audit --audit-level=high` reports **0** high/critical vulnerabilities (moderate transitive issues remain).
- CORS, rate limiting, password policy, JWT, RBAC, audit logging, and encrypted mobile token storage are implemented.

See `docs/SECURITY_AUDIT.md` for details.

## 7. Testing status

| Check | Result |
|-------|--------|
| `pytest` backend + AI service tests | 2 passed |
| `npx tsc --noEmit` mobile type check | passed |
| `npm audit --audit-level=high` | 0 high/critical |
| `pip-audit` | 0 vulnerabilities |
| `python -m py_compile` across backend/ai-service | passed |

End-to-end smoke testing was performed with fresh and rotten apple images, barcode lookup, report generation, and model registry promote/rollback.

## 8. Performance benchmarks

| Metric | Value | Source |
|--------|-------|--------|
| AI inference mean latency | 340.3 ms | `backend/scripts/benchmark_api.py` (10 runs, CPU) |
| AI inference p95 latency | 396.78 ms | `backend/scripts/benchmark_api.py` |
| AI service throughput | 2.64 requests/sec | `ai-service/reports/model_benchmark.json` |
| Model checkpoint size | 4.23 MB | `ai-service/reports/model_benchmark.json` |
| YOLO detection model size | 6.23 MB | `ai-service/reports/model_benchmark.json` |
| Total trainable parameters | 9.5 M | `ai-service/reports/model_benchmark.json` |

Mobile device benchmarks remain a pilot activity because they require physical devices in the target environments.

## 9. Release readiness

The `docs/RELEASE_CHECKLIST.md` contains the full list of gates. At the time of this report, the engineering checklist items are complete; the pilot and validation items (labelled datasets, independent AI validation, production environment verification, customer acceptance) are pending.

## 10. Outstanding risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Small labelled dataset | High | Pilot data collection + reviewer-approved retraining pipeline. |
| AI accuracy on real products | High | Controlled pilots, human-in-the-loop, model comparison before promotion. |
| Node.js version mismatch for Expo 57 | Medium | Update CI/build environment to Node `>=20.19.4` before production builds. |
| Production secrets/CORS misconfiguration | High | `RELEASE_CHECKLIST.md` hardening steps and production deployment review. |
| Regulatory acceptance of camera-only claims | Medium | Clear limitation statements and `docs/VALIDATION_AND_REGULATORY.md`. |

## 11. Recommended next actions

1. Recruit pilot partners and sign data-sharing agreements.
2. Deploy the RC1 backend and mobile app to each pilot site.
3. Train inspectors and reviewers on the accept/override workflow.
4. Collect expert-labelled images and metadata.
5. Generate weekly and monthly pilot reports with the provided scripts.
6. Retrain AI models offline after accumulating sufficient approved data.
7. Promote a new model only if it outperforms the active model.
8. Complete `docs/RELEASE_CHECKLIST.md` and obtain sign-off for `v1.0.0`.

## 12. Conclusion

The engineering baseline is complete, stable, and ready for pilot validation. No further feature development should occur unless it is required by pilot feedback, a critical security fix, a production defect, or an approved Version 1.1.0 roadmap item. The next milestone is real-world evidence, not more code.
