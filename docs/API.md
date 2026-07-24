# API Reference

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
  "organization": "Dept of Health"
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
- `latitude` (float, optional)
- `longitude` (float, optional)

Requires `Authorization: Bearer <token>`.

Returns a `ScanResult` including `condition`, `confidence`, `product_name`, `category`, `packaging_type`, `findings`, `expiry_risk`, `image_path`, and `created_at`.

### GET /scans/

List recent scans.

### GET /scans/{scan_id}

Get a single scan.

## Reports

### POST /reports/?format=pdf

Generate a report for a scan.

```json
{
  "scan_id": "<uuid>",
  "notes": "Sample note",
  "include_signature": false
}
```

Supported `format`: `pdf`, `csv`, `excel`.

### GET /reports/

List reports.

### GET /reports/{report_id}

Get report metadata.

## Dashboard

### GET /dashboard/stats

Return aggregate inspection statistics.

## Admin

### GET /admin/audit-logs/

List authentication and scan audit events. Restricted to users with the `administrator` role.
