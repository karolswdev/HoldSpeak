# ADR 0002 — Secrets via sealed-secrets

**Status:** Accepted (2026-04-12)

## Context

Secrets were managed out of band (a shared vault export, occasional
plaintext in a private branch). This was hard to audit and one leak
away from a breach. We wanted secrets in git — auditable, reviewed,
diffable — without ever committing plaintext.

## Decision

Adopt the **sealed-secrets** controller. Engineers encrypt a secret to
a `SealedSecret` (ciphertext) with the controller's public key and
commit that. The controller, holding the private key, decrypts it into
a real Kubernetes `Secret` in-cluster at apply time. Only ciphertext
ever lands in the repo; deployments consume the decrypted Secret via
`envFrom` (see `k8s/base/deployment.yaml`).

## Consequences

- Secrets are reviewed and audited like any other change.
- The controller's private key is now the crown jewel; back it up and
  rotate deliberately. Losing it means re-sealing every secret.
- A plaintext secret in a diff is a hard PR blocker (CI scan + review).
- Becomes a standing invariant: secrets via sealed-secrets, never in
  git (`.hs/memory.md`).
