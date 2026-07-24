# Project Status

**Current status: Release Candidate 1 (RC1) — Pilot Evaluation Phase**

The Smart Consumable Scanner AI is a real, functional application with a working AI inference pipeline, backend, mobile app, and deployment scaffolding. It is ready for controlled pilot deployments.

It is **not yet Version 1.0.0 production-ready**. The following must be completed before declaring production readiness:

1. Controlled pilot deployments with real inspectors and organisations.
2. Collection of a sufficiently large, expert-labelled, representative dataset.
3. Retraining and validation of AI models to meet the F1 and performance targets in `PILOT_METRICS.md`.
4. Resolution or documented acceptance of all critical/high security vulnerabilities.
5. Completion of the release checklist in `RELEASE_CHECKLIST.md`.
6. Sign-off from engineering, AI/ML, security, QA, product, and a pilot site representative.

## Release path

- `RC1` (current) — controlled pilot deployments begin.
- `RC2` (if required) — after pilot feedback and model improvements.
- `v1.0.0` — production release only after the checklist is complete and signed off.

## What works today

- Camera-first product inspection with real AI classification and explanation.
- Barcode/QR scanning with Open Food Facts integration and expiry-vs-AI discrepancy flagging.
- Inspector accept/override workflow for human-in-the-loop validation.
- Enterprise reporting (PDF/CSV/Excel), audit logs, RBAC, and multi-organisation support.
- Dataset, training, validation, explainability, benchmarking, and model registry scaffolding.
- Operational monitoring and pilot success metrics.

## Current limitations

- The smartphone camera can only assess observable external characteristics. It cannot detect internal spoilage, odour, or chemical contamination in sealed or opaque products.
- Model accuracy reported so far is based on small public datasets and must be validated on a large, representative, expert-labelled dataset before production claims are made.
- NIR, hyperspectral, thermal, Bluetooth, RFID, NFC, and IoT integrations are on the roadmap but not yet implemented.

See `PILOT_PLAN.md`, `PILOT_METRICS.md`, `RELEASE_CHECKLIST.md`, `SECURITY_AUDIT.md`, and `VALIDATION_AND_REGULATORY.md` for the complete gate-to-release documentation.
