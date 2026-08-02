# Smart Consumable Scanner AI — RC1 Pilot Test Build

## APK Details

- **File:** `SmartConsumableScannerAI-RC1-Pilot-v8.apk`
- **Version:** `0.1.7-RC1`
- **Package:** `com.smartscanner.ai`
- **Size:** ~109 MB
- **SHA-256:** `cf10dd0e162923d3e58ce381a43bad6e5b58e1ceb3bb6c60f1a40837ec009436`
- **Signed:** Yes, with a self-signed RC1 pilot keystore (v2 APK signature scheme)
- **Status:** Release Candidate 1 — for private pilot evaluation only. Not for Google Play Store or public distribution.

## What's New in v8

- **Automatic packaging detection:** the camera scan now auto-detects barcode/QR codes and uses OCR to extract product name, batch number, printed expiry date, and production date whenever they are visible on the packaging.
- **Auto-analyze:** after capture, the app automatically sends the image to the AI backend and populates the fields.
- **Spoken inspection result:** the AI speaks the result out loud (e.g., "Expired – Do not consume").
- **Visual inspection messages:** the result card shows the exact wording requested:
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
2. On the login screen, enter the current public pilot backend URL in the **Pilot server URL** field:
   - **Current public pilot backend:** `https://social-dogs-create.loca.lt`
   - If running the backend on the same Wi-Fi network: `http://192.168.x.x:8000`
   - If testing with `adb reverse`: `http://localhost:8000`
   - A self-hosted backend: `https://api.yourdomain.com`
3. Enter your email and password, then tap **Log in**.
   - If you do not have an account, tap **Register**, fill in all fields, and then log in.

> **Note:** The public URL above is a temporary tunnel for this pilot test session. It is not a permanent production deployment. For a long-lived backend you will need to host the Docker Compose stack on your own cloud server.

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

## Branding

Final branding is included in the app:

- App icon
- Android adaptive icon
- Splash screen
- Full horizontal logo (`mobile/assets/logo.png`)

## What to Test

- Login / registration
- Dashboard (inspection statistics)
- History (previous scans)
- Reports (PDF / CSV / Excel generation)
- Review workflow
- Camera scanning, OCR, automatic field population, AI analysis, and spoken results on real products

## Important Notes

- This build is **RC1 Pilot Test** only. Do not publish it or share it outside your pilot organisations.
- The AI evaluates observable external characteristics from a smartphone camera. It cannot determine the internal condition of sealed or opaque products.
- For best results, scan in good lighting and hold the phone steady so the barcode and printed text are clearly visible.
- The default pilot server URL is a placeholder. You must set a real backend URL before logging in.

## Support

If you encounter issues, capture a screenshot and the app version, and report it as a GitHub issue or in your pilot feedback channel.
