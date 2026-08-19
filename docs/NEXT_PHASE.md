# Next Phase — Pilot Validation & Version 1.0.0 Readiness

**Status:** Engineering Complete — RC1 Maintenance Mode.

The engineering phase is complete. The next phase is not more feature development; it is **pilot validation and evidence gathering**. The goal is to prove the system works in real organisations and to collect the labelled data, customer acceptance, and operational evidence required for a responsible `v1.0.0` production release.

## Phase goal

Validate the RC1 baseline with real inspectors and products, improve the AI on representative data, and complete the `docs/RELEASE_CHECKLIST.md` so that a go/no-go decision for `v1.0.0` can be made.

## 1. Pilot operations

1. **Recruit pilot partners**
   - Schools and school nutrition programmes.
   - Supermarkets and retail stores.
   - Warehouses, wholesalers, and food manufacturers.
   - Restaurants and hotels.
   - Municipal health departments and government inspectors.

2. **Deploy RC1**
   - Provision backend and AI service.
   - Configure pilot profile for each organisation type.
   - Onboard users, branches, and devices.
   - Train inspectors and reviewers.

3. **Collect evidence**
   - Inspection statistics.
   - Inspector feedback (accept/override reasons).
   - False positives and false negatives.
   - Crash reports and device metrics.
   - Performance benchmarks on real devices and networks.
   - System uptime and sync success.

4. **Generate reports**
   - Weekly: `backend/scripts/pilot_weekly_report.py`.
   - Monthly: `backend/scripts/pilot_monthly_report.py`.
   - Ad-hoc: false-positive and false-negative analysis.

## 2. Dataset and AI validation

1. **Collect expert-labelled images**
   - Fresh, near expiry, expired, damaged packaging.
   - Diverse lighting, angles, cameras, and manufacturers.
   - Minimum targets in `docs/DATASET_STRATEGY.md`.

2. **Quality check**
   - Run `ai-service/datasets/quality.py`.
   - Remove duplicates, blur, and corruption.
   - Balance classes.

3. **Retrain offline**
   - Use `ai-service/datasets/train.py`.
   - Stratified k-fold cross-validation.
   - Hyperparameter tuning with Optuna.

4. **Evaluate and explain**
   - `ai-service/scripts/evaluate_models.py`.
   - `ai-service/scripts/explain.py` for Grad-CAM and calibration.
   - Compare per-class F1, precision, recall, and ECE against active model.

5. **Promote only if improved**
   - Register candidate in `/model-registry`.
   - Promotion blocked unless new score >= active score (or explicit `force=true`).
   - Keep previous model available for rollback.

## 3. Release readiness

Complete every item in `docs/RELEASE_CHECKLIST.md`:

- Functional testing with real users.
- Security review and production hardening.
- Performance benchmarks on target devices.
- AI validation results on representative data.
- Documentation review.
- Accessibility review.
- Localization review.
- Backup and recovery verification.
- Deployment verification.
- Pilot sign-off.

## 4. Research backlog for Version 1.1.0

These items are **not to be implemented during the pilot validation phase**. They are approved candidates for future investigation once `v1.0.0` is released or explicitly prioritised.

| # | Item | Value | Feasibility | Notes |
|---|------|-------|-------------|-------|
| 1 | Near-Infrared (NIR) camera integration | Detect internal spoilage non-destructively | Medium | Requires specialised hardware and labelled NIR datasets. |
| 2 | Hyperspectral imaging | Rich spectral signatures for freshness and contamination | Low-Medium | Expensive hardware; research use. |
| 3 | Thermal imaging | Detect temperature anomalies, thaw/refreeze | Medium | Requires thermal camera attachment. |
| 4 | Specialised food inspection hardware | pH, VOC, gas, and temperature probes | Medium | Bluetooth/USB sensor integration. |
| 5 | Bluetooth/USB sensor integration | Real-time auxiliary measurements | High | Add sensor abstraction layer in AI service. |
| 6 | ERP integration | Pull product master and batch data | High | Standard REST/SOAP connectors. |
| 7 | Warehouse Management System integration | Receiving, put-away, and dispatch checks | High | WMS-specific APIs. |
| 8 | Retail POS integration | Point-of-sale expiry alerts | Medium | POS vendor APIs. |
| 9 | GS1 product information integration | Trusted manufacturer and product data | High | GS1 Digital Link / GDSN. |
| 10 | Inventory lifecycle prediction | Predict shelf-life depletion | Medium | Time-series and inventory data. |
| 11 | Shelf-life forecasting using AI | Estimate remaining freshness | Medium | Requires labelled time-series data. |
| 12 | Predictive quality analytics | Trending and early warning | High | Aggregate inspection and IoT data. |
| 13 | Federated learning | Privacy-preserving model improvement across organisations | Low-Medium | Research project; legal and technical complexity. |
| 14 | Edge AI optimisation | On-device inference for low-latency offline scanning | High | TFLite/ONNX Runtime deployment; requires device testing. |

## 5. Milestone plan

| Milestone | Target | Success criteria |
|-----------|--------|------------------|
| Pilot 1 | Q3 | 1 site, ≥500 inspections, weekly reports stable. |
| Dataset v2 | Q3 | ≥1,000 new approved labels covering target categories. |
| Retrained model | Q4 | F1 meets `PILOT_METRICS.md` targets on held-out test set. |
| Pilot 2 | Q4 | 2–3 sites, ≥2,000 inspections, model improved over RC1. |
| v1.0.0 release gate | Q4/Q1 | `RELEASE_CHECKLIST.md` signed off and customer acceptance obtained. |
| v1.1.0 planning | After v1.0.0 | Approved roadmap items from research backlog. |

## 6. Decision criteria for moving out of pilot

The project stays in pilot validation until:

- AI performance meets `docs/PILOT_METRICS.md` targets on representative data.
- At least one pilot organisation provides formal acceptance.
- `docs/RELEASE_CHECKLIST.md` is fully signed off.
- Critical/high defects are closed.
- Production environment is verified.

Only then can `v1.0.0` be tagged and the project move into production support and Version 1.1.0 planning.
