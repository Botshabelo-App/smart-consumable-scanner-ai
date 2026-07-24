# Production Deployment Checklist

**Status:** Engineering Complete — Release Candidate 1 (RC1) — Pilot Evaluation and Maintenance Mode. Use this checklist before deploying to a pilot environment; complete the final `RELEASE_CHECKLIST.md` before tagging `v1.0.0`.

## Infrastructure

- [ ] Provision Kubernetes cluster or Docker host(s).
- [ ] Configure managed PostgreSQL or deploy `k8s/postgres.yaml` with persistent volume.
- [ ] Configure S3-compatible object storage for images and reports (or use a persistent shared volume).
- [ ] Set up Nginx / cloud load balancer and ingress with TLS termination.
- [ ] Register DNS names for API, dashboard, and mobile update endpoints.
- [ ] Configure firewall rules (allow 443/80, restrict internal DB/AI service ports).

## Secrets & configuration

- [ ] Generate and store `SECRET_KEY` (JWT signing).
- [ ] Set `DATABASE_URL` and `AI_SERVICE_URL` in `backend/.env` / `k8s/backend.yaml`.
- [ ] Create Postgres credentials; use Kubernetes secrets or a vault.
- [ ] Configure `EXPO_PUBLIC_API_URL` / `API_BASE_URL` in mobile build configuration.
- [ ] Do NOT commit secrets, `.env` files, or credentials to Git.

## Build & deploy

- [ ] Build and push backend Docker image.
- [ ] Build and push AI service Docker image.
- [ ] Run Alembic/migration or create tables if using SQLAlchemy `create_all`.
- [ ] Seed manufacturers: `python backend/scripts/seed_manufacturers.py`.
- [ ] Apply `k8s/` manifests in order: namespace, postgres, backend, ai-service, ingress.
- [ ] Verify `/health` on backend and AI service.

## Mobile release

- [ ] Configure `mobile/eas.json` production profile.
- [ ] Update app metadata, icon, splash screen, and store screenshots.
- [ ] Submit Android build to Google Play Console.
- [ ] Submit iOS build to App Store Connect.
- [ ] Enable OTA updates via EAS Update (optional).

## Security

- [ ] Remove test users (`phase3@example.com`, `admin3@example.com`, etc.).
- [ ] Enforce strong password policy and role assignment.
- [ ] Enable audit logging; forward logs to SIEM.
- [ ] Run `npm audit` and `pip audit` / `safety`; patch high/critical findings.
- [ ] Add rate limiting at ingress and/or backend.
- [ ] Verify RBAC endpoints deny access for lower-privilege roles.

## Monitoring & reliability

- [ ] Configure liveness/readiness probes in Kubernetes.
- [ ] Add application metrics (Prometheus/Grafana or SaaS).
- [ ] Add error tracking (Sentry) for backend and mobile.
- [ ] Set up log aggregation and alerting on AI service failures.
- [ ] Configure automated PostgreSQL backups and test restore.
- [ ] Define RTO/RPO and document incident response runbook.

## Scalability

- [ ] Configure HPA for backend and AI service based on CPU/memory.
- [ ] Run load test (`backend/scripts/benchmark_api.py`) against production-like environment.
- [ ] Confirm object storage scales across multiple backend pods.
- [ ] Set AI service resource requests/limits; schedule on GPU nodes if available.

## Pre-launch validation

- [ ] Run `pytest` and `npx tsc --noEmit` against the release branch.
- [ ] Perform end-to-end scan → report → analytics on staging.
- [ ] Verify PDF/CSV/Excel reports download and open correctly.
- [ ] Test barcode/QR scanning on iOS and Android devices.
- [ ] Confirm offline scan queue syncs when connectivity returns.
- [ ] Review `docs/LIMITATIONS_AND_ROADMAP.md` and `docs/RELEASE_READINESS.md` with stakeholders.

## Post-launch

- [ ] Monitor error rates and latency for 48 hours.
- [ ] Onboard first pilot users with training session.
- [ ] Collect feedback and review requests weekly.
- [ ] Export approved reviews for offline model retraining monthly.
