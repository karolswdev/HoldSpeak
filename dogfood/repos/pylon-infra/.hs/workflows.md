# pylon-infra — change workflow

The path every change follows, from idea to verified-in-prod.

1. **Plan.** Open an issue (PI-xxx) describing the change, blast
   radius, and rollback. Branch from `main`.
2. **PR.** Push the branch, open a PR. CI runs `terraform fmt -check`,
   `terraform validate`, and `terraform plan` and posts the plan.
   A platform owner reviews; the plan must be clean (no surprise drift).
3. **terraform apply via CI.** On merge to `main`, CI applies to
   **dev** automatically, then **staging** (with a 24h soak). **prod**
   waits at a manual approval gate.
4. **Progressive rollout.** For workload changes, the operator drives
   canary → 10% → 100%, pausing at each step for an SLO check. A failed
   check halts and rolls back automatically.
5. **Observe SLO.** After 100%, watch the Grafana dashboard for the
   service: availability, p99 latency, and error-budget burn. The
   change is "done" only once the SLO is steady post-rollout.

Hotfix during an incident: the same path, compressed — but still a PR,
still progressive, never a manual kubectl on prod.
