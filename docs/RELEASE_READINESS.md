# Release Readiness — Phase 4 Validation & Version 1.0.0 Roadmap

This document consolidates test results, model evaluation metrics, performance benchmarks, deployment readiness, known limitations, a recommended pilot plan, and the roadmap toward a production 1.0.0 release.

## 1. Test Results

### Automated test suite

```bash
python -m pytest backend/ai_scanner/tests ai-service/ai_service/tests -q
```

Result: **2 passed** (backend health + AI service health/classifier smoke tests).

### Mobile type-check

```bash
cd mobile && npx tsc --noEmit
```

Result: **No TypeScript errors**.

### End-to-end smoke tests

All executed against a running backend (`localhost:8000`) and AI service (`localhost:8001`):

| Test | Input | Expected | Result |
|------|-------|----------|--------|
| Fresh produce | `/tmp/apple.png` | `condition: fresh`, `category: produce` | PASS |
| Spoiled produce | `/tmp/rotten_apple.png` | `condition: expired`, `category: produce` | PASS |
| Expiry/AI discrepancy | rotten image + future printed expiry | `ai_vs_label_discrepancy: true` | PASS |
| Barcode lookup | `737628064502` | Returns product name from Open Food Facts | PASS |
| PDF report generation | `/reports/?format=pdf` then `/reports/{id}/download` | Returns valid PDF file | PASS |
| Admin CRUD | `POST /admin/companies` + `GET /admin/companies` | Company created and listed | PASS |
| Review workflow | `POST /reviews/` + `GET /reviews/` | Review request persisted | PASS |
| Analytics | `GET /analytics/` | Stats, category expiry, trends, geo distribution | PASS |

## 2. Model Evaluation Metrics

The real AI pipeline (`ai_service/app/models/real_classifier.py`) was evaluated with `ai-service/scripts/evaluate_models.py`.

### Test set

Because the project is in pre-release, the current labelled set is small:

- `/tmp/apple.png` — ground-truth `fresh`
- `/tmp/rotten_apple.png` — ground-truth `expired`

Both images were evaluated with the product hint `apple` so the spoilage classifier (the most relevant model head) was exercised.

### Results

```json
{
  "summary": {
    "total_images": 2,
    "accuracy": 1.0,
    "device": "cpu"
  },
  "per_class_metrics": {
    "fresh":    {"precision": 1.0, "recall": 1.0, "f1": 1.0, "support": 1},
    "expired":  {"precision": 1.0, "recall": 1.0, "f1": 1.0, "support": 1},
    "near_expiry": {"precision": 0.0, "recall": 0.0, "f1": 0.0, "support": 0},
    "suspicious":  {"precision": 0.0, "recall": 0.0, "f1": 0.0, "support": 0}
  }
}
```

### How to reproduce and expand

```bash
cd ai-service
python scripts/evaluate_models.py --test-dir datasets/test --output reports/model_evaluation.json
```

To expand metrics before production, create a directory:

```
datasets/test/fresh/
datasets/test/near_expiry/
datasets/test/suspicious/
datasets/test/expired/
```

 populated with representative images for each supported product class and condition. The evaluation script will then produce a full confusion matrix and per-class precision/recall/F1.

## 3. Performance Benchmarks

### Model-only inference (CPU)

Run:

```bash
cd ai-service
python scripts/benchmark_models.py --image /tmp/apple.png --runs 20
```

Latest result:

```json
{
  "device": "cpu",
  "model_load_time_sec": 0.4,
  "total_trainable_parameters": 9515429,
  "checkpoint_size_mb": 4.23,
  "yolo_size_mb": 6.23,
  "mean_ms": 327.7,
  "min_ms": 201.03,
  "max_ms": 1848.6,
  "p50_ms": 244.75,
  "p95_ms": 1848.6,
  "throughput_rps": 3.05
}
```

Notes:

- First inference after model load is slow (PyTorch model warm-up, graph compilation, cache effects); subsequent calls stabilize around 200–350 ms on CPU.
- On a modest CPU this supports roughly **3 full end-to-end scans per second**, which is acceptable for a single AI service pod. GPU deployment is expected to improve this to >20 scans/second.

