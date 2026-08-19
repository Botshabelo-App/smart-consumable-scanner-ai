# Pilot Success Metrics

**Status:** Engineering Complete — Release Candidate 1 (RC1) — Pilot Evaluation and Maintenance Mode.

These metrics determine whether the RC1 pilot is successful and the project can proceed to RC2 and Version 1.0.0.

## 1. Operational metrics

| Metric | Definition | Target (RC1) | Endpoint |
|--------|------------|--------------|----------|
| System uptime | Backend and AI service availability | ≥ 99.5% | Monitoring dashboard |
| Inference success rate | Scans with a valid AI result | ≥ 98% | `GET /monitoring/operational` |
| Average scan time | End-to-end latency (camera → result) | ≤ 2.5 s on Wi-Fi | `GET /monitoring/operational` |
| API latency p95 | 95th percentile backend latency | ≤ 1000 ms | `GET /monitoring/operational` |
| Average confidence | Mean AI confidence across scans | ≥ 0.80 | `GET /monitoring/operational` |
| Offline sync success rate | Queued scans uploaded when online | ≥ 95% | `GET /monitoring/operational` |
| Crash count (24h) | Mobile crashes per day | 0 critical | `GET /monitoring/operational` |
| Device health score | Composite of crashes, latency, battery | ≥ 0.90 | `GET /monitoring/operational` |

## 2. AI accuracy metrics

| Metric | Definition | Target (RC1) | Measurement |
|--------|------------|--------------|-------------|
| AI agreement rate | Inspector accepts / total inspected | ≥ 85% | `GET /monitoring/pilot` |
| False positive rate | AI says expired/suspicious, inspector overrules to fresh | ≤ 10% | `GET /monitoring/pilot` |
| False negative rate | AI says fresh, inspector overrules to expired/suspicious | ≤ 5% | `GET /monitoring/pilot` |
| Produce F1 | Per-class F1 on held-out produce set | ≥ 0.85 | `ai-service/scripts/evaluate_models.py` |
| Packaged/beverage F1 | Per-class F1 on held-out packaged/beverage set | ≥ 0.70 | `ai-service/scripts/evaluate_models.py` |

## 3. Process metrics

| Metric | Definition | Target (RC1) |
|--------|------------|--------------|
| Inspection completion rate | Scans with inspector feedback / total scans | ≥ 90% |
| Average inspection time | Total time per inspection including review | ≤ 60 s |
| Report generation success rate | Reports successfully generated / requested | ≥ 99% |
| Override reason capture | Overrides with a recorded reason | 100% |
| Review turnaround time | Time from override to reviewer decision | ≤ 48 hours |
| Offline sync reliability | Offline scans synced without loss | ≥ 95% |

## 4. User satisfaction

| Metric | Method | Target (RC1) |
|--------|--------|--------------|
| Inspector NPS | Weekly 1-question survey | ≥ 40 |
| Ease of use score | 1–5 Likert scale | ≥ 4.0 |
| Confidence in AI | 1–5 Likert scale | ≥ 3.5 |

## 5. Go / no-go criteria

All of the following must be met before tagging `v1.0.0-rc2`:

- [ ] System uptime ≥ 99.5% over pilot period.
- [ ] Inference success rate ≥ 98%.
- [ ] Average scan time ≤ 2.5 s on Wi-Fi.
- [ ] AI agreement rate ≥ 85% or documented root cause for disagreements.
- [ ] False positive rate ≤ 10% and false negative rate ≤ 5%.
- [ ] Produce F1 ≥ 0.85 on a representative held-out set.
- [ ] Packaged/beverage F1 ≥ 0.70 on a representative held-out set.
- [ ] Inspector NPS ≥ 40.
- [ ] No critical security vulnerabilities unpatched or accepted without sign-off.
- [ ] Disaster recovery and backup procedures tested.

If any criterion is not met, address the gap, re-run the pilot segment, and produce RC2 before final release.

## 6. Reporting cadence

- **Daily:** system uptime, crash count, inference success rate.
- **Weekly:** AI agreement rate, false positive/negative rates, user satisfaction.
- **Monthly:** full per-class F1 re-evaluation, dataset growth, model registry review.
