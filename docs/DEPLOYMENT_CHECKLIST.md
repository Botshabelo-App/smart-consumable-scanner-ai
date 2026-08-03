# Production Deployment Checklist

**Status:** Engineering Complete — Release Candidate 1 (RC1) — Pilot Evaluation and Maintenance Mode. Use this checklist before deploying to a pilot environment; complete the final `RELEASE_CHECKLIST.md` before tagging `v1.0.0`.

## Pilot / temporary backend

- The RC1 private pilot currently runs through a Cloudflare quick tunnel started with `cloudflared tunnel --url http://localhost:8003` (the local backend listens on port 8003).
- This URL is temporary and changes whenever the tunnel process restarts; it is suitable only for private pilot testing, not production.
- To keep the tunnel stable, run `cloudflared` under a process supervisor (e.g., `systemd`, `pm2`, or `tmux`) and monitor `/health` on the public URL.

## Permanent deployment options

When the pilot is successful, choose one of these managed platforms and deploy the combined backend (`main.py`) plus a managed PostgreSQL database:

- **Render** — a `render.yaml` Blueprint is included in the repo root. Add a payment method in the Render dashboard, then run `render blueprint apply` to create a Docker web service and a `basic_256mb` Postgres database. The Blueprint uses `DATABASE_URL` from the database and auto-generates `SECRET_KEY`.
- **Railway** — create a project from the GitHub repo, add a Postgres service, and set the environment variables `DATABASE_URL`, `AI_SERVICE_URL`, `SECRET_KEY`, and `CORS_ORIGINS`.
- **Fly.io** — use `fly launch` with the provided `Dockerfile` and attach a Fly Postgres service. The built-in `deploy backend` tool was not usable in this environment, so manual `flyctl` deployment is recommended.
- **AWS / Azure / GCP** — deploy the Docker image to an EC2/VM or container service (ECS, App Service, Cloud Run) with a managed Postgres instance and a load balancer handling TLS.

For all options:

- Use the combined `Dockerfile` in the repo root, which bundles the FastAPI backend and the AI inference service in one container.
- Set `DATABASE_URL` to a persistent Postgres URL (not SQLite).
- Generate a strong `SECRET_KEY` and set `CORS_ORIGINS` to the public origin(s) of the mobile app.
- Build the mobile app with the permanent backend URL in `mobile/src/config/brand.ts` and upload the rebuilt APK to the download page.

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