### End-to-end API benchmark

Run:

```bash
cd backend
python scripts/benchmark_api.py --image /tmp/apple.png --runs 20
```

Latest result (5 runs):

```json
{
  "endpoint": "http://localhost:8000/scans/analyze",
  "runs": 5,
  "mean_ms": 412.52,
  "min_ms": 396.82,
  "max_ms": 448.6,
  "p50_ms": 400.72,
  "p95_ms": 448.6,
  "throughput_rps": 2.42
}
```

The API overhead (upload, auth, DB writes, serialization) adds ~80–120 ms on top of model inference.

### Mobile bundle size (estimated)

| Component | Approximate size |
|-----------|------------------|
| React Native + Expo runtime + deps | ~45–60 MB |
| `expo-camera`, `expo-location`, maps, charts | +15 MB |
| TensorFlow Lite / ONNX runtime (future on-device) | +5–20 MB |
| Total first install | **65–95 MB** |

## 4. Deployment Checklist

### Pre-deployment

- [ ] **Secrets**: generate strong `SECRET_KEY`, `DATABASE_URL`, Postgres credentials, and JWT signing key. Do not commit secrets.
- [ ] **Database**: run migrations/create tables; prefer PostgreSQL for production.
- [ ] **Object storage**: configure S3-compatible bucket for report files and images instead of local disk.
- [ ] **SSL/TLS**: terminate HTTPS at Nginx/ingress; backend uses HTTP internally only inside the cluster.
- [ ] **Domain & DNS**: point `api.smartscanner.example.com` and `app.smartscanner.example.com` to the ingress/load balancer.
- [ ] **EAS build**: configure `mobile/eas.json` with production build profile and Apple/Google credentials.
- [ ] **Play/App Store**: prepare store listings, screenshots, privacy policy, and terms of service.

### Kubernetes production

- [ ] Apply `k8s/namespace.yaml`, `k8s/postgres.yaml`, `k8s/backend.yaml`, `k8s/ai-service.yaml`, `k8s/ingress.yaml`.
- [ ] Set resource requests/limits for AI service (CPU/GPU nodes recommended).
- [ ] Configure horizontal pod autoscaling (HPA) for backend and AI service.
- [ ] Set `DATABASE_URL` to managed PostgreSQL or the in-cluster Postgres service.
- [ ] Mount persistent volume for report/image storage or use object storage.

### Security & compliance

- [ ] Rotate default passwords and disable test accounts (`phase3@example.com`, `admin3@example.com`).
- [ ] Enable audit logging and ship logs to a SIEM.
- [ ] Review RBAC roles; avoid granting `administrator` to field inspectors.
- [ ] Perform dependency audit (`npm audit`, `pip audit` / `safety`) and patch high/critical issues.
- [ ] Add rate limiting and DDoS protection at the ingress.

### Monitoring & reliability

- [ ] Configure health checks (`/health`) and readiness/liveness probes.
- [ ] Add application monitoring (Prometheus/Grafana or Datadog).
- [ ] Set up error tracking (Sentry) for backend and mobile.
- [ ] Configure log aggregation and alerting for AI service failures.
- [ ] Define RTO/RPO and implement database backups.

### Post-deployment validation

- [ ] Run smoke tests against the production API.
- [ ] Verify mobile app can scan, generate reports, and sync offline queue.
- [ ] Test report downloads (PDF/CSV/Excel) and QR codes.
- [ ] Confirm analytics dashboards render correctly.

## 5. Known Limitations for v1.0.0

### AI / camera limitations

- The smartphone camera can assess **surface appearance and packaging condition** only.
- It **cannot reliably determine internal spoilage** of sealed or opaque products (cans, cartons, vacuum packs, frozen blocks, opaque bottles).
- It **cannot detect smell, bacterial load, gas composition, or true chemical expiry**.
- For sealed products, the system flags only visible packaging damage, swelling, leaks, or label/expiry discrepancies.

### Model scope

