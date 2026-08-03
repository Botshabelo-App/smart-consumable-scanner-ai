# Smart Consumable Scanner AI — RC1 Pilot User Guide

## Download and install

1. Open the pilot download page in Chrome on your Android phone.
2. Tap **Download APK** (`SmartConsumableScannerAI-RC1-Pilot-v10d.apk`).
3. Open the downloaded file and tap **Install**.
4. If prompted, allow installation from Chrome / unknown sources.

- Version: `0.1.9-RC1`
- SHA-256: `6a9ff38939823c42f843f2ef7b207ffcaf4a34139a3b5a2af4f0d3dee9b06a89`

## Log in

1. Open **Smart Consumable Scanner AI**.
2. The backend URL is already filled in.
3. Enter the test account:
   - **Email:** `moeketsitsomodan@gmail.com`
   - **Password:** `477SectionA`
   - **Role:** Inspector
4. Tap **LOG IN**.

(If the server URL field is ever empty, enter `https://street-compatibility-known-projection.trycloudflare.com`.)

## Scan a product

1. Allow camera and location permissions when asked.
2. On the **Scan** screen, choose a voice language.
3. Point the camera at the product label and tap **Capture**.
4. Wait a few seconds while the app auto-detects the barcode/OCR and runs AI analysis.
5. Review the result: product name, brand, batch, expiry date, packaging condition, and the spoken/visual inspection result.

## Generate a report

1. Tap **Reports** at the bottom of the screen.
2. Select a scan and tap **SELECT**.
3. Choose **PDF**, add optional notes, then tap **GENERATE REPORT**.
4. The report ID is shown. PDFs are stored on the server and can be downloaded from the report URL.

## Tips

- Scan in good, even lighting.
- Hold the phone 15–25 cm from the label and keep it steady.
- Avoid heavy reflections, curved, or damaged labels when possible.
- Any auto-detected field can be edited before saving if the OCR is wrong.

---

This is the RC1 Private Pilot build. Do not publish to the Google Play Store or share publicly.
