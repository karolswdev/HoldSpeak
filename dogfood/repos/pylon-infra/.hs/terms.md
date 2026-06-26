# pylon-infra — glossary

**Canary** — the first, smallest rollout step. A single replica (or a
tiny traffic slice) takes the new version while the rest stay on the
old one, so a bad release is caught before it reaches everyone.

**Blast radius** — how much breaks if a change goes wrong. We bound it
deliberately: one cluster's prod node pool per change, never several.

**SLO / error budget** — the Service Level Objective (e.g. 99.9%
monthly availability) and the budget of allowed failure it implies
(~43 minutes/month at 99.9%). Burn the budget too fast and rollouts
freeze until it recovers.

**Runbook** — a step-by-step operational procedure for a known
situation (cert renewal, eviction storm). On-call follows it during an
incident; a stale runbook is a liability.

**Sealed secret** — an encrypted secret committed safely to git. The
sealed-secrets controller holds the private key and decrypts it into a
real Kubernetes Secret in-cluster. The plaintext never touches the repo.

**Drift** — when live infrastructure diverges from what Terraform
declares (someone changed it by hand, or a provider mutated it). CI
surfaces drift in `terraform plan`; unreviewed drift blocks a merge.

**Cordon / drain** — `cordon` marks a node unschedulable; `drain`
evicts its pods so they reschedule elsewhere. Used for node
maintenance — and the source of the PI-220 eviction-storm risk if done
too aggressively.
