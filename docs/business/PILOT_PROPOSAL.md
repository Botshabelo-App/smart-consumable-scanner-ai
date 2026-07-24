# Pilot Proposal — Smart Consumable Scanner AI

**Status:** Release Candidate 1 (RC1) — Pilot Evaluation and Maintenance Mode.

## Objective

Validate the Smart Consumable Scanner AI in a real operational environment, collect structured feedback and expert-labelled data, and demonstrate measurable improvement in inspection efficiency and accuracy before a production release.

## Why pilot now

The software architecture is stable, the AI pipeline uses real inference, and the mobile and backend systems are feature-complete for inspection workflows. The remaining risk is AI accuracy on real-world, institution-specific products and conditions. A controlled pilot directly addresses that risk.

## Pilot scope

| Activity | Description |
|----------|-------------|
| Camera inspection | Inspectors capture product images and receive AI condition results. |
| Override/accept workflow | Inspectors accept or override AI with reasons. |
| Review queue | Authorised reviewers examine overrides and assign corrected labels. |
| Reporting | Generate PDF/CSV/Excel reports with signatures and QR codes. |
| Monitoring | Track scan volume, accuracy, false positives, false negatives, uptime, and device performance. |

## Proposed pilot sites

- School canteens / school nutrition programmes
- Supermarkets / retail stores
- Warehouses / wholesalers
- Food manufacturers
- Restaurants / hotels
- Municipal health departments / government inspectors

## Duration

4–8 weeks per site, depending on inspection volume and product mix.

## Responsibilities

| Party | Responsibilities |
|-------|------------------|
| Pilot site | Provide inspectors, products to inspect, and ground-truth labels for disagreements. |
| Project team | Deploy backend, mobile app, training, and weekly monitoring. |
| Reviewers | Adjudicate inspector overrides and approve high-quality examples for retraining. |

## Success criteria

See `docs/PILOT_METRICS.md` for quantitative targets. Key metrics include:

- Inspection completion rate ≥ 95%.
- AI agreement with expert inspectors ≥ 80%.
- Report generation success ≥ 99%.
- System uptime ≥ 99%.
- Offline sync success ≥ 95%.

## Deliverables

- Weekly pilot summary reports.
- Monthly aggregated performance report.
- Expanded, expert-labelled dataset.
- Validated model candidate (if data supports improvement).
- Final pilot report with go/no-go recommendation for `v1.0.0`.

## Data and privacy

- Pilot images and metadata are stored in the pilot site's environment or a dedicated project tenant.
- PII is minimised; faces and incidental personal data are blurred or excluded.
- Ground-truth labels are owned by the project and used only for model improvement under the pilot agreement.

## Next step

Contact the project owner to confirm pilot terms, deployment model, data-sharing agreement, and training schedule.
