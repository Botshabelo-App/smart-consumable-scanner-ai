# Final Release Checklist — Version 1.0.0

This checklist must be completed and signed off before tagging `v1.0.0`.

## 1. Functional testing

- [ ] All user roles can log in and view role-appropriate screens.
- [ ] Camera capture, image quality validation, and AI analysis work end-to-end.
- [ ] Inspector can accept or override AI assessment with a reason.
- [ ] Barcode/QR scan and Open Food Facts lookup return expected product data.
- [ ] Discrepancy between printed expiry and AI condition is flagged for review.
- [ ] PDF, CSV, and Excel reports generate correctly with QR code and signature.
- [ ] Dashboard, analytics, and monitoring endpoints return accurate data.
- [ ] Offline scan queue syncs when connectivity returns.
- [ ] Multi-language UI strings display for all 11 South African languages.

## 2. Security review

- [ ] `SECRET_KEY` is a 256-bit random value stored in a secret manager.
- [ ] `CORS_ORIGINS` is restricted to production dashboard/mobile domains.
- [ ] Rate limiting is enabled and verified (`slowapi`).
- [ ] Password policy enforced on registration.
- [ ] `PyJWT` is used for tokens; `python-jose` removed.
- [ ] `npm audit` shows no high or critical vulnerabilities in mobile dependencies.
- [ ] Backend `pip-audit` shows no unpatched critical vulnerabilities.
- [ ] HTTPS/TLS enforced in production (Nginx / load balancer).
- [ ] Database credentials rotated and stored as secrets.
- [ ] Container images scanned and free of known critical CVEs.

## 3. Performance benchmarks

- [ ] `backend/scripts/benchmark_api.py` passes at expected concurrency.
- [ ] AI service p95 inference latency is documented for CPU and GPU targets.
- [ ] Mobile scan latency ≤ 2.5 s on mid-range Wi-Fi.
- [ ] Battery and temperature measured on low-end, mid-range, and flagship devices.
- [ ] Offline sync completes within 5 minutes of connectivity restoration for ≤100 queued scans.

## 4. AI validation results

- [ ] Training dataset version, size, and categories documented in model registry.
- [ ] Model checkpoint passed `ai-service/scripts/evaluate_models.py` on a held-out test set.
- [ ] Produce F1 ≥ 0.85 on held-out data.
- [ ] Packaged/beverage F1 ≥ 0.70 on held-out data.
- [ ] `explain.py` Grad-CAM and calibration reports generated for each class.
- [ ] ECE < 0.1 or documented calibration limitations.
- [ ] New model score is equal to or better than the previous active model before promotion.

## 5. Documentation review

- [ ] `README.md` reflects current RC1 Maintenance Mode status and points to all relevant docs.
- [ ] `docs/PROJECT_STATUS.md` and `MAINTENANCE.md` are consistent with `README.md`.
- [ ] `docs/OPERATIONS_GUIDE.md` reviewed by at least one pilot administrator.
- [ ] `docs/SECURITY_AUDIT.md` remediations completed or accepted with sign-off.
- [ ] `docs/PILOT_METRICS.md` targets understood by pilot team.
- [ ] `docs/VALIDATION_AND_REGULATORY.md` updated with final dataset and model details.
- [ ] `docs/AI_GOVERNANCE.md` and `docs/DATASET_STRATEGY.md` reviewed and approved.
- [ ] `docs/LIMITATIONS_AND_ROADMAP.md` clearly states camera-only limitations.

## 6. Accessibility review

- [ ] Mobile screens usable with device font scaling up to 200%.
- [ ] Color-coded condition states also use text labels and icons.
- [ ] Form fields have clear labels and error messages.
- [ ] Screen reader labels added to critical actions (capture, accept, override).

## 7. Localization review

- [ ] All 11 SA language files present in `mobile/src/locales/`.
- [ ] Default fallback to English when a translation is missing.
- [ ] Date/number formatting respects locale where applicable.
- [ ] Key inspector-facing terms reviewed by a native speaker where possible.

## 8. Backup and recovery verification

- [ ] PostgreSQL automated daily backups configured and tested restore.
- [ ] Model artifacts and images stored in replicated object storage.
- [ ] Disaster-recovery runbook executed at least once.
- [ ] RTO and RPO documented and validated.

## 9. Deployment verification

- [ ] Kubernetes manifests applied to a staging cluster.
- [ ] Nginx reverse proxy terminates TLS and forwards correctly.
- [ ] AI service scales horizontally behind the backend.
- [ ] Health checks (`/health`) pass for all services.
- [ ] Log aggregation and alerting configured.
- [ ] EAS production build succeeded for Android (and iOS if applicable).
- [ ] Build environment uses Node.js version supported by Expo SDK 57 / React Native 0.86 (>=20.19.4).

## 10. Pilot sign-off

- [ ] Pilot success criteria in `docs/PILOT_METRICS.md` met for at least one full site cycle.
- [ ] Weekly pilot summaries reviewed and signed off by project stakeholders.
- [ ] No unresolved critical or high-severity issues.
- [ ] Rollback plan to previous model version tested.

## Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Engineering Lead | | | |
| AI/ML Lead | | | |
| Security Lead | | | |
| QA Lead | | | |
| Product Owner | | | |
| Pilot Site Representative | | | |

## Release decision

- [ ] Approve release of Version 1.0.0
- [ ] Require RC2 and additional pilot evaluation
- [ ] Block release until critical issues resolved

Only tag `v1.0.0` after all applicable boxes are checked and signed off.
