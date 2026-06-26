# pylon-infra — durable invariants

These hold across every change. If a dictated task conflicts with one
of these, the invariant wins and the task must call out the conflict.

**Every change is a reviewed PR.** No commits straight to `main`, no
out-of-band changes. The PR is the unit of audit.

**Prod rollouts are progressive.** Canary first, then 10%, then 100%,
with an SLO check at each step. Never flip prod traffic in one move.

**No manual kubectl in prod.** All prod state flows through CI applies
and the operator. `kubectl edit`/`kubectl apply` against prod is an
incident in itself, not a fix.

**Secrets live in the sealed-secrets controller, never in git.** Commit
the SealedSecret ciphertext only; the controller decrypts in-cluster.
A plaintext secret in a diff blocks the PR.

**Certificates auto-renew via cert-manager.** No human renews certs.
If a cert is within 14 days of expiry, that is a cert-manager failure
to investigate (see PI-204), not a thing to hand-renew.

**Blast radius is bounded.** One change touches at most one cluster's
prod node pool. Destructive terraform on prod needs a second owner and
a maintenance window.
