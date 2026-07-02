# HS-76-01 — The truth audit (the drift ledger)

- **Status:** done
- **Severity:** HIGH
- **Depends on:** —
- **Evidence:** [evidence-story-01.md](./evidence-story-01.md)

## What

(The contract lives in the phase status doc's exit-criteria row for
HS-76-01; this file carries the build notes and the Done record.)

## Test plan

- The doc guards (voice/dash/canon + the mermaid render guard where
  diagrams change) green; screenshots shot from a REAL seeded hub, not
  mocks; every claim in changed prose read against the shipped code.

## Done

Shipped. Three parallel verify-against-code passes over 22 docs produced
the ledger: five HIGH targets (README desk-less; ARCHITECTURE's map
missing the island/bus/run subsystem; the docs index on the retired
Home IA; WEB_DESK inverted; SECURITY's egress table missing three shipped
egress doors), two MED (MEETING_MODE's `/` dashboard; CHANGELOG trailing
three features), a short LOW tail, seven docs verified current, and six
dead root strays surfaced as an owner decision. The audit's own
screenshot pass caught a shipped P75 bug (the visible empty PreviewCard —
fixed in 349646d). See [evidence-story-01.md](./evidence-story-01.md).
