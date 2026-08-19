# Training Guide — Smart Consumable Scanner AI

**Status:** Engineering Complete — Release Candidate 1 (RC1) — Pilot Evaluation and Maintenance Mode.

## Who should read this

Inspectors, reviewers, administrators, and pilot coordinators using the Smart Consumable Scanner AI mobile app and dashboard.

## Inspector workflow

### 1. Log in

Open the mobile app, enter your email and password. Your token is stored securely on the device.

### 2. Capture a product

- Centre the product in the camera preview.
- Ensure good lighting.
- If scanning a barcode or QR code, point the camera at the code until it is recognised.
- Tap the capture button. The app validates image quality before sending it.

### 3. Review the AI result

The app displays:

- Detected product name and category.
- Condition (fresh, near expiry, suspicious, expired, damaged packaging).
- Confidence score.
- Explainable findings (e.g., "normal colour", "possible mould", "packaging swelling").
- Captured location and timestamp.

### 4. Accept or override

- **Accept** if the AI result matches your assessment.
- **Override** if you disagree. Choose the correct condition and enter a reason. You may attach additional photos.

> Important: your override creates a review request and helps improve the AI. Always provide a clear reason.

### 5. Generate a report (optional)

Tap the report icon to generate a PDF, CSV, or Excel report. The report includes the product image, AI analysis, GPS location, inspector name, signature, and a unique report ID with QR code.

## Reviewer workflow

1. Open the review queue in the dashboard.
2. Examine the image, AI result, and inspector reason.
3. Assign an `approved_label` if the override is correct.
4. Mark the request as `approved` or `rejected`.
5. Approved examples are collected for the next training dataset.

## Administrator workflow

- Create companies, branches, devices, and users via the admin endpoints.
- Monitor `/monitoring/operational` and `/monitoring/pilot` daily.
- Review audit logs for security and compliance.
- Manage the model registry: register candidates, promote validated models, rollback if performance degrades.

## Best practices

- Capture products in consistent, well-lit conditions.
- Avoid glare, motion blur, and extreme angles.
- For sealed or opaque products, note that the AI only assesses visible external characteristics.
- Sync the device regularly when connectivity is available.
- Keep the app updated to the latest RC build.

## Limitations to communicate

- The camera cannot see inside sealed packaging, cans, or opaque containers.
- The AI is an assistant, not a replacement for human judgement or laboratory testing.
- Expiry date discrepancies are flagged for review, not automatic fraud conclusions.

## Getting help

- Check `docs/business/IMPLEMENTATION_GUIDE.md` for deployment and configuration.
- Check `docs/OPERATIONS_GUIDE.md` for detailed operations procedures.
- Contact the pilot coordinator for account, training, or escalation issues.
