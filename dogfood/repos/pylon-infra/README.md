# pylon-infra

The platform/infrastructure repo for our Kubernetes estate. It
provisions clusters, drives progressive rollouts, and codifies the
runbooks on-call uses during incidents.

**Stack:** Terraform · Kubernetes · a Go operator · GitHub Actions ·
Prometheus/Grafana.

## Estate

Three clusters (dev, staging, prod), three AZs each. dev and staging
auto-apply on merge; prod waits at a manual gate and rolls out
progressively (canary → 10% → 100%).

## Layout

- `terraform/` — clusters and node pools.
- `k8s/base/` — base workload manifests (progressive-rollout annotated).
- `operator/` — the Pylon reconcile loop driving rollouts.
- `runbooks/` — operational procedures (cert renewal, eviction storms).
- `docs/adr/` — architecture decisions.
- `docs/POSTMORTEM-*.md` — incident postmortems.
- `STAGES.md` — what shipped, what's next.

## Invariants

Every change is a reviewed PR · prod rollouts are progressive · no
manual kubectl in prod · secrets via sealed-secrets (never in git) ·
certs auto-renew via cert-manager. See `.hs/memory.md`.

## Contributing

Open an issue (PI-xxx), branch, PR. CI runs fmt/validate/plan and posts
the plan; an owner reviews. See `.hs/workflows.md` for the full path.
