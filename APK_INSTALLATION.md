# Smart Consumable Scanner AI — RC1 Pilot Test Build

## APK Details

- **File:** `SmartConsumableScannerAI-RC1-Pilot-v10f.apk`
- **Version:** `0.1.9-RC1`
- **Package:** `com.smartscanner.ai`
- **Size:** ~110 MB
- **SHA-256:** `85dfd28a0ede48521feabc43bbefb5b58e29c0e1310e548058bc39350bb993da`
- **Signed:** Yes, with a self-signed RC1 pilot keystore (v2 APK signature scheme)
- **Status:** Release Candidate 1 — for private pilot evaluation only. Not for Google Play Store or public distribution.

## What's New in v10

- **Final enterprise branding:** new app icon, splash screen, adaptive icon, and full horizontal logo on the login screen.
- **Modular branding configuration:** all colours, app name/tagline, and default backend URL are centralised in `mobile/src/config/brand.ts` so organisations can rebrand without touching core screens.
- **Multi-language voice guidance:** choose English, isiZulu, isiXhosa, Afrikaans, or Sesotho for spoken inspection results.
- **Per-field confidence badges:** the result card now shows AI confidence, label OCR confidence, and the list of auto-detected fields.
- **Improved offline mode:** scans queued offline are encrypted locally (file path + metadata) and automatically synchronised when the app starts and the network is available.
- **Regulatory-ready PDF reports:** generated PDFs include inspector name, GPS coordinates, timestamps, evidence photo, brand, manufacturing and expiry dates, batch/lot, barcode, packaging condition, AI confidence, and a digital-signature placeholder.
- **Automatic packaging detection:** the camera scan auto-detects barcode/QR codes and uses OCR to extract product name, brand, batch/lot number, manufacturing date, and expiry date whenever they are visible.
- **Packaging defect detection:** the AI flags missing labels, label replacement/expiry-date tampering, barcode/product-name mismatches, and damaged or contaminated packaging.
- **Spoken inspection result:** the AI speaks the exact result message out loud in the selected language.
- **Visual inspection messages:** the result card shows the wording you requested:
  - Fresh – Safe to consume
  - Near expiry – Inspect carefully
  - Expired – Do not consume
  - Possible label or expiry-date tampering detected
  - Packaging damage or contamination detected
- **Manual fallback:** all fields remain editable if the automatic detection is incomplete or wrong.

## Installation Steps

1. **Enable installation from unknown sources**
   - On your Android phone: **Settings → Apps → Chrome / Files → Install unknown apps → Allow**.
2. **Download the APK** from the link provided in this message.
3. Open the downloaded file and tap **Install**.
4. If Android warns about an unknown publisher, tap **Install anyway**.

## First Launch

1. Open the **Smart Consumable Scanner AI** app.
2. The login screen is pre-filled with the current public pilot backend URL. If it differs, enter the URL in the **Pilot server URL** field:
   - **Current public pilot backend:** `https://controversial-made-grant-altered.trycloudflare.com`
   - If running the backend on the same Wi-Fi network: `http://192.168.x.x:8000`
   - If testing with `adb reverse`: `http://localhost:8000`
   - A self-hosted backend: `https://api.yourdomain.com`
3. Enter your email and password, then tap **Log in**.
   - If you do not have an account, tap **Register**, fill in all fields, and then log in.

> **Note:** The public URL above is a temporary tunnel for this pilot test session. It is not a permanent production deployment. For a long-lived backend you will need to host the Docker Compose stack on your own cloud server.

## Test Account (already created on the live pilot backend)

- **Email:** `moeketsitsomodan@gmail.com`
- **Password:** `477SectionA`
- **Role:** Inspector

## Backend Setup

The APK connects to the FastAPI backend. To run the backend locally:

```bash
cd /path/to/smart-consumable-scanner-ai
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
pip install -r ai-service/requirements.txt

# Terminal 1: AI inference service
python -m uvicorn ai_service.main:app --app-dir ai-service --host 0.0.0.0 --port 8001

# Terminal 2: Backend API
python -m uvicorn ai_scanner.main:app --app-dir backend --host 0.0.0.0 --port 8000
```

For a Docker deployment, see `docker-compose.yml` in the repository.

## Real-Device Pilot Testing

For step-by-step test procedures, product categories, success criteria, and data to collect, see `PILOT_TEST_PROTOCOL.md` in the repository.

## Branding

Final branding is included in the app:

- App icon (`mobile/assets/icon.png`)
- Android adaptive icon (`mobile/assets/adaptive-icon.png`)
- Splash screen (`mobile/assets/splash.png`)
- Full horizontal logo (`mobile/assets/logo.png`)
- Modular brand configuration (`mobile/src/config/brand.ts`)

## What to Test

- Login / registration
- Dashboard (inspection statistics)
- History (previous scans)
- Reports (PDF / CSV / Excel generation)
- Review workflow
- Camera scanning, OCR, automatic field population, AI analysis, spoken results, and Accept/Override on real products
- Voice language selector
- Offline scan queue and background sync

## Important Notes

- This build is **RC1 Pilot Test** only. Do not publish it or share it outside your pilot organisations.
- The AI evaluates observable external characteristics from a smartphone camera. It cannot determine the internal condition of sealed or opaque products.
- For best results, scan in good lighting, hold the phone steady, and keep the label 15–25 cm from the camera.
- The default pilot server URL is the current public tunnel. If it expires, enter the new working backend URL before logging in.

## Support

If you encounter issues, capture a screenshot and the app version, and report it as a GitHub issue or in your pilot feedback channel.
