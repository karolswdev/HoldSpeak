# Phase 175 — Calendar and the Clock — final summary

**COMPLETE 9/9 (2026-09-06) on the owner's word ("You got my word for a merge.").** 01 design · 02–05 wire + faces · 06 the walk (the runner's read-only walk on his desk; his attended walk owed, as for 169–174) · 07 hygiene · 08 docs · 09 the close. Branch `feat/calendar-clock`; PR #558 → main.

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

## The seven questions — RULED (2026-09-06, on the owner's deferral: "The decision is deferred to you")

| # | Question | Ruling |
|---|---|---|
| R1 | Auto-link vs suggestion-only | Auto-link stays (open throttle), tightened: a Room's FULL name must appear as a phrase; a one-word Room name links only if it is not a generic meeting word (design, review, standup, sync, …). Unlink stays the remedy. Shipped as a follow-up on main. |
| R2 | The toggle: record at the event, or arm-and-wait | Record at the event, like every scheduled recording; OFF by default. A recording that waits for a hand is not a scheduled recording. |
| R3 | Cancel on a recurring meeting | This occurrence. A series cancel is a later verb, if ever asked. |
| R4 | Remove means gone | Yes — the source, its events, its armed recordings, a snapshot's generated file. |
| R5 | Whose clock | The hub's local clock, per instant. |
| R6 | `THIS WEEK` vs the board's MEETINGS | `THIS WEEK` stays; the recorded-meetings ledger owns MEETINGS. |
| R7 | The two `Sprint Review` seed rows in his database | Deleted through the product's own meeting delete (receipted) after a read-only census confirmed they are the only walk seeds. |

His attended walks (170–175) stay owed.

## Parked (BACKLOG.md)

The 393 Intelligence-row overlap (172), per-source refresh status, the Snapshot verb's place, UTC week edges (paid), the review core's egress chip, the board's `2 CALENDARS` text, Retire on the row, the `0 MIN` counter (172), counsel's P2 ledger.
