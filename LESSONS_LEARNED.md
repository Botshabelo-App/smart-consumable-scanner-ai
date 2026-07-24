# Lessons Learned

This document captures technical, product, and process lessons learned during the development of the Smart Consumable Scanner AI. It is intended to help future contributors and pilot teams avoid repeating mistakes and to preserve institutional knowledge.

## 1. AI and validation

### Lesson: small labelled datasets produce misleading accuracy
Early model evaluation was based on only two labelled images (`/tmp/apple.png` and `/tmp/rotten_apple.png`). The accuracy was 100% on that pair, but that figure is not representative of real-world performance.

**Action:** `docs/VALIDATION_AND_REGULATORY.md` and `docs/PILOT_METRICS.md` now require a large, representative, expert-labelled dataset before any accuracy claims are made or a model is promoted to active.

### Lesson: explainability is essential for inspector trust
Inspectors and regulators will not trust a black-box AI. Grad-CAM, saliency maps, and top-k finding explanations are required for human review.

**Action:** `ai-service/scripts/explain.py` produces Grad-CAM overlays and calibration diagrams for every trained model.

### Lesson: model promotion must be gated by validated metrics
It is risky to automatically deploy the latest checkpoint. A model can overfit the training data or fail on real-world conditions.

**Action:** The model registry (`/model-registry/{model_id}/promote`) now compares the candidate's F1/accuracy against the active model and blocks downgrade unless an administrator explicitly forces it.

## 2. Software engineering

### Lesson: keep inference service failures transparent
If the AI service is down, the backend must not fabricate a result. Returning an explicit error is safer than silently falling back to a placeholder.

**Action:** `ai_client.py` raises `AIAnalysisError` and the backend returns HTTP 503 when inference fails.

### Lesson: consolidate duplicate auth/admin code
User creation appeared in both `auth.py` and `admin.py`, increasing the chance of inconsistent validation or hashing.

**Action:** `backend/ai_scanner/app/services/user_service.py` provides a single `create_user` helper used by both routers.

### Lesson: rate limit authentication and expensive endpoints
Without rate limiting, login and scan analysis endpoints are easy targets for abuse or accidental overload.

**Action:** `slowapi` rate limiting is applied to login, register, analyze, and health endpoints.

## 3. Mobile and deployment

### Lesson: Expo SDK upgrades must be planned carefully
The initial Expo SDK 51 dependency tree contained high/critical advisories. A major upgrade is not a one-line change; it requires updating React, React Native, TypeScript, and native module versions together.

**Action:** Mobile dependencies were upgraded to Expo SDK 57.0.8. Build environments should use Node.js `>=20.19.4` to match the new React Native requirements.

### Lesson: TypeScript major versions can deprecate old compiler options
Upgrading TypeScript to 6.x caused `baseUrl` deprecation warnings that broke `tsc --noEmit`.

**Action:** `mobile/tsconfig.json` now sets `ignoreDeprecations: "6.0"` while keeping `baseUrl` for path aliasing.

## 4. Security

### Lesson: JWT libraries have transitive vulnerabilities
`python-jose` depended on `ecdsa`, which has a known Minerva timing-side-channel advisory.

**Action:** Switched to `PyJWT` and removed `python-jose` from backend dependencies.

### Lesson: default CORS and secrets are not safe for production
A development configuration with `allow_origins=["*"]` and a default `SECRET_KEY` must be replaced before any real deployment.

**Action:** `docs/SECURITY_AUDIT.md` and `docs/RELEASE_CHECKLIST.md` list explicit hardening steps for production secrets and CORS.

## 5. Product and regulatory

### Lesson: do not overstate AI capabilities
A smartphone camera cannot see inside sealed or opaque packaging. Claims must be limited to observable external characteristics.

**Action:** Every release-facing document includes the limitation statement, and the architecture is designed to support future NIR/hyperspectral/thermal sensors without claiming current capability.

### Lesson: pilot success must be measured, not assumed
Good software is not enough; the AI must actually help inspectors in real environments.

**Action:** `docs/PILOT_METRICS.md` defines quantitative go/no-go criteria, and `backend/scripts/pilot_summary.py` generates weekly reports.

## 6. Process

### Lesson: documentation must be updated with every phase
It is easy for README, release checklists, and roadmaps to contradict each other as the project evolves.

**Action:** This Maintenance Mode phase includes a full cross-document consistency review and a central `PROJECT_STATUS.md` source of truth.
