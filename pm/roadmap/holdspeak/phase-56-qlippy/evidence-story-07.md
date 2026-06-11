# Evidence — HS-56-07: Closeout: live dogfood + final-summary + PR

**Date:** 2026-06-11
**Branch:** `phase-56-qlippy`

The closeout's full evidence lives in [`final-summary.md`](./final-summary.md)
(shipped in this same commit); this file records the story-level proof.

## 1. The all-in-one live dogfood

`dogfood_story07.py` — one live runtime, zero mocks, every card driven by a
real broadcast over the real `/ws` socket:

```
PASS  the dock followed real socket broadcasts [('listening', 'listening'),
      ('processing', 'thinking'), ('complete', 'approve')] and settled idle
PASS  the queue held a race: the sticky decision card stayed, '+1' queued
PASS  audit parity: card approval (approved, 'web-user') == dashboard
      approval (approved, 'web-user'); no side effect on either
PASS  the queued learned card presented (matches 2)
PASS  the aftercare card presented from a real wrap ('Your meeting left 1 open item')
PASS  the served /presence page is byte-identical with the mascot on vs. off
PASS  mascot off: Qlippy stayed hidden through a proposal AND activity
PASS  presence off entirely: Qlippy never appears (the double gate)
PASS  zero page errors across the whole run
RESULT: PASS
```

Five reviewed screenshots: `story07-dock-flourish.png`,
`story07-actuator-card.png`, `story07-queue-race.png` (the sticky decision
card with the "+1" hint), `story07-learned-card.png`,
`story07-aftercare-card.png`.

Notes from the run (per the story's "findings go back to their story"
rule, none required code changes — both were dogfood-harness issues): a
shared action-item id across seeded meetings lets a later save steal the
row (the script now seeds unique ids), and a queued proposal card must be
drained before asserting the next card's headline.

## 2. The audit-parity proof (the phase's central guarantee)

Two twin proposals on one runtime: one approved by a Playwright click on
the **card's** Approve, one by the **dashboard's** exact decision request
(`POST /api/meetings/{id}/proposals/{id}/decision`, `{"decision":
"approved"}`). Both rows read back from the same database:
`(status, decided_by) == ("approved", "web-user")` on each, no execution
performed on either — approving records a decision; the guarded executor
remains the only path that acts.

## 3. The off-proof

- The served `/presence` HTML is **byte-identical** with the mascot on vs.
  off (the gate lives in the boot fetch, not the page).
- Mascot off: `#qlippy` stayed `hidden` through a real proposal broadcast
  AND a runtime-activity broadcast; no card class ever applied.
- Presence off entirely: same silence (the double gate).

## 4. Gates

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2602 passed, 17 skipped in 81.92s (0:01:21)
$ (cd web && npm run build)   # clean, 13 pages
$ git ls-files holdspeak/static/_built/ | wc -l
0
```

BACKLOG: **J → shipped (CLOSED 7/7)**, **G → absorbed-shipped**, **K →
next**. Project README: phase CLOSED + index row flipped. PR to `main`
merged on green CI (recorded in the project README's operating cadence).
