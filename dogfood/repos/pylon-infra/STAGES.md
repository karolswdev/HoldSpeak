# pylon-infra — stages

What has shipped, and what is next. One line per stage.

## Shipped

- **Stage 1 — Base cluster (Terraform).** Three clusters (dev/staging/
  prod), three AZs each, general + spot node pools, remote locked
  state. *Done 2026-01-22.*
- **Stage 2 — CI pipeline.** GitHub Actions: `fmt`/`validate`/`plan` on
  every PR, auto-apply to dev/staging on merge, manual prod gate.
  *Done 2026-02-18.*
- **Stage 3 — Observability.** Prometheus + Grafana, SLO dashboards
  (availability, p99 latency, error-budget burn) wired to alerting.
  *Done 2026-03-25.*
- **Stage 4 — cert-manager + sealed-secrets.** Auto-renewing TLS via
  cert-manager; secrets committed as SealedSecret ciphertext only,
  decrypted in-cluster. *Done 2026-04-30.*

## Planning

- **Stage 5 — Cluster autoscaler migration (PI-215).** Move prod off
  fixed-size node pools onto the Kubernetes cluster autoscaler so
  capacity tracks demand. Touches `terraform/cluster.tf`, the
  operator's capacity assumptions, and requires the PI-220 eviction
  runbook rewrite first (autoscaling makes evictions routine).
  *Status: PLANNING — milestone meeting pending.*
