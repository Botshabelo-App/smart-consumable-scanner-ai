# Maintenance Mode Guide

The Smart Consumable Scanner AI project is in **Maintenance Mode** while Release Candidate 1 (RC1) pilots are evaluated. The `main` branch is frozen; see `BRANCHING.md` for the full branch, release, and freeze policy.

## What Maintenance Mode means

- No major new features unless they are required by pilot feedback or critical business/regulatory requirements.
- Focus is on stability, bug fixes, security updates, AI model improvements based on validated data, documentation maintenance, and pilot support.
- Version 1.0.0 will only be tagged after the release checklist is fully signed off.

## Allowed changes

| Type | Allowed | Notes |
|------|---------|-------|
| Bug fixes | Yes | Include regression test and CHANGELOG entry. |
| Security patches | Yes | Update `SECURITY_AUDIT.md` and re-run `pip-audit` / `npm audit`. |
| Dependency updates | Yes | If they fix vulnerabilities or are required for Expo/React Native compatibility. |
| AI model retraining | Yes | Only with a new dataset version, evaluation on a held-out test set, and registry update. |
| Pilot monitoring reports | Yes | Refine `backend/scripts/pilot_summary.py` and related endpoints. |
| Documentation corrections | Yes | Keep `PROJECT_STATUS.md` and cross-references consistent. |
| New sensors/hardware | No | Keep in `docs/LIMITATIONS_AND_ROADMAP.md` and `V1_ROADMAP.md` for post-1.0.0. |
| New UI features | No | Unless directly required by pilot feedback and approved. |
| New product categories | No | Dataset and model must be validated first; add to roadmap. |

## Version control

The following tags are used:

- `RC1-Stable` — current stable RC1 baseline.
- `Pilot-1` — snapshot deployed to the first pilot site.
- `Pilot-2` — snapshot deployed to the second pilot site (when applicable).
- `v1.0.0` — production release, only after all gates in `docs/RELEASE_CHECKLIST.md` are met.

## Weekly maintenance tasks

1. Review `backend/scripts/pilot_summary.py` output.
2. Check `npm audit` and `pip-audit` for new high/critical issues.
3. Review pending review requests (`GET /reviews?status=pending`).
4. Verify database backups and model artifact storage.
5. Monitor `/monitoring/operational` and `/monitoring/pilot` metrics.

## Monthly maintenance tasks

1. Run `backend/scripts/pilot_monthly_report.py`.
2. Re-evaluate active model on latest approved review dataset.
3. Review and update `CHANGELOG.md`, `SECURITY_AUDIT.md`, and `PROJECT_STATUS.md`.
4. Test backup/restore procedures.

## AI model retraining policy

1. New dataset must be collected and quality-checked with `ai-service/datasets/quality.py`.
2. Train with `ai-service/datasets/train.py` and evaluate with `ai-service/scripts/evaluate_models.py`.
3. Register candidate in `/model-registry` with full metrics, dataset version, and checksum.
4. Promote only if the candidate's validation score is >= the active model, or with an explicit `force=true` and documented reason.
5. Keep the previous model available for rollback.

## Communication

- All non-trivial changes require a PR.
- Pilot findings must be recorded in `docs/PILOT_PLAN.md` or `docs/LESSONS_LEARNED.md`.
- Update `CHANGELOG.md` with every merged change.
