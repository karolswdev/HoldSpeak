# HS-146-05 — Docs, walk, and close

- **Project:** holdspeak
- **Phase:** 146
- **Status:** ready
- **Depends on:** HS-146-02, HS-146-03, HS-146-04
- **Unblocks:** —
- **Owner:** unassigned

## Problem

Six surfaces still say "one subscription", and multi-calendar is a
claim until the shots, the cold walk, and a baseline-judged sweep
say otherwise.

## Scope

### In

- The six prose sites (plan §7): `docs/USER_GUIDE.md:486-497`,
  `docs/SECURITY.md:355` (the egress row tells the multi-source
  truth), `holdspeak/mcp/families/settings.py:28`, and the three
  docstrings (`integrations.py`, `calendar_ingest_conductor.py`,
  `db/calendar_events.py`).
- **Shots against the real hub**, both widths, eyeballed by the
  orchestrator first: the list editor (empty / one / two sources,
  egress chips), the rail with two sources (provenance chips, a
  cross-feed duplicate), the single-source rail (no chips).
- **Cold walk**: `scripts/door_walk_hs144.py` 7/7 with the reworked
  leg 5.
- **Close sweep** (readable + dw-capture PAIR), verdict vocabulary
  baseline-exact / zero branch-new; full a/b/c triage of anything
  non-baseline.
- `final-summary.md`; phase/README cadence updates; one counsel
  close pass before the flip.

### Out

- Push/PR/merge — the owner's shot verdicts + merge word gate it.

## Acceptance criteria

1. Zero "one subscription" claims survive on the six sites (grep
   proof in evidence).
2. Shot set delivered; no byte-identical pairs.
3. Walk 7/7; sweep baseline-exact zero branch-new (or triaged).
4. Counsel verdict recorded; final-summary exists; statuses truthful.

## Test plan

The walk + sweep ARE the tests; captured via `dw evidence capture`
with the readable-run pairing noted in the triage note.
