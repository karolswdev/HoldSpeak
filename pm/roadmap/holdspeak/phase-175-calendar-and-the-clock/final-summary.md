# Phase 175 — Calendar and the Clock — final summary (DRAFT: his attended walk and the close still open)

**State at c98ccf2f (2026-09-06):** 7/9 — 01 design · 02–05 wire + faces · 07 hygiene · 08 docs DONE; 06 his attended walk OPEN (the runner's read-only walk ran on his desk, evidence captured, ships with his flip); 09 the close OPEN. Branch `feat/calendar-clock`; draft PR #558 on main.

## What the phase bought (the Tuesday)

The calendar gave the desk its clock: the arrival's WEEK strip and `NEXT · <title> · HH:MM · ROOM · <name>`, the THIS WEEK section with `ARMS HH:MM` and a Cancel that works for the row's whole life and is final; Settings → Meetings' CALENDAR section (sources with their egress, Add · Snapshot, one well with a mic, Edit · Disable · Remove, Auto-record with `5 MIN BEFORE` and `N MATCHED THIS WEEK`); the Room's real meeting Watch (`MTG · MEETINGS · N THIS WEEK · NEXT DAY HH:MM · CHECKED`, Pause/Resume, Retire a tombstone), feeding SINCE YOU LOOKED; Rhythm's `Weekly brief · DAILY 08:00` and the brief's THIS WEEK / SINCE FRIDAY at one gutter.

## The gates

| Gate | Result |
|---|---|
| Design | RATIFY-W-C (five conditions paid, Addendum 1); build rulings B1–B17 (Addendum 2) |
| Counsel on the built phase | BOUNCE (12 conditions, 6 reproduced) → paid → re-read RATIFY-W-C, five of six paid; the sixth is his walk (`assets/counsel-on-built-175.md`, `-reread.md`) |
| Faces | four lanes, every face shot beside its board at 1440 + 393 (`assets/story-0{2,3,4,5}-shots/`) |
| Unit set + fences | 496 passed (-n auto, isolated HOME) + 188 in the 07 capture |
| Web baseline | zero branch-new (`scripts/check_web_baseline.py --run`) |
| UX canon ratchet | green; A8 healed 25 → 24 |
| Rigs | the 175 rigs + 170/171/172 neighbours 58 passed serially; one Room-open timeout and two setup errors pass alone |
| Full suite (CI shape, -n auto) | 9998 passed · 97 skipped · 23 failed = 6 inherited (ask grounding ×2, ask runner migration, the two broker density fences, product copy — identical to main) + the xdist-only rig family (hs144/152/153/154/174) + mid-edit failures re-run green serially + four fences paid in c98ccf2f |
| Docs | thirteen verify-at-build markers paid; mermaid render guard 2 passed; drift guard green (shots under docs/assets) |
| Schema | 75, additive (`owner_cancelled_at`, `calendar_starts_at`, `calendar_event_link_suppressions`); canonical snapshot regenerated |
| API surface | 667 routes (`GET /api/calendar/sources`; the unlink route with its consumer) |

## Scars (laws now)

- A worker's `git stash` in the shared tree wiped ten files; recovered from the dangling stash commit. Law in `.claude/agents/opus-worker.md` and memory: no git verb that moves the tree; the orchestrator reads `git reflog` before every verification run; rigs re-shoot other phases' assets — restore before staging.
- Earlier walks (167/168) left seed meetings in the owner's real database; the 175 runner found them read-only. His rows; listed for his sitting.

## Owed to the owner (his sitting)

1. Auto-link vs suggestion-only (a Room named `Design` links a 401k webinar; Unlink is the remedy). 2. The toggle: consent to record at the event (built) or arm-and-wait. 3. Cancel on a recurring meeting: this one (built) or the series. 4. Remove means gone (built). 5. Whose clock: the hub's local (built). 6. The arrival's `THIS WEEK` caption vs the board's MEETINGS (B10). 7. The two `Sprint Review` seed rows are his to delete. Then: his attended walk (06), the close (09), #558 out of draft, merge on his word.

## Parked (BACKLOG.md)

The 393 Intelligence-row overlap (172), per-source refresh status, the Snapshot verb's place, UTC week edges (paid), the review core's egress chip, the board's `2 CALENDARS` text, Retire on the row, the `0 MIN` counter (172), counsel's P2 ledger.
