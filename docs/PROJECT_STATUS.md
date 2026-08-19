# Project Status

**Project:** Smart Consumable Scanner AI

**Current status:**

- ✅ Engineering Complete
- ✅ Release Candidate 1 (RC1) — Stable
- ✅ Pilot-1 baseline
- ✅ Maintenance Mode
- ✅ `main` branch frozen; all changes via PR
- ⏳ Awaiting real pilot deployments
- ⏳ Awaiting expert-labelled dataset expansion
- ⏳ Awaiting independent AI validation
- ⏳ Awaiting Version 1.0.0 Production Approval

## Summary

The engineering phase is complete. The repository contains a real, functional application with a working AI inference pipeline, FastAPI backend, React Native/Expo mobile app, and deployment scaffolding. It is frozen as the RC1 Engineering Baseline and is ready for controlled pilot deployments.

It is **not yet Version 1.0.0 production-ready**. The following must be completed before declaring production readiness:

1. Successful pilot deployments with real inspectors and organisations.
2. Collection of a sufficiently large, expert-labelled, representative dataset.
3. Retraining and validation of AI models to meet the F1 and performance targets in `PILOT_METRICS.md`.
4. Resolution or documented acceptance of all critical/high security vulnerabilities.
5. Completion of the release checklist in `RELEASE_CHECKLIST.md`.
6. Sign-off from engineering, AI/ML, security, QA, product, and a pilot site representative.
7. Customer acceptance from at least one pilot organisation.
8. Production environment verification (Kubernetes, TLS, backups, monitoring, Node `>=20.19.4`).

## Release path

- `RC1-Stable` — stable RC1 engineering baseline.
- `Pilot-1` — first pilot deployment snapshot.
- `Engineering-Complete-RC1` — engineering milestone freeze.
- `RC2` (if required) — after pilot feedback and model improvements.
- `v1.0.0` — production release only after all gates are met.

## What works today

- Camera-first product inspection with real AI classification and explanation.
- Barcode/QR scanning with Open Food Facts integration and expiry-vs-AI discrepancy flagging.
- Inspector accept/override workflow for human-in-the-loop validation.
- Enterprise reporting (PDF/CSV/Excel), audit logs, RBAC, and multi-organisation support.
- Dataset, training, validation, explainability, benchmarking, and model registry scaffolding.
- Operational monitoring and pilot success metrics.
- Weekly and monthly pilot reporting scripts.

## Current limitations

- The smartphone camera can only assess observable external characteristics. It cannot detect internal spoilage, odour, or chemical contamination in sealed or opaque products.
- Model accuracy reported so far is based on small public datasets and must be validated on a large, representative, expert-labelled dataset before production claims are made.
- NIR, hyperspectral, thermal, Bluetooth, RFID, NFC, and IoT integrations are on the research backlog and not yet implemented.

## Key documents

- `docs/FINAL_ENGINEERING_REPORT.md` — engineering completion summary.
- `docs/FINAL_FEATURE_MATRIX.md` — full feature status.
- `docs/KNOWN_LIMITATIONS.md` — current limitations.
- `docs/RELEASE_DECISION.md` — go/no-go and release gates.
- `docs/NEXT_PHASE.md` — pilot validation plan and v1.1 research backlog.
- `docs/RELEASE_CHECKLIST.md` — gates for `v1.0.0`.
- `docs/PILOT_PLAN.md` / `PILOT_METRICS.md` — pilot approach and targets.
- `docs/SECURITY_AUDIT.md` — security findings and remediations.
- `docs/VALIDATION_AND_REGULATORY.md` — validation methodology.
- `docs/LIMITATIONS_AND_ROADMAP.md` — capabilities, limitations, and future sensor roadmap.
- `BRANCHING.md` — branch freeze, versioning, and release policy.
- `MAINTENANCE.md` — Maintenance Mode rules.
- `INTELLECTUAL_PROPERTY.md` — copyright and third-party licences.
