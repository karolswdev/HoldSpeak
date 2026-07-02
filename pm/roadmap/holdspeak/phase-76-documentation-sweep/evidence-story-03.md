# Evidence — HS-76-03 — ARCHITECTURE catches up

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-76-documentation-sweep`)

## What changed (each fix maps to a ledger row)

- **The component map** gains what shipped in 72–74: the Desk as its own
  output box ("the web front door, React island at /", `web/src/desk/`),
  the runtime bus ("the one /ws per page", `runtime-bus.js`) with its
  live-frame edges into the Desk and the rooms, and the capability-run
  subsystem (`web/routes/primitives.py`) with its LLM and DB edges. The
  old single "Web UI + presence" box is now the rooms
  (`web/src/pages/`) beside the Desk.
- **The dictation diagram's preview fork is honest**: "Preview first?"
  routes both the wake word's default AND the opt-in
  `dictation.preview_before_type`; the card is labeled with the one-shot
  server token; Discard's burn path journals.
- **The artifact diagram gains the run-born lane**: a persona/chain/
  workflow run enters the SAME artifact store with capability lineage.
- The trust-boundary diagram needed no change here (its egress rows
  follow SECURITY, which HS-76-05 completes — the ordering is
  deliberate: SECURITY first, then the mirror check at closeout).

## Verification artifacts

- The Mermaid render guard (`tests/e2e/test_mermaid_renders.py`, real
  mmdc): **2 passed** — all diagrams still render after the edits.
- Doc guards: **85 passed, 2 skipped**.

## Acceptance criteria — re-checked

- [x] The map includes the desk island, the one runtime bus, run-born
      artifacts, and the honest preview gate.
- [x] The render guard green.
- [x] Trust boundary == SECURITY deferred to 05 by design (SECURITY's
      own fix lands there first).
