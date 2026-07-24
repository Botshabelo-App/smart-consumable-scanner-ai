# Security Audit Report

**Scope:** Smart Consumable Scanner AI — backend, mobile app, infrastructure, and dependency surface.  
**Date:** 2026-07-24  
**Status:** Release Candidate 1 (RC1) — Pilot Evaluation and Maintenance Mode. Remediations completed or documented as accepted risk for pilot.

## 1. Executive Summary

The RC1 security posture is appropriate for controlled pilot deployments when the remediations below are applied. The most critical production risks are default secrets, broad CORS, and transitive vulnerabilities in mobile dependencies. No evidence of simulated AI or fabricated results was found.

## 2. Methodology

- Static code review of backend routers, models, dependencies, and configuration.
- Dependency scan with `pip-audit` and `npm audit`.
- Review of authentication, authorization, audit logging, and data handling.
- Configuration review of CORS, secret management, and container/deployment manifests.

## 3. Findings and Remediations

| ID | Finding | Severity | Status | Remediation |
|----|---------|----------|--------|-------------|
| SEC-1 | Default `SECRET_KEY` in `backend/.env` | Critical | Remediated partially | Added startup warning; enforce `SECRET_KEY` rotation in production. |
| SEC-2 | CORS `allow_origins=["*"]` by default | High | Remediated partially | Origins are configurable via `CORS_ORIGINS`; restrict to exact dashboard/mobile domains in prod. |
| SEC-3 | No rate limiting on auth/scans | Medium | Fixed | Added `slowapi` with 10/min login, 5/min register, 30/min analyze. |
| SEC-4 | Weak password policy | Medium | Fixed | Enforce min 8 chars with at least one letter and one digit. |
| SEC-5 | `python-jose` pulls vulnerable `ecdsa` (Minerva timing) | Medium | Fixed | Replaced `python-jose` with `PyJWT`. |
| SEC-6 | Starlette < 1.1.0 URL reconstruction vulnerabilities | Medium | Fixed | Upgraded `fastapi`/`starlette` and `pillow` to patched versions. |
| SEC-7 | Pillow integer overflow / decompression bomb | Medium | Fixed | Upgraded `pillow` to 12.2.0. |
| SEC-8 | Expo SDK 51 transitive high/critical vulnerabilities | High | Fixed | Upgraded to Expo SDK 57.0.8; `npm audit` now reports only moderate-severity transitive issues. |
| SEC-9 | Mobile local token storage uses `expo-secure-store`; no biometrics | Medium | Accepted for RC1 | Add optional biometric/PIN unlock and keychain-backed storage. |
| SEC-10 | No Content Security Policy headers on API | Low | Accepted for RC1 | Add `TrustedHostMiddleware` and CSP headers in Nginx. |
| SEC-11 | SQLite used in dev; PostgreSQL required for prod | Medium | Documented | Use managed PostgreSQL with TLS and backup in production. |
| SEC-12 | Audit logs do not hash user IP | Low | Accepted for RC1 | Anonymize IP in privacy-sensitive jurisdictions. |

## 4. Dependency Scan Details

### Python (`pip-audit`)

The current `pip-audit` scan (after dependency upgrades) reports no vulnerabilities in installed production packages.

Resolved by:

- Removing `python-jose` (and its transitive `ecdsa` dependency) and switching to `PyJWT==2.13.0`.
- Upgrading `fastapi` to `0.139.2`, `starlette` to `1.3.1`, and `python-multipart` to `0.0.32`.
- Upgrading `pillow` to `12.3.0`.
- Upgrading `pytest` and `setuptools` to non-vulnerable versions.

Re-run `pip-audit` after the next dependency update to verify.

### Mobile (`npm audit`)

Expo SDK 51 and its transitive packages reported high/critical advisories. The mobile app has been upgraded to Expo SDK 57.0.8. `npm audit` now reports only moderate-severity transitive issues.

> Note: Expo SDK 57 and React Native 0.86 prefer Node.js `>=20.19.4`. The current CI/dev environment uses Node 20.18.1, which produces `EBADENGINE` warnings but still installs and type-checks. Update the build environment to a supported Node LTS before production builds.

## 5. Configuration Hardening Checklist

Before production:

- [ ] Generate a 256-bit+ `SECRET_KEY` and store it in a secret manager.
- [ ] Set `CORS_ORIGINS` to the exact production origins.
- [ ] Disable backend debug mode.
- [ ] Use PostgreSQL with TLS and rotate credentials.
- [ ] Enable Nginx HTTPS termination and HSTS.
- [ ] Restrict SSH and database firewall rules.
- [ ] Enable S3/object-storage encryption at rest and in transit.
- [ ] Enable log aggregation and tamper-evident audit storage.
- [ ] Review and enforce RBAC role assignments.

## 6. Mobile Security Notes

- JWT tokens are stored in `expo-secure-store` (encrypted iOS keychain / Android Keystore).
- All API calls use the bearer token over HTTPS.
- Offline scans are queued locally and uploaded when online.
- For RC2: add optional biometric unlock and certificate pinning.

## 7. Sign-off

This audit is a point-in-time assessment. A full penetration test and third-party code review are recommended before the final `v1.0.0` production release.
