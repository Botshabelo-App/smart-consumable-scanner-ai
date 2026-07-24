# Operations Guide — RC1

This guide covers user, inspector, administrator, deployment, troubleshooting, disaster recovery, backup/restore, AI model management, and data governance.

## 1. User Manual

### Getting started

1. Install the mobile app from the pilot build distribution.
2. Log in with the credentials supplied by your organisation administrator.
3. Grant camera, location, and storage permissions.
4. Select the organisation profile if prompted.

### Scanning a product

1. Point the camera at the product.
2. Tap **Capture** or enable **Continuous** for multiple angles.
3. (Optional) Scan the barcode for cross-check.
4. Tap **Analyze with AI**.
5. Review the condition, confidence, and findings.
6. Tap **Accept** if you agree, or **Override** if you disagree and record a reason.

### Viewing reports

- Open the **Reports** tab to see generated PDF/CSV/Excel reports.
- Tap a report to download or share.

## 2. Inspector Manual

### Inspection workflow

1. **Identify** the product and category.
2. **Capture** a clear image in good lighting.
3. **Verify** the AI result against your own visual assessment.
4. **Record** any override with a mandatory reason.
5. **Generate** a report when required.

### When to override

Override the AI when:

- The product is actually fresh but the AI flags it expired due to lighting.
- The packaging is damaged but the product itself appears intact (or vice versa).
- The AI cannot see through sealed/opaque packaging and the inspector has additional evidence.

### Do not rely on the AI alone

The AI assesses visible external characteristics. It cannot detect internal spoilage, odour, or chemical contamination. Use it as a decision-support tool only.

## 3. Administrator Guide

### Managing organisations

- Create companies and branches via `POST /admin/companies` and `POST /admin/branches`.
- Assign a pilot profile to a company with `POST /pilot-profiles/{id}/assign/{company_id}`.
- Register devices with `POST /admin/devices`.

### User management

- Create users through `POST /auth/register` (admin only).
- Assign roles (e.g., `school_food_inspector`, `supermarket_manager`).
- Deactivate users by setting `is_active=false`.

### Review workflow

- Inspectors submit review requests through `POST /reviews`.
- Authorised reviewers approve/reject with `PATCH /reviews/{id}`.
- Approved corrections are exported with `GET /reviews/export` for model retraining.

### Monitoring

- View operational metrics at `GET /monitoring/operational`.
- Track pilot success metrics at `GET /monitoring/pilot`.
- Review audit logs at `GET /admin/audit-logs`.

## 4. API Reference

The interactive OpenAPI documentation is available at `/docs` when the backend is running.

Key endpoint groups:

- `POST /auth/register` — create user
- `POST /auth/login` — obtain JWT
- `POST /scans/analyze` — analyse image
- `POST /scans/{id}/feedback` — accept or override AI result
- `GET /scans` — list scans
- `POST /reports` — generate report
- `GET /dashboard` — dashboard stats
- `GET /analytics` — analytics
- `GET /pilot-profiles` — deployment profiles
- `GET /model-registry` — AI model registry
- `GET /monitoring/operational` and `GET /monitoring/pilot` — metrics

See `docs/API.md` for additional detail.

## 5. Deployment Guide

### Backend

```bash
cd backend
cp .env.example .env  # edit SECRET_KEY, DATABASE_URL, AI_SERVICE_URL
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn ai_scanner.main:app --host 0.0.0.0 --port 8000
```

### AI service

```bash
cd ai-service
pip install -r requirements.txt
PYTHONPATH=ai-service uvicorn ai_service.main:app --host 0.0.0.0 --port 8001
```

### Mobile

```bash
cd mobile
npm install
npx expo start
```

### Production (Kubernetes)

See `docs/DEPLOYMENT_CHECKLIST.md` and `k8s/` manifests. Use PostgreSQL and object storage instead of SQLite/local disk.

## 6. Troubleshooting Guide

| Symptom | Likely cause | Resolution |
|---------|--------------|------------|
| Mobile shows `Analysis error` | AI service down or unreachable | Check `AI_SERVICE_URL`, ensure service is healthy at `/health` |
| Scan returns `expired` for fresh produce | Lighting, glare, or bruising | Re-capture with diffuse lighting and tap **Override** if wrong |
| Barcode scan fails | Low light or unsupported format | Use a clearer image or enter barcode manually |
| Reports not generating | Missing image or backend error | Check backend logs and `uploads/` directory permissions |
| Offline scans not syncing | No network or invalid token | Connect to network and re-login |
| Login rejected after password change | Token expired | Re-login |

## 7. Disaster Recovery

- **RTO:** 4 hours for backend, 24 hours for full AI pipeline.
- **RPO:** 1 hour for PostgreSQL with automated backups.
- Backup PostgreSQL daily and test restores monthly.
- Store model artifacts and images in replicated object storage.
- Keep a rollback model in the registry (`/model-registry/{id}/rollback`).
- Document incident runbook and on-call contacts.

## 8. Backup & Restore

### Database

```bash
# PostgreSQL backup
pg_dump $DATABASE_URL > scanner_$(date +%F).sql

# Restore
psql $DATABASE_URL < scanner_YYYY-MM-DD.sql
```

### Model artifacts

```bash
# Copy active model
cp ai-service/checkpoints/model.pth s3://models-backup/model-$(date +%F).pth
```

### Mobile app data

- Encourage users to sync before device replacement.
- Audit logs and scan images are server-side; no local backup needed.

## 9. AI Model Management Guide

1. **Train** a candidate using `ai-service/datasets/train.py`.
2. **Evaluate** with `ai-service/scripts/evaluate_models.py` on a held-out test set.
3. **Register** the candidate:
   ```bash
   curl -X POST $API/model-registry/ \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"model_id":"scsa-2026-07-24","version":"0.6.0-rc1","dataset_version":"pilot-001","training_date":"...","validation_metrics":{...},"supported_categories":["produce","dairy"],"artifact_path":"...","checksum":"..."}'
   ```
4. **Promote** to active: `POST /model-registry/{model_id}/promote`.
5. **Monitor** operational metrics and pilot success metrics.
6. **Rollback** if error rate spikes: `POST /model-registry/{model_id}/rollback`.
7. **Retrain** quarterly with approved inspector corrections.

## 10. Data Governance

- All images are stored with access logging and encrypted at rest.
- Labels and reviewer corrections are auditable.
- Users can only access data for their company/branch based on RBAC.
- Retention: scan images 90 days minimum or per local regulation; audit logs 2 years.
- Export approved review data for retraining only after anonymising PII where required.
- Comply with POPIA/GDPR for personal data and inspector location data.
