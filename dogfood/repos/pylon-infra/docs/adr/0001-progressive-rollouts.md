# ADR 0001 — Progressive rollouts for prod

**Status:** Accepted (2026-02-10)

## Context

Early on we shipped to prod with a plain RollingUpdate. A bad image
reached every replica before metrics caught it, and we burned most of a
month's error budget in one release. We needed releases that fail small.

## Decision

All prod workload changes roll out **progressively**: canary (one
replica), then 10%, then 100%. Each step is gated on the workload's SLO
(availability + p99 latency). A breach halts the rollout and rolls back
automatically. The progression is driven by the Pylon operator
(`operator/main.go`), not by hand-editing manifests, encoded in the
deployment annotations (`k8s/base/deployment.yaml`).

## Consequences

- A bad release is contained to the canary, not the fleet.
- Rollouts are slower (soak between steps) — acceptable for prod.
- The operator becomes a hard dependency for prod deploys; it must be
  highly available.
- "No manual kubectl on prod" follows directly: hand edits bypass the
  gate. This is now a standing invariant (`.hs/memory.md`).
