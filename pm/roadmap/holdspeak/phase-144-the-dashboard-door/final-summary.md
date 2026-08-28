# Phase 144 — The Dashboard Door — Final Summary

**Closed:** 2026-08-28 (6/6). One session, charter to close. Every
story shipped through the gate with a dw-stamped capture, an
orchestrator triage note, and a verdict of baseline-exact / zero
branch-new against the Phase 143 inherited-failure baseline.

## What the owner got

The front door the owner asked for twice — proposed at the Phase 139
close, cancelled in the complexity cut, revived by explicit ruling
with the history on the table:

- **The Door board.** The Chair's lane half reforged
  (replace-never-sit-beside): five columns — overdue / now / waiting /
  unassigned / active — from ONE server aggregate (`GET /api/door` +
  the `door.get` MCP twin, reciprocal-parity-proven). Every card
  affordance is drawn from server-named `lawful_verbs` and calls a
  real route; success is the board changing, failure is a named
  in-flow refusal (the stale-thought 409 is proven on glass). Counts
  are server truth; the glass does no arithmetic.
- **A calendar, for the first time.** The hub's first
  calendar-protocol code: one ICS subscription (file or HTTPS), a
  bounded hostile-proof parser (5 MiB / 2000 events / 4000 projected /
  14-day horizon / 128 occurrences; SECONDLY and MINUTELY refused by
  name), a conductor with the ruled wire posture proven against a
  live local server — HTTPS-only, NO redirects (refusals name the
  target), 10s timeout, zero credential headers — the
  last-good-projection law, and named skip receipts for every
  malformed event.
- **The upcoming rail.** One merged timeline (EVENT vs SCHEDULED
  RECORDING, labeled honestly) off the same one fetch; scheduled rows
  live exactly once (MeetingsLane keeps live/recent meetings); one
  `Schedule recording` action reusing the Phase 136 control.
- **The doorframe repaired.** Go exists at 393 as a designed
  navigator; `/meetings` opens deterministically on a server registry
  fact (15/15 serial, no sleeps). The calendar setting lives in the
  Meetings Settings tile with its mic and ONE egress chip derived
  from the server fact.
- **Docs that tell the truth.** Nine entry-point surfaces corrected;
  the doc-drift guard fences the retired Chair vocabulary; SECURITY
  carries the one truthful ICS egress row.

## The cold walk (the exit proof)

`scripts/door_walk_hs144.py` — reusable, failable, fresh HOME, real
hub, no lore, seeded only through production HTTP. All seven legs
PASS on the worker's run AND the orchestrator's own rerun:

| Leg | Result |
|---|---|
| Cold open: First Sentence untouched; typed first-value ≤3 min | PASS (~1.3–1.9 s; speech honestly refused `transcription_unavailable`, never faked) |
| Reveal lands on the populated Door | PASS |
| Card completion → visual truth ≤500 ms + stale-409 receipt | PASS (~39–42 ms) |
| In-world schedule create, visible on the rail | PASS |
| ICS fixture → Settings → real conductor → rail + egress chip | PASS |
| Click-depth vs the audit before-pictures | tasks 1→0 · upcoming 1+→0 · schedule create 2→1 |
| Doorframe repairs hold (393 Go; deep-link 15+1) | PASS |

Before/after pairs against the audit shots carry a SHA-256
byte-identical guard; First Sentence pairs are marked parity, not
improvement. The walk touches no real machine state and prints its
cleanup.

## Verification posture

CI is dead by owner order; all verification local. Six close sweeps
(one per story), each triaged name-by-name against
`../phase-143-intelligence-router/assets/
story-08-inherited-failure-baseline.txt`; every close verdict
baseline-exact, zero branch-new. **Ten opus gate audits, zero product
bugs across all ten.** The sweeps and guards earned their keep: five
real regressions were caught in-flight and fixed with their laws
untouched (the bare Door error state; the 960px-era 1440 clip; the
floating empty Agents; the 393×667 working-band overflow — fixed by
the height-cap grammar; the undeclared People route — caught by the
API-manifest guard) plus one real determinism bug in projection
replacement caught by a worker's own test.

## Judgment calls made alone (the owner may overrule any)

1. The Chair reforged rather than a second surface (the
   replace-never-sit-beside law).
2. Kanban lanes are server projections; card moves are real verbs; no
   board-position store — a drag with no lawful verb does not exist.
3. Thoughts join the board on existing fields; no schema extension;
   workbench items stay out.
4. ICS-in (executing the Phase 135 ruling), cut as a clean amputation
   point the owner declined to use.
5. The docs round ran without a separate opus audit (tie-break
   recorded in evidence-story-05 with the guard evidence).
6. Story 03's visible scope amendment: `people.commitment.transition`
   was MCP-only — one thin HTTP route added, parity-proven.
7. The walk's leg-1 scope: a model-less fresh HOME proves the TYPED
   first-value path and the NAMED speech refusal; a spoken-transcript
   leg is an attended addendum on the owner's word.

## The ledger (carried, named, owner-visible)

| Item | Class | Home |
|---|---|---|
| `_active_thoughts` pagination spin needs a concurrent write mid-page | theoretical race | ledgered (story 01 audit) |
| Calendar conductor global double-start | theoretical race, single call site | ledgered (story 02 audit) |
| Calendar conductor thread starts when unconfigured | pattern-consistent with every sibling | ledgered |
| Scheduled-recording conductor shutdown gap | PRE-EXISTING; repair exceeds one-line boundary | ledgered → backlog candidate |
| trust-destinations registry lacks the calendar-fetch entry | named product gap; deliberately NOT faked | ledgered → backlog candidate |
| xdist watch items ×2 (inference-capability census; calendar boot/tick test) | serial-green flakes, first/second occurrence | recurrence = diagnose, not label |

## Counsel and owner gates

The opus close counsel's verdict is recorded in
`current-phase-status.md`'s decision log next to this summary — two
minds on the close, disagreements included. Open owner gates at close:
the shot verdicts (the board set and the rail/Go/settings set, both
delivered) and the merge word for the unpushed branch line
(`feat/phase-144-charter` → `feat/hs144-06-walk-close`).

## Pointers

- Phase status, settled design, decisions, ledger:
  `current-phase-status.md`
- Walk record: `assets/story-06-walk-report.md`, pairs manifest
  `assets/story-06-pairs.md`, shots `assets/story-06-shots/`
- Audit evidence base: `assets/audit-a-pillars-census.md`,
  `assets/audit-b-front-door-walk.md` (+ before-shots)
- Per-story evidence: `evidence-story-01..06.md`
