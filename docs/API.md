# API Reference

**Status:** Engineering Complete — Release Candidate 1 (RC1) — Pilot Evaluation and Maintenance Mode. Base URLs and endpoints are stable for RC1.

Base URL: `http://localhost:8000`

## Auth

### POST /auth/register

Register a new inspector user.

```json
{
  "email": "inspector@example.com",
  "full_name": "Jane Inspector",
  "password": "securepassword",
  "role": "government_inspector",
  "organization": "Dept of Health",
  "company_id": "...",
  "branch_id": "..."
}
```

### POST /auth/login

Returns JWT access token.

```json
{
  "email": "inspector@example.com",
  "password": "securepassword"
}
```

## Scans

### POST /scans/analyze

Analyze an uploaded product image.

- `image` (file, required)
- `product_name` (string, optional)
- `category` (string, optional)
- `barcode_code` (string, optional)
- `batch_number` (string, optional)
- `production_date` (ISO datetime, optional)
- `expiry_date` (ISO datetime, optional)
- `latitude` (float, optional)
- `longitude` (float, optional)
- `company_id` (UUID, optional)
- `branch_id` (UUID, optional)
- `device_id` (UUID, optional)

Requires `Authorization: Bearer <token>`.

Returns a `ScanResult` including `condition`, `confidence`, `product_name`, `category`, `packaging_type`, `findings`, `expiry_risk`, `barcode_code`, `ai_vs_label_discrepancy`, `image_path`, and `created_at`.

### GET /scans/

List recent scans.

### GET /scans/{scan_id}

Get a single scan.

## Products / Barcodes

### GET /products/barcodes/{code}

Look up a barcode. First checks the local database, then falls back to Open Food Facts and stores the result.

### POST /products/barcodes

Create a barcode entry manually.

### GET /products/

List products.

### POST /products/

Create a product.

### GET /products/manufacturers

List manufacturers.

### POST /products/manufacturers

Create a manufacturer.

## Reports

### POST /reports/?format=pdf

Generate a report for a scan.

```json
{
  "scan_id": "<uuid>",
  "notes": "Sample note",
  "include_signature": false,
  "signature_data": "data:image/png;base64,..."
}
```

Supported `format`: `pdf`, `csv`, `excel`.

### GET /reports/

List reports.

### GET /reports/{report_id}

Get report metadata.

## Dashboard & Analytics

### GET /dashboard/stats

Return aggregate inspection statistics.

### GET /analytics/

Return full analytics: stats, expired by category, manufacturer trends, time series, and geographic distribution.

## Reviews (continuous AI improvement)

### POST /reviews/

Request a review of an AI prediction.

```json
{
  "scan_id": "<uuid>",
  "suggested_condition": "fresh",
  "reviewer_notes": "Looks fresh to me"
}
```

### GET /reviews/

List review requests.

### PATCH /reviews/{review_id}

Approve or reject a review request.

```json
{
  "status": "approved",
  "approved_label": "fresh",
  "reviewer_notes": "Confirmed fresh"
}
```

### GET /reviews/export

Export approved review examples for offline retraining (admin only).

## Admin

All endpoints require `administrator` or `company_admin` role.

### Companies

- `POST /admin/companies`
- `GET /admin/companies`

### Branches

- `POST /admin/branches`
- `GET /admin/branches?company_id=...`

### Devices

- `POST /admin/devices`
- `GET /admin/devices?branch_id=...`

### Inspectors

- `POST /admin/inspectors`
- `GET /admin/inspectors`

## Admin Audit Logs

### GET /admin/audit-logs/

List authentication and scan audit events. Restricted to users with the `administrator` role.
