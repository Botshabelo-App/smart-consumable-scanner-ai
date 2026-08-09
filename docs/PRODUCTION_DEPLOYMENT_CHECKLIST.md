# Smart Consumable Scanner AI — Production Deployment Checklist

This checklist is used once real-device and real-product pilot validation is complete. Do **not** deploy permanently until the pilot has been signed off.

## Production application requirements

The production app must be:

- Organisation-agnostic (no hard-coded Department of Education branding)
- Locked to the same logo, app name, and branding until the client explicitly approves a change
- Able to scan any packaged consumable with a barcode or QR code
- Able to continue inspection when the barcode/QR is missing or unknown
- Able to cross-check barcode/QR data against OCR and visual inspection
- Cautious in AI language ("possible", "suspicious", "needs manual inspection")
- Hosted on a permanent, always-on HTTPS service with automatic recovery

## 1. Pre-deployment validation

- [ ] Real-device pilot results reviewed (minimum 5 Android devices)
- [ ] Real-product pilot results reviewed (minimum one product per category)
- [ ] Critical bugs from pilot resolved
- [ ] Security audit passed
- [ ] Performance budget met (startup < 3 s, scan < 5 s on mid-range device)
- [ ] APK size and signing verified
- [ ] Branding/logo change explicitly approved or explicitly kept as pilot

## 2. Hosting options and monthly cost estimates

These are representative prices for a small-to-medium pilot/production workload. Prices are subject to the provider and region; confirm before paying.

| Service | Provider | Instance/plan | Est. monthly cost (USD) | Notes |
|---------|----------|---------------|---------------------------|-------|
| Web/API + AI | Render | Web service (Starter) + Postgres (Basic 256 MB) | ~$13 | Simplest if a payment method is added. |
| Web/API + AI | Railway | Starter plan + managed Postgres | $0–$20+ | Usage-based; scales with traffic. |
| Web/API + AI | Fly.io | `shared-cpu-1x` (256 MB) + 1 GB Postgres | ~$3–$5 | Very cost-effective; pay-as-you-go. |
| Web/API + AI | AWS (EC2 + RDS) | `t3.small` + `db.t3.micro` Postgres | ~$25–$40 | More setup, more control. |
| Web/API + AI | Azure | App Service B1 + Azure Database for Postgres Basic | ~$30–$50 | Managed, easy scaling. |
| Web/API + AI | Google Cloud | Cloud Run + Cloud SQL Postgres | $0–$30 | Scales to zero, pay per request. |
| Object storage | AWS S3 / Backblaze B2 / Cloudflare R2 | Scan images + PDF reports | ~$0–$5 | Backblaze B2 and R2 are cheapest. |
| CDN | Cloudflare | Free plan | $0 | Caching and custom DNS. |
| Domain (optional) | Namecheap / Cloudflare | `smartscanner.yourdomain` | ~$10–$15 / year | Use only if a custom domain is required. |

### Recommended minimal production stack

For the Department of Education pilot/production transition, the recommended minimum is:

- **Fly.io** or **Render** for the FastAPI/AI backend and managed Postgres.
- **Cloudflare R2** or **Backblaze B2** for scan images and generated reports.
- **Cloudflare Free** for DNS/SSL if a custom domain is used.

Estimated monthly cost: **$5–$20** for the first 1–5 inspectors, depending on traffic.

## 3. Required credentials and accounts

Before deployment, the following must be available:

- [ ] Cloud provider account with billing enabled
- [ ] Provider API token or IAM credentials scoped to create services and databases
- [ ] S3-compatible object storage keys (if not using the provider’s built-in storage)
- [ ] SMTP or transactional email service (optional, for user invitations)
- [ ] Crash/error reporting service (optional, e.g., Sentry)

## 4. Deployment steps

1. Create the managed database and apply migrations.
2. Build the backend Docker image or deploy the `main.py` combined service.
3. Set environment variables:
   - `DATABASE_URL`
   - `SECRET_KEY`
   - `AI_SERVICE_URL` (or run AI in-process)
   - `CORS_ORIGINS`
   - `STORAGE_ENDPOINT`, `STORAGE_KEY`, `STORAGE_SECRET` (if using object storage)
4. Verify `/health` returns HTTP 200.
5. Verify `/auth/login` returns a valid JWT.
6. Verify `/scans/analyze` with a test image returns a valid result.
7. Verify `/reports/?format=pdf` generates a PDF.
8. Build the release APK with the permanent backend URL pre-configured.
9. Sign the APK with the production keystore.
10. Upload the APK to the download page/object storage and record the SHA-256.
11. Run smoke tests on a real Android device.

## 5. Post-deployment checks

- [ ] Public backend URL is HTTPS and reachable 24/7.
- [ ] APK download link returns HTTP 200.
- [ ] SHA-256 of published APK matches the tested APK.
- [ ] Health monitor or uptime service is in place.
- [ ] Automated backups for the database are configured.
- [ ] Logs and crash reports are captured.
- [ ] SSL certificate is valid and auto-renewed.

## 6. Go-live criteria

The production build may go live when:

- Pilot validation report is approved.
- Hosting plan and budget are approved.
- Required credentials are provided.
- All deployment steps are completed and verified on a real device.
- A rollback plan exists (previous APK and backend version kept).