- Spoilage classifier is currently strongest for exposed fruits/vegetables (where colour and texture are highly informative).
- Meat, dairy, seafood, and frozen product classification relies more on packaging analysis and user-provided metadata.
- Confidence scores are real, but the training dataset is small; broader per-class validation is required before high-stakes enforcement use.

### Dataset and evaluation

- Only 2 labelled examples were available for the Phase 4 report. The accuracy figure is therefore **not statistically representative** of production performance.
- A full production validation must include hundreds to thousands of labelled examples across all target categories and conditions.

### Mobile

- Barcode/QR scanning depends on `expo-camera` and device camera quality; low-light conditions reduce scan reliability.
- On-device inference is not yet enabled; the app requires network connectivity to the AI service.
- Offline mode stores scans locally and syncs when online, but AI analysis is deferred until connectivity returns.

### Backend

- SQLite is supported for local/offline development; production should use PostgreSQL.
- Local filesystem storage for images/reports is not horizontally scalable; object storage is recommended.

## 6. Recommended Pilot Plan

### Phase A — Internal validation (2–4 weeks)

- Run the app internally with the QA and data-science teams.
- Capture at least 500 labelled images across produce, packaged goods, and beverages.
- Use `ai-service/scripts/evaluate_models.py` to re-measure precision/recall/F1.
- Fix model/regression issues and tune confidence thresholds.

### Phase B — Friendly single-site pilot (4–6 weeks)

- Deploy to one partner: a supermarket, school kitchen, or small warehouse.
- Train 5–10 inspectors on the workflow (scan → review → report).
- Collect inspector feedback and review requests; feed approved corrections into the retraining pipeline.
- Measure report generation, sync reliability, and dashboard usage.

### Phase C — Municipal / government inspector pilot (4–6 weeks)

- Invite 2–3 municipal health inspectors or food-safety officers.
- Focus on expired-product detection and discrepancy flagging.
- Validate GPS map, audit logs, and PDF reports for compliance use.

### Phase D — Multi-organization scaled pilot (8–12 weeks)

- Add 3–5 companies with branches and devices.
- Test multi-tenant isolation, role-based access, and device registration.
- Run load tests with concurrent inspectors.

### Go / no-go criteria for v1.0.0

| Criterion | Minimum target |
|-------------|----------------|
| Per-class F1 (produce) | ≥ 0.85 |
| Per-class F1 (packaged/beverages) | ≥ 0.70 |
| End-to-end p95 latency (CPU) | ≤ 1000 ms |
| Uptime (production environment) | ≥ 99.5% |
| Report generation success rate | ≥ 99% |
| Inspector satisfaction (NPS) | ≥ 40 |

## 7. Roadmap to Version 1.0.0 Production Release

| Quarter | Milestone | Key deliverables |
|---------|-----------|------------------|
| **Now – Q1** | Validation & dataset | Expand labelled dataset to ≥5,000 images, run per-class evaluation, improve model, add data augmentation. |
| **Q1 – Q2** | Hardening | PostgreSQL by default, object storage, rate limiting, security audit, dependency patching, CI/CD. |
| **Q2** | Pilot I | Single-site pilots (supermarket/school), feedback loop, offline-first mobile improvements. |
| **Q2 – Q3** | Pilot II | Government inspector pilot, multi-organization/branch support, compliance reporting. |
| **Q3** | Sensors & on-device | ONNX/TFLite export, optional on-device spoilage inference, barcode/QR/NFC/RFID integration scaffolding. |
| **Q3 – Q4** | Scale & certify | Load testing, HPA, monitoring, backup/DR, documentation, training material, production release 1.0.0. |

### Post-1.0.0 roadmap (not blocking initial release)

- Integration with NIR/hyperspectral/thermal camera attachments.
- Bluetooth/USB pH, VOC, and gas sensor support.
- IoT warehouse temperature/humidity telemetry correlation.
- Blockchain or traceability-API integration for provenance verification.

## 8. Recommendation

The Phase 3 feature set is **functionally complete** for an enterprise inspection MVP. Before presenting to real organizations, complete the validation steps above — especially dataset expansion, per-class model evaluation, and a supervised single-site pilot. The architecture supports production scaling, and all AI inferences are real and auditable.
