# Implementation Guide — Smart Consumable Scanner AI

**Status:** Engineering Complete — Release Candidate 1 (RC1) — Pilot Evaluation and Maintenance Mode.

## Overview

This guide is for IT administrators and DevOps engineers deploying the Smart Consumable Scanner AI for a pilot or production environment.

## 1. Infrastructure requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Backend host(s) | 1 CPU, 2 GB RAM | 2+ CPUs, 4 GB RAM, horizontal scaling |
| AI service host(s) | 1 CPU, 4 GB RAM, GPU optional | 4+ CPUs or 1 GPU for faster inference |
| Database | SQLite for single-node dev | PostgreSQL 14+ with TLS and backups |
| Object storage | Local filesystem | S3-compatible with encryption |
| Mobile | Android 8+ / iOS 14+ | Mid-range device with autofocus camera |
| Network | 4G/LTE or Wi-Fi | Stable Wi-Fi for image uploads |

## 2. Deployment options

### Docker Compose (development / small pilot)

```bash
docker-compose up --build
```

- API: http://localhost:8000
- AI service: http://localhost:8001

### Kubernetes (production pilot)

```bash
kubectl apply -f k8s/
```

Apply `k8s/postgres.yaml` or use a managed PostgreSQL service. Configure `backend-config` and `ai-service-config` ConfigMaps with `DATABASE_URL`, `AI_SERVICE_URL`, `SECRET_KEY`, and `CORS_ORIGINS`.

### Mobile app

1. Install dependencies: `cd mobile && npm install`.
2. Update `src/api.ts` `API_BASE` to point to the deployed backend.
3. Run `npx expo start` or build with EAS: `eas build --platform android`.

## 3. Configuration checklist

- [ ] Generate a 256-bit `SECRET_KEY` and store it as a secret.
- [ ] Set `CORS_ORIGINS` to exact production dashboard/mobile origins.
- [ ] Configure `DATABASE_URL` for PostgreSQL.
- [ ] Configure object-storage endpoint/credentials.
- [ ] Set `AI_SERVICE_URL` and ensure backend can reach it.
- [ ] Enable TLS termination (Nginx or cloud load balancer).
- [ ] Configure backup schedules for PostgreSQL and object storage.
- [ ] Set up log aggregation and alerting.

## 4. User onboarding

1. Create a company and branch via `/admin/companies` and `/admin/branches`.
2. Register an administrator with `POST /auth/register`.
3. Create inspectors via `POST /admin/inspectors`.
4. Register mobile devices via `/admin/devices`.
5. Optionally seed a pilot profile with `/pilot-profiles` and link it to the company.

## 5. Pilot-specific setup

1. Select a pilot profile matching the organisation type.
2. Configure the inspection workflow and branding JSON.
3. Train inspectors on the accept/override workflow.
4. Assign reviewer accounts for the review queue.
5. Schedule weekly pilot summary generation with `backend/scripts/pilot_weekly_report.py`.

## 6. Monitoring and support

- Health: `GET /health` on backend and AI service.
- Operational metrics: `GET /monitoring/operational`.
- Pilot metrics: `GET /monitoring/pilot`.
- Audit log: `/admin/audit-log`.

## 7. Troubleshooting

| Symptom | Check |
|---------|-------|
| Mobile cannot connect | `API_BASE`, CORS, TLS certificate. |
| AI inference slow | AI service resources, CPU vs GPU, model size. |
| Scans not syncing | Offline queue, network, backend `/scans` endpoint. |
| Reports fail | File storage permissions, disk space, object storage credentials. |
| Rate limit errors | `slowapi` config and legitimate traffic patterns. |

## 8. Going to production

Complete `docs/RELEASE_CHECKLIST.md` and sign off before tagging `v1.0.0`.
