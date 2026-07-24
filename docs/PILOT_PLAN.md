# Recommended Pilot Plan

This plan moves Smart Consumable Scanner AI from validated MVP to production-ready deployment through four low-risk, iterative pilots.

## Phase A — Internal validation (2–4 weeks)

**Goal:** find and fix critical bugs before external users see the app.

- QA and data-science teams use the app daily.
- Capture ≥500 labelled inspection images across produce, packaged goods, and beverages.
- Run `ai-service/scripts/evaluate_models.py` weekly and track per-class F1.
- Tune confidence thresholds and update `docs/LIMITATIONS_AND_ROADMAP.md` with observed failure modes.

## Phase B — Friendly single-site pilot (4–6 weeks)

**Goal:** validate real-world workflow and UX.

- Select one partner: a supermarket, school kitchen, small warehouse, or restaurant.
- Train 5–10 inspectors on scan → review → report workflow.
- Collect review requests and inspector notes.
- Measure:
  - Scan success rate
  - Report generation success rate
  - Time per inspection
  - Inspector satisfaction

## Phase C — Municipal / government inspector pilot (4–6 weeks)

**Goal:** validate compliance and audit use cases.

- Invite 2–3 municipal health inspectors or food-safety officers.
- Focus on expired-product detection and discrepancy flagging.
- Validate:
  - PDF/Excel reports with QR codes and signatures
  - GPS map of inspections
  - Audit logs and role-based access
  - Multi-language UI support

## Phase D — Multi-organization scaled pilot (8–12 weeks)

**Goal:** validate multi-tenancy and scale.

- Add 3–5 companies with branches and registered devices.
- Test company/branch isolation and company-admin workflows.
- Run concurrent load tests with `backend/scripts/benchmark_api.py`.
- Refine analytics dashboards and time-series insights.

## Go / no-go criteria for v1.0.0

| Criterion | Minimum target | Measurement |
|-----------|----------------|-------------|
| Produce F1 | ≥ 0.85 | `ai-service/scripts/evaluate_models.py` on a held-out labelled set |
| Packaged/beverage F1 | ≥ 0.70 | Same as above |
| End-to-end p95 latency | ≤ 1000 ms on CPU | `backend/scripts/benchmark_api.py` |
| Uptime | ≥ 99.5% | Monitoring dashboard |
| Report generation success | ≥ 99% | Backend logs / analytics |
| Inspector NPS | ≥ 40 | Weekly survey |

If all criteria are met, proceed to full production release 1.0.0.

## Pilot Readiness Checklist

Before inviting external pilot users:

- [ ] `download_datasets.py` has been run and the local `data/raw` folder contains representative categories and conditions.
- [ ] `quality.py` has been executed and all corrupted, duplicate, and blurred images have been reviewed.
- [ ] `benchmark_backbones.py` has selected the best architecture for the target devices.
- [ ] `train.py` has produced a frozen checkpoint with per-class F1 meeting the go/no-go criteria.
- [ ] `evaluate_models.py` reports the same metrics on a held-out test set as `train.py` reports on validation.
- [ ] `explain.py` generates Grad-CAM overlays and top-k explanations for at least one image per class.
- [ ] `calibrate` produces a reliability diagram with ECE < 0.1.
- [ ] Mobile `PerformanceProfiler` has been tested on at least one low-end, one mid-range, and one flagship device.
- [ ] `docs/VALIDATION_AND_REGULATORY.md` has been updated with the final dataset size, model version, and risk assessment.
- [ ] Pilot user agreements, data-consent forms, and incident-response contacts are in place.
- [ ] A weekly feedback and review cadence is scheduled.

## Pilot Feedback Workflow

1. Inspector scans product and records AI result.
2. Inspector can flag `Disagree` and add a note/image through the review workflow.
3. Authorised reviewer inspects the flagged case and assigns a corrected label.
4. Approved corrections are exported with `ai-service/scripts/build_feedback_dataset.py`.
5. Quarterly offline retraining run creates a new model candidate.
6. Model candidate is validated on a held-out test set before replacing the production checkpoint.

## Release Candidate Gate

Only after the pilot data has been collected, the model retrained and validated, and the device matrix tested should the project be tagged:

- `v1.0.0-rc1` — first pilot release candidate.
- `v1.0.0-rc2` — second release candidate after pilot fixes.
- `v1.0.0` — final production release.

