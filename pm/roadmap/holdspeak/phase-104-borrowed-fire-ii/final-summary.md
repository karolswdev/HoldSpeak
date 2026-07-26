# Phase 104 — Borrowed Fire II: The Watched Hand — final summary

**Machine scope complete 2026-07-26 (7 stories built and walked in
one day); the phase flips CLOSED when the owner's sitting verdict
lands (Article IX.4).** Chartered from the AgentGlass study + the
adversarial council review; the council's cuts held all phase (no
census-as-objects, no context physics, no cockpit sprawl), and the
three kept ideas shipped at their redesigned scope:

- **HS-104-01** — the capability ledger: 4 adapters × 5 capabilities,
  hand-declared standings, `GET /api/agents/capabilities` + contract
  schema, the doctor census over registered consumers, and
  `require_capability` as the enforcement hook everything downstream
  rides.
- **HS-104-02** — the tool-call gate, failure posture inverted from
  AgentGlass: fail-closed when armed, no timeout-auto-allow, the
  proposal a record never authority, one census-pinned transition
  chokepoint, redaction at the agent edge, decision cards on the
  shade with the deny reason riding back verbatim (a real denied
  agent visibly course-corrected), restart invalidation, doubly
  opted in and inert by default. Proven against two real `claude -p`
  sessions on real metal.
- **HS-104-03** — the gate under attack: the eight-item hostile
  checklist pinned as tests (restart/replay/TOCTOU over a REAL
  SIGKILLed-and-restarted hub process), the load-bearing three
  proven by mutation (guard out → named failure → guard restored).
- **HS-104-04** — PR receipts, the candidate-Y deferral paid: one
  batched `gh` per registered source, attribution wearing its
  epistemics (exact / name-match-only / unattributed), observed-at
  always printed, stale-with-retained-rows on a real network yank,
  local-only see-diff with the explicit-fetch offer.
- **HS-104-05** — session receipts: one line, three tiers
  (always-true hub records; reported tokens only where the ledger
  vouches, via the gate hook's Stop leg reading the agent's own
  transcript, cache figures never summed; estimated cost only with
  a price row — absent, never $0.00), per-tool hold latency
  sample-floored at 20.
- **HS-104-06** — docs at the entry points: USER_GUIDE (the
  fail-closed trade written first), SECURITY boundary + egress row,
  ARCHITECTURE paragraph + rendered mermaid, one README paragraph
  leading with off-by-default; truth-audited.
- **HS-104-07** — the walk: all seven beats live in one staged
  session (`seeded-desk-watched-hand`, the HS-103-05 recipe family
  extended, not forked), sweeps green, candidates parked, this
  ledger written. The sitting is the owner's.

## The spec ledger (per the standing web-is-the-spec direction)

Spec-complete contracts a Swift recreation can build from:

- `agent-capabilities.schema.json` — the ledger wire shape, validated
  against the live payload in-test.
- `gate-proposal.schema.json` — the proposal record and its state
  vocabulary (held | approved | denied | expired | invalidated),
  redaction fields, decide/poll routes' payload.
- The route surface in `docs/API_SURFACE.md` (344 routes): the gate
  family (`/api/gate/*`), `/api/sessions/{key}/receipt`,
  `/api/delivery/prs*`, `/api/agents/capabilities`.

Spec debt — behaviors living only in TypeScript today, named:

- The shade gate card's composition (redacted preview, age line, the
  in-place deny-reason editor) — `SystemShade.tsx` + `gate.ts`.
- The receipt line's segment grammar (`receipts.ts:receiptSegments`)
  — which tiers render, in what order, with what labels.
- PR receipt row ordering + labels (`prReceipts.ts`: needs-you
  bands, `attributionLabel`, `prStateLabel`) and the inline diff /
  fetch-offer flow (`PrReceiptsSection.tsx`).
- The gate hook's poll cadence and idempotency-key minting
  (`coder_gate.py` is Python, portable, but the hook contract with
  Claude Code — PreToolUse deny JSON, Stop usage report — is
  documented only in code and SECURITY.md prose).

## Handoff

- The parked candidates live in BACKLOG.md §AB (observed-archives
  adapter, context gauge, the merge actuator).
- BACKLOG.md §AC records the sync-clock drift defect diagnosed while
  it flaked CI during this phase's merges (root cause + fix shape).
- The kernel program (PLAN_KERNEL_OPERATION_BROKER.md) follows per
  the owner's Phase-105 rider; the gate's propose/decide spine and
  the capability ledger are the vertebrae it inherits.
