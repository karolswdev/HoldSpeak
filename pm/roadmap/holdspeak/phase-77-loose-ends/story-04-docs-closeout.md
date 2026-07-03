# HS-77-04 — Docs + closeout

- **Status:** done
- **Severity:** MED
- **Depends on:** 01–03
- **Evidence:** [evidence-story-04.md](./evidence-story-04.md)

## What

(The contract lives in the phase status doc's exit-criteria row; this
file carries the build notes and the Done record.)

## Test plan

- Story tests per the criteria row; the schema-sensitive guards
  (snapshot/matrix/serialization) updated per the documented recipes when
  they fire; full suite green at ship.

## Done

Shipped as the closeout: the entry points verified silent on every
changed surface (AGENT_HOOK_INSTALL's expected coders-status shape never
included the removed block), the manifest current, final-summary.md
carrying the ledger and the two durable contracts (schema v7 with both
facsimile upgrade paths locked; the HUD's linger grammar). The phase
closes 4/4; the PR merges on a conclusion-checked green.
