# Release Decision — Smart Consumable Scanner AI

**Project status:** Engineering Complete — Release Candidate 1 (RC1) — Pilot Evaluation and Maintenance Mode  
**Date:** 2026-07-24

## Decision

The engineering milestone is complete. The repository is frozen as the **RC1 Engineering Baseline**. **Version 1.0.0 is not released.**

The project will remain in RC1 Maintenance Mode and transition into pilot validation. No new functionality will be added unless it is:

- Required by pilot feedback.
- Required to fix a critical security defect.
- Required to fix a production defect discovered during pilot.
- Approved as part of Version 1.1.0 planning.

## Release gates for Version 1.0.0

The following must all be completed and signed off before `v1.0.0` can be tagged and declared production-ready:

1. **Successful pilot deployments** with at least one target organisation type (school, supermarket, warehouse, restaurant, manufacturer, or municipal inspector).
2. **Expert-labelled dataset expansion** — a representative dataset covering the target product categories, lighting conditions, cameras, and viewing angles.
3. **Independent AI validation** — per-class F1, precision, recall, ECE, and calibration on a held-out test set that meets the targets in `docs/PILOT_METRICS.md`.
4. **Release checklist signed off** — all items in `docs/RELEASE_CHECKLIST.md` completed and approved by engineering, AI/ML, security, QA, product, and a pilot site representative.
5. **Customer acceptance** — at least one pilot organisation signs a formal acceptance or go-live approval.
6. **Production environment verification** — Kubernetes/Nginx deployment, TLS, PostgreSQL, object storage, backups, monitoring, and build environment (Node `>=20.19.4`) verified.
7. **Critical and high-priority defects closed** — no open critical/high issues blocking production use.

## Current evidence

| Gate | Evidence | Status |
|------|----------|--------|
| Engineering complete | `docs/FINAL_ENGINEERING_REPORT.md`, `docs/FINAL_FEATURE_MATRIX.md` | ✅ Met |
| Branch frozen | `BRANCHING.md`, GitHub branch protection on `main` | ✅ Met |
| Security dependency scan | `pip-audit` 0 vulnerabilities, `npm audit` 0 high/critical | ✅ Met |
| Automated tests | `pytest` passed, `npx tsc --noEmit` passed | ✅ Met |
| Documentation | All major docs present and cross-checked | ✅ Met |
| Pilot data | Not yet collected | ⏳ Pending |
| Independent AI validation | Not yet performed | ⏳ Pending |
| Customer acceptance | Not yet obtained | ⏳ Pending |
| Production verification | Not yet performed | ⏳ Pending |

## Go / no-go

- **Go to pilot:** Yes. RC1 is approved for controlled pilot deployments.
- **Go to v1.0.0 production:** No. The project must complete the gates above first.

## Next milestone

**Pilot Validation & Version 1.0.0 Readiness**

- Recruit pilot partners.
- Deploy RC1.
- Collect data and feedback.
- Retrain and validate AI models offline.
- Complete `docs/RELEASE_CHECKLIST.md`.
- Make a new go/no-go decision for `v1.0.0`.

## Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Engineering Lead | | | |
| AI/ML Lead | | | |
| Security Lead | | | |
| QA Lead | | | |
| Product Owner | | | |
| Pilot Site Representative | | | |

## Version control

- `RC1-Stable` — stable RC1 baseline.
- `Pilot-1` — first pilot deployment snapshot.
- `Engineering-Complete-RC1` — engineering milestone freeze.
- `v1.0.0` — reserved for production release after all gates are met.
