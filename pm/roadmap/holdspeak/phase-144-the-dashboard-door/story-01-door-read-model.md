# HS-144-01 — The Door read model

- **Project:** holdspeak
- **Phase:** 144
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-144-03, HS-144-04
- **Owner:** unassigned

## Problem

The Door needs ONE server-owned aggregate to render from. Today the
Chair's lanes each read their own route (`ChairHome.tsx` per audit A
§3.1) and the closest kanban read model —
`GET /api/follow-through/board`
(`holdspeak/services/follow_through_service.py:122`, four lanes over
action_items + cadence_loops + people projections) — excludes
unfinished thoughts and carries no headline counts. There is no
unified "3 overdue, 2 waiting" truth anywhere (audit A, Pillar 3 gaps).

## Scope

### In

- **`GET /api/door`** — one server-owned aggregate with three parts:
  - **board**: the follow-through four lanes (now / waiting /
    unassigned / overdue) EXTENDED with an `active` column of
    unfinished thoughts projected from their existing
    state/continuity fields (`refinement_thoughts`,
    `schema.py:859-883`; the same truth `FinishThoughtsLane.tsx:45-60`
    reads). No schema extension — settled design §3. Every card
    carries source, target ref, and the verb(s) lawful on it, so the
    glass never invents a transition.
  - **upcoming**: one merged timeline — enabled
    `scheduled_recordings` by `next_fire_at` (`schema.py:3354-3375`)
    now; calendar events join in HS-144-02 behind the same shape, so
    the glass never re-merges.
  - **counts**: honest headline counts (overdue / now / waiting /
    active / upcoming-today) computed server-side.
- **Composition, not duplication.** The door service composes
  `FollowThroughService` and the scheduled-recordings store; it does
  not re-query their tables with its own logic. Where lane math
  lives in `follow_through_service.py:104-231`, the Door calls it.
- **MCP twin** `door.get` calling the exact application service the
  HTTP route calls (the Phase 143 parity pattern).
- Focused tests: aggregate shape, thoughts projected with continuity
  states, counts against a constructed fixture set, parity
  HTTP-vs-MCP on production compositions (decorated fakes are a named
  sin; only external wire boundaries may be faked).

### Out

- Any glass (HS-144-03/04).
- Calendar sources (HS-144-02 extends `upcoming` behind the same
  shape).
- New write verbs — the board's cards name EXISTING verbs only.
- Workbench items (settled design §3).

## Acceptance criteria

- [ ] `GET /api/door` returns board + upcoming + counts in one
  response; every board card names its source and lawful verbs
  (tests).
- [ ] Unfinished thoughts appear in the `active` column with their
  continuity labels, from existing fields only — a grep proves no
  `refinement_thoughts` schema change (test + grep in evidence).
- [ ] Counts are server-computed and match the lanes they summarize
  (property-style test over a generated fixture set).
- [ ] `door.get` MCP twin proves parity against the HTTP route on
  production compositions (test).
- [ ] Zero changes under `web/src`.

## Test plan

- `HOME="$(mktemp -d)" uv run --python 3.13.11 pytest -q
  tests/ -k door` (plus the follow-through and scheduled-recording
  suites the composition touches).
- MCP parity vectors in the same run.
