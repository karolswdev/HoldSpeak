# HS-163-06 - The walk: STW-011 on glass — one real effect, receipted

- **Project:** holdspeak
- **Phase:** 163
- **Status:** done
- **Depends on:** HS-163-04 (rig vs the wire; face legs after 05's functional)
- **Unblocks:** HS-163-07
- **Owner:** unassigned

## Problem

STW-011: a successful dogfood run MUST perform at least one real,
deduplicated effect beyond summarization and record its
verification/receipt. The exit bar, measured on glass.

## Scope

- **In:** tests/e2e/test_hs163_steward_glass.py (the house rig):
  (1) THE DOGFOOD LEG — seeded room with a stale source + an
  overdue high-material item → Run once from the mounted posture →
  the run completes with ≥1 real effect (the Door item AND/OR an
  applied proposal + the drafted update) → the receipts render and
  open → re-run at the same watermark ⇒ ZERO duplicate effects
  (the dedup law on glass). (2) THE STOP LEG — slow-phase fixture,
  Stop mid-run → stopping → interrupted, honest summary.
  (3) THE DEGRADED LEG — a failing source isolates to partial
  coverage (STW-006) and a dead model falls back deterministically
  (STW-007), both visible and honest. (4) run-history rows: the
  no-raw-ids regex law + designed-row assertions at both viewports.
  Segments/timing into assets/story-06-stopwatch.json where a bar
  applies; shots both viewports >20KB; fixture legs ×2
  deterministic.
- **Out:** scheduling.

## Acceptance criteria

- [ ] STW-011 proven on glass with the receipt chain openable; the same-watermark re-run duplicates NOTHING.
- [ ] Stop + degraded legs deterministic ×2; overflow zero; no raw ids.
- [ ] The walk record carries the effect inventory (what the hand actually did).

## Test plan

- **E2E:** the four legs; build-first; ×2.
