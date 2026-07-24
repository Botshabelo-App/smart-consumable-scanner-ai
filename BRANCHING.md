# Branching, Release, and Freeze Policy

This repository is in **Maintenance Mode** while the Smart Consumable Scanner AI RC1 pilots run. No feature development should occur without an approved roadmap item or pilot requirement.

## Branch freeze

- `main` is frozen to direct pushes.
- All changes must go through a Pull Request.
- Every PR requires:
  - Code review by at least one reviewer.
  - Passing automated tests (`pytest`, `npx tsc --noEmit`, `npm audit --audit-level=high`, `pip-audit` where applicable).
  - Updated documentation when the change touches user-facing behaviour, API contracts, deployment, security, or AI claims.
  - A `CHANGELOG.md` entry for non-trivial changes.

## Branch strategy

| Branch | Purpose |
|--------|---------|
| `main` | Stable RC branch. Only merged, reviewed, and verified changes. Tagged `RC1-Stable`, `Pilot-*`, and eventually `v1.0.0`. |
| `develop` | Integration branch for future development. Currently on hold during Maintenance Mode unless a roadmap item is approved. |
| `hotfix/*` | Critical security, stability, or data-integrity fixes that cannot wait for a normal release cycle. |
| `pilot/*` | Pilot-specific configuration, feedback-driven fixes, and monitoring improvements. |
| `research/*` | Experimental AI work, new sensor integration prototypes, and dataset experiments. Must not merge directly to `main` without full validation. |

## Versioning policy

We follow [Semantic Versioning](https://semver.org/) with pre-release tags for pilot and release-candidate builds.

- `v1.0.0-rc1` — current RC1 baseline.
- `v1.0.0-rc2` — if pilot feedback requires a new release candidate.
- `v1.0.0` — Production release, only after all gates are met.
- `v1.1.0`, `v1.2.0` — subsequent feature releases after v1.0.0.

Release tags are annotated (`git tag -a`) and include the release date, key changes, and known limitations.

## Release gates for v1.0.0

`v1.0.0` must not be tagged until:

1. Pilot validation is successful.
2. AI models have been validated on representative, expert-labelled datasets.
3. `docs/RELEASE_CHECKLIST.md` is fully signed off.
4. Remaining production environment issues (e.g., Node.js `>=20.19.4`) are resolved.
5. Critical and high-priority defects are closed.
6. Documentation and training materials are complete.

## Allowed changes during Maintenance Mode

See `MAINTENANCE.md` for the detailed Maintenance Mode policy. In summary:

- Bug fixes and stability improvements.
- Security patches and dependency updates.
- Documentation corrections and clarifications.
- AI model improvements backed by validated datasets and evaluation reports.
- Pilot feedback-driven changes.

Prohibited without explicit approval:

- New user-facing features.
- New product categories or AI model expansion.
- New sensor/hardware integrations.
- Major dependency upgrades that change API contracts or require native rebuilds.

## Pilot operations

During an active pilot:

- Do not modify AI models in the pilot environment.
- Collect inspection statistics, user feedback, false positives, false negatives, crash reports, and performance metrics.
- After the pilot, review results, improve datasets, retrain offline, validate, and promote a new model only if it outperforms the previous version.
