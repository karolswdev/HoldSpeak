# Phase 145 — The Door Polish — final summary

**Verdict:** complete (3/3). Close counsel (opus):
**RATIFY-WITH-CONCERNS, zero should-fixes** — five concerns, all
ledger severity (one withdrawn by the counsel itself); Tuesday
question PASS on all six affordance states; all six orchestrator
judgment calls ruled defensible. Full verdict + dispositions in the
`current-phase-status.md` decision log.

## What shipped

Two close-counsel concerns from Phase 144, dispositioned "polish, not
defects", became product:

1. **The 393 board scroll hint (HS-145-01).** The Door board's
   horizontally clipped columns now announce themselves: a
   scroll-position-honest edge gradient (`--surface-1` dissolve) on a
   non-scrolling hint wrapper, driven by a rAF-throttled listener
   setting `data-scroll-hint="none|right|left|both"`. Absent whenever
   all five columns fit; never lies at either end of the range.
2. **The connect-calendar affordance (HS-145-02).** The empty
   UPCOMING rail dead-end is gone: an unconfigured hub shows
   "No calendar connected." + a ghost **Connect calendar** button that
   opens Settings scoped to the Meetings module in-world. The new
   additive `calendar_configured` projection field is computed LIVE
   from config on both transports (HTTP `/api/door` + MCP `door.get`),
   so the affordance dies the moment a calendar connects — and a
   configured-but-quiet calendar is never nagged.

## The design fought back (recorded honestly)

The plan's sticky in-flow pseudo-elements did NOT paint (zero
resolved height in an auto-height block container). The worker's
glass proof caught it — the shipped design is an outer
`.door-board-hint-wrap` with absolutely positioned pseudo-elements,
plus a 20px `computeScrollHint` tolerance absorbing
`scrollbar-gutter: stable both-edges`. The false-start →
honest-fail → fixed chain is in evidence-story-01.

## Proof

- **Focused suites** (orchestrator-run, output read): 18 Python door
  tests, 18 vitest lane tests, all green; typecheck provenance
  13 = 13 (stash/pop verified at both worker rounds).
- **Glass**: `tests/e2e/test_hs145_door_polish_glass.py` (real hub,
  2 tests) proves the hint state machine on real scroll geometry
  (including that the pseudo-element actually paints) and both
  empty-rail states; 8 shots in `assets/story-03-shots/`, every one
  eyeballed by the orchestrator (magnified edge crops confirmed the
  gradient dissolve), zero byte-identical pairs.
- **Cold walk**: `scripts/door_walk_hs144.py` re-run on the polished
  product — all seven legs PASS (cold 1.85s, completion 52ms,
  schedule, calendar, click-depth, doorframe; cleanup pass). The
  phase-144 walk artifacts the rerun regenerates were restored
  (`git checkout --`) — the 144 record stays the 144 record.
- **Close sweep**: 12 failed / 6736 passed — **baseline-exact, zero
  branch-new**; every FAILED name is in the Phase 143 inherited
  baseline. The stamped `dw evidence capture` record is in
  evidence-story-03 (readable-run + capture PAIR, per the sweep law).

## Sweep triage (the full a/b/c table)

First sweep (pre-triage): 16 failed / 6732 passed. Ten names
baseline-exact. Non-baseline triage:

| Name | Class | Disposition |
|---|---|---|
| `test_hs141_thought_workbench_glass` 1440+393 | (c) known glass-under-load family | serial ×2 green, named |
| `test_calendar_ingest_conductor::test_boot_and_tick…` | cross-arc xdist WATCH ITEM, 2nd recurrence → diagnosed per the recurrence law | TEST race: waited on reader ENTRY, not the receipts it asserts; fixed to wait on the receipts (5s deadline) |
| `test_hs144_door_glass::…populated_glass…` | pre-existing time-dependent seed | the fixed `0 9 * * *` cron made `upcoming_today: 1` true only ~00:00–03:00 local (Phase 144 swept overnight, so it never showed); seed now relative to now, clamped inside today's local day; the sub-two-minute pre-midnight sliver accepted, not mitigated |
| `test_hs144_door_glass::…upcoming_rail…` | (a) asserted the retired posture | unconfigured empty rail now asserts "No calendar connected." + the button; the configured-quiet copy stays pinned in the hs145 e2e |

**Zero branch-new product defects.** The `upcoming_today` failure was
isolated to the test seed with an isolated-service repro AND a
real-hub HTTP repro (both returned 1 on a relative-time seed) before
any code was touched. The three baseline-failing content guards
(product copy, product language, DOM-mutation) were stash-compared at
HEAD vs dirty: byte-identical violation lists — this branch added
nothing to any of them.

## Ledger

- The Phase 144 consolidated ledger stands; its two counsel-concern
  rows are CLOSED by this phase.
- The calendar-conductor xdist watch item is CLOSED (diagnosed +
  fixed on its second recurrence).
- Backlog candidates unchanged (scheduled-recording conductor
  shutdown gap; trust-destinations calendar entry — REAL enforcement
  only, never data-only; multiple calendar subscriptions;
  calendar-event → one-tap scheduled recording).
- New counsel-ledgered items from this close: the scroll-hint
  `useEffect` per-render reattach (ResizeObserver pattern if the Door
  ever renders hot); a debug-log breadcrumb inside
  `_calendar_configured`'s exception swallow (posture stays
  fail-to-nag).

## Owner gates (open)

1. **Shot verdicts** on this phase's 8-shot set — a flinch is a redo.
2. **The merge word** — this branch stacks on the unpushed Phase 144
   line; one PR of `feat/hs145-door-polish` → main delivers both
   phases when the word comes. CI is dead; local verification is the
   record.
