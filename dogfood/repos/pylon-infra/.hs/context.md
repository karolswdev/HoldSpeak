# pylon-infra — context

pylon-infra is the platform/infrastructure repo for our Kubernetes
estate. It provisions clusters, codifies rollouts, and stores the
runbooks the on-call rotation uses during incidents.

## Estate

Three clusters, each spanning three availability zones:

- **dev** — auto-applies on merge to `main`, low guardrails.
- **staging** — auto-applies, 24h soak before prod promotion.
- **prod** — manual approval gate in CI, progressive rollout only.

## Stack

Terraform (infra), Kubernetes (workloads), a Go operator (custom
resources + reconcile loops), GitHub Actions (CI/CD), and
Prometheus/Grafana (observability).

## Primary entry points

- `terraform/main.tf` — providers, backend, remote state.
- `terraform/cluster.tf` — the cluster + managed node pools.
- `terraform/variables.tf` — per-environment inputs.
- `k8s/base/deployment.yaml` — base workload manifest with the
  progressive-rollout annotations.
- `k8s/base/service.yaml` — the stable service fronting the rollout.
- `operator/main.go` — the `Pylon` custom-resource reconcile loop.
- `.github/workflows/ci.yml` — fmt/validate/plan + apply-on-main.
- `runbooks/` — operational runbooks (cert renewal, eviction storms).
- `STAGES.md` — what has shipped and what is in planning.
- `docs/adr/` — architecture decision records.
- `docs/POSTMORTEM-2026-05-cert-outage.md` — the PI-204 incident.

## Where to look first

- A rollout question → `k8s/base/` + ADR 0001.
- A secrets question → ADR 0002 + the sealed-secrets controller.
- An incident → `runbooks/` + the latest postmortem.
- "What's next" → `STAGES.md` (Stage 5, PI-215).
