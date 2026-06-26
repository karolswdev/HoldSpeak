# pylon-infra — tracked work

## PI-204 — cert-manager renewal failed → TLS outage (incident, CLOSED)
The ACME HTTP-01 solver could not reach the API on renewal; the
`api.prod` certificate expired and ingress served an expired cert for
~38 minutes. Root cause and action items in
`docs/POSTMORTEM-2026-05-cert-outage.md`. Action items partly open
(alerting on expiry headroom, solver path test).

## PI-209 — alert fatigue from noisy CPU alerts (incident hygiene, OPEN)
The `HighNodeCPU` rule fires on every batch job and pages on-call at
night. Signal-to-noise is poor; people are starting to ignore the
channel. Need to re-tune thresholds / route to a non-paging tier.

## PI-215 — migrate to the cluster autoscaler (delivery milestone, PLANNING)
Today node pools are fixed-size; we over-provision to absorb spikes.
Stage 5 migrates prod to the Kubernetes cluster autoscaler so pools
scale with demand. Cross-cutting: `terraform/cluster.tf`, the operator's
capacity assumptions, and the rollout/soak plan. Tracked in `STAGES.md`.

## PI-220 — pod-eviction-storm runbook is stale (incident readiness, OPEN)
`runbooks/pod-eviction-storm.md` predates the operator and still tells
on-call to `kubectl drain` aggressively, which can cascade evictions
under PodDisruptionBudgets. Must be rewritten for the operator-driven
world before the autoscaler (PI-215) ships, since autoscaling will make
evictions routine.

## PI-231 — Grafana dashboard JSON drifts from code (delivery, OPEN)
Dashboards are edited in the UI and exported by hand, so the committed
JSON lags reality. Want them provisioned from `terraform/` so they
match the SLOs declared in `.holdspeak/project.yaml`.
