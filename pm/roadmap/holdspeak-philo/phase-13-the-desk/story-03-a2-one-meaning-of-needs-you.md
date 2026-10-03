# PHILO-13-03 - A2 One meaning of "needs you"

- **Project:** holdspeak-philo
- **Phase:** 13
- **Status:** in-progress
- **Depends on:** the owner's ratification of this charter
- **Unblocks:** A2-W (the faces lane's wiring step), PHILO-13-13 (C3's counts)
- **Owner:** Astra (Luna, xhigh); Muad'Dib checks. Wiring step A2-W: Muad'Dib (Fedaykin, Opus 5.5) on `feat/philo-13-muaddib`; Astra checks
- **Lane:** Data + truth (`../wt-philo-13-astra`, `feat/philo-13-astra`)
- **Proposal:** A2 (PROPOSAL §3, Wave A)
- **Closure finding:** `grounding/faces.md:20` (qualified, Astra faces r1 finding 3); `grounding/faces-surfaces.md` F1 (`:188`); Astra charter check r1 finding 3
- **Canvas:** none (one number and its words; the faces it lands on keep their species)

`grounding/` = `docs/internal/philo/phase-13/grounding/`.

## Goal

"Needs you" means one thing, defined by one membership rule in one pure module, everywhere it shows. A window that counts something narrower says what it counts.

## Problem

One label, several meanings. On one screen he reads `8 need you` beside `NEEDS YOU 5 OF 7`; the bell reads 7; Meetings says "Nothing needs you" while the Dock shows 5 (`grounding/shots/surfaces/01-chair-pop-1440.png`, `41-frame-meetings-open-pop-393.png`, `13-meetings-pop-1440.png`, `131-frame2-bell-pop-1440.png`, `64-room-pop-1440.png`). The surfaces count different things: the Chair combines ranked rows and blockers (`web/src/desk/chair/ChairHome.tsx:795-812`, `:825-840`); Meetings counts summary-needed or failed only (`web/src/pages/cores/history/helpers.ts:216-233`); the Dock polls its own read every 60 s (`web/src/desk/components/window/Dock.tsx:60`); the shade reads needs-you on its own 5 s poll (`web/src/desk/components/SystemShade.tsx:149`). The defect is one label with several meanings (`grounding/faces.md:20`).

## The membership rule (Muad'Dib's ruling, r2: the Chair's existing membership is the one meaning)

An item **needs you** when it is one of:

| # | Member | Source today |
|---|---|---|
| R1 | an **unmuted ranked attention row**: the Door board's cards (`overdue`, `now`, `waiting`, `unassigned`) plus the Room's `desk.needs_you` items; a Door card whose action item the Room already emits as a `commitment` row is dropped (the Room's row wins); then `dedupAttention` and `rankAttention`; muted rows (muted projects) are not counted | `ChairHome.tsx:770-812`; `web/src/desk/attention.ts`; `holdspeak/web/routes/projects.py:596-603` |
| R2 | each **meeting-path blocker**: with neither speech nor summary engine assigned, one blocker `engines`; else one per missing engine (`speech`, `summary`); a failed assignment read gives `unknown`; a pending read gives none | `web/src/desk/chair/meetingPathBlocker.ts:71-97`; `ChairHome.tsx:662-665` |
| R3 | each **meeting whose summary state is `FAILED` or `RETRYING`** | `ChairHome.tsx:278-281`, `:825-831` |

`needsYou = R1 rows + R2 blockers + R3 meetings`; the count is their number. Nothing else is "needs you". A narrower count (meetings that need a summary; a Room's own items) is never labelled "needs you".

## Scope

- **In (this lane, H-A2):**
  - `web/src/desk/needsYou.ts` (new, pure): the rule above as one function over its inputs (Door board, Room items, muted projects, assignment summary and read state, meetings), returning the member list (each with its ref) and the count; and one hook that reads those inputs from the existing projections (`web/src/desk/projections.ts:101`; `holdspeak/web/routes/projections.py:20`). It imports `meetingPathBlocker.ts` and `attention.ts` and does not edit Chair files.
  - The Dock badge logic (`Dock.tsx`, this lane's) reads the hook.
  - Any service change the rule needs, in `holdspeak/**` (this lane's).
- **In (A2-W, the faces lane, a named wiring step):** the Chair drops its local membership code (`ChairHome.tsx:278-281`, `:309`, `:770-840`) and reads `needsYou.ts`; the bell/shade (`SystemShade.tsx`, `AttentionDrawer.tsx`) and the Room headline read it; Meetings (`history/helpers.ts:216-233`) and the Room relabel their narrower counts (e.g. `2 need a summary`), never "needs you"; no counter of zero (A.8).
- **Out:** the Chair's open grammar (B1); live push of the count (C3); new attention kinds.

## Acceptance criteria

- [ ] **The oracle week.** A fence mints this week through real producers on an isolated HOME (Door/Room action items through the meeting producer and the project routes; the mute through the heartbeat's muted projects; no engine assigned; meeting summary states through the real summary path or its stored-state producer). Each member has a fixed ref in the fixture:

  | Seeded | Expected |
  |---|---|
  | A1 action item, owner Karol, due yesterday (Door `overdue`) | member (R1) |
  | A2 action item due today, also emitted by the Room as a `commitment` row | **one** member, the Room's row (R1, dedup) |
  | A3 action item waiting on Priya (Door `waiting`) | member (R1) |
  | A4 action item with no owner (Door `unassigned`) | member (R1) |
  | M1 an attention item on a muted project | not a member |
  | D1 a done action item | not a member |
  | no engine assigned for speech or summary | one member, blocker `engines` (R2) |
  | F1 a meeting whose summary state is `FAILED` | member (R3) |
  | S1 a meeting with a stored summary | not a member |

  **Expected membership** = {A1, A2 (Room row), A3, A4, blocker `engines`, F1}; **expected count = 6**. The fence asserts the refs, not only the number.
- [ ] **One mutation.** Mark A1 done through its real route → expected membership loses A1, count 5. (If the real Door classes A1 differently than seeded, the fence records the real class and keeps the expected set fixed by ref.)
- [ ] **A wrong projection fails.** A fence variant that counts muted M1, or counts A2 twice, or drops R3, fails the oracle.
- [ ] The Dock badge reads the hook; on the oracle week it shows 6.
- [ ] **A2-W merged by the faces lane:** on the oracle week, the Chair headline, the bell/shade and the Dock all read 6 at 1440 and 393 (touch); Meetings shows `1 needs a summary` (or its true narrower count) and never "needs you"; the Room's headline never uses "needs you" for its own narrower count. Red on main (the shots above disagree). The story flips `done` only when H-A2 and A2-W are merged; the merge record names both commits.

## Test plan

- **Atlas file:** `docs/internal/philo/graph/atlas-phase13-astra.json` (this lane's only atlas file; `--atlas` per run, `scripts/graph_walk.py:6507`); its count fence in `tests/unit/test_philo13_astra_atlas.py`. The A2-W wiring step's face cases go in `atlas-phase13-muaddib.json` (the faces lane's file).
- **Focused:** web unit on `needsYou.ts` over the oracle inputs and the wrong-projection variants; service tests where the backend changes; `uv run python scripts/check_web_baseline.py --run` (zero branch-new).
- **R2 C1–C4 fences:** a status-filtered `/api/meetings?summary_attention=true` read returns only unparked FAILED/RETRYING Meetings, reports the exact match total, and pages only those matches; the Dock hook makes no all-meeting page read. Its minute read uses cached `/api/desk/needs-you`; only explicit `refresh()` asks for `fresh=1`. Preserve the ref-level Room-covers-Door mutant and prove a code mutant that skips `dedupAttention` fails against a duplicate minted by real producers and the exact six-ref oracle.
- **Glass / atlas:** the oracle week through the real hub: one case reading the Dock (this lane); one case reading the Chair, bell and Dock in one run (A2-W, the faces file); at 1440 and 393 (touch), one case per `scripts/graph_walk.py run` invocation.
- **Shots:** the six shots above, re-taken on the oracle week.

## Worker-brief scars

- **Doubles that lie:** the oracle week is minted through the real producers (`scripts/philo11_send_job.py` `mint` pattern, `grounding/faces-surfaces.md:11`); never a stub that returns the count; the fence asserts member refs.
- **Fences that name old words:** fences that assert `Nothing needs you` on Meetings or the Room change with the word, in the same commit (A2-W).
- **Never rewrite a guard to match a removal:** the Chair's existing needs-you fences (HS-200-15, HS-201-01) rehome onto `needsYou.ts`; none is loosened.

## Effort (not a promise)

Grounding size: not sized as a move. PROVISIONAL.

## Notes

- 2026-10-02 — Muad'Dib counsel on built for PR #728: RATIFY-WITH-CONDITIONS, C1–C4. R3 counts every FAILED/RETRYING Meeting via the bounded status-filtered server read; the minute poll uses the cached needs-you route and `fresh=1` is explicit only; `atlas.schema.json` and `scripts/graph_walk.py` are Astra-owned shared paths with changes requested by named handoff; retain the Room-covers-Door ref mutant and add a code mutant for skipped `dedupAttention`. See [H-A2 r2 condition contract](handoff-a2-astra.md). A2-W remains the other half; the story stays in-progress until both merge.
- 2026-10-02 — r3 paid Muad'Dib's signed R1/R2 conditions for PR #728. The five source-reference fences now point to their current symbols, and the generated API, OpenAPI, boundary and graph references were regenerated. The old Room title-match suppression is removed: title equality is not a link between a project milestone and a meeting action. The oracle's seeded Room milestone uses a distinct title and future due date. A separate regression fence mints a same-title overdue milestone through the real project route, marks A1 done through the real action route, and asserts Room health still counts the milestone (1 before, 1 after); the old predicate failed at 1→0 ([red](assets/story-03-needs-you/r3/r2-title-match-pre-fix.txt), [green](assets/story-03-needs-you/r3/r3-focused-green.txt)). The five old atlas anchors fail their shared semantic fence before correction ([red](assets/story-03-needs-you/r3/r1-source-anchors-pre-fix.txt)). All Documentation Navigation commands pass ([log](assets/story-03-needs-you/r3/documentation-navigation.txt)). The real Dock case then passes at 1440 and 393 native touch ([r3 walks](walks-03-astra.md#r3-actual-dock-walk)). This supersedes the temporary suppression described in the r2 record below. Story 03 remains in-progress pending A2-W and Muad'Dib's check; no done flip.
- 2026-10-02 — r4 paid the C4 code-mutant condition on #728. The pre-fix test receipt shows `rejection: NONE`, expected 6 and actual 6 because the canonical week correctly keeps the A1 Room milestone title distinct ([red](assets/story-03-needs-you/r4-c4-before.txt)). A separate `dedup-probe` now saves a second real A2 action, links its meeting with the real project route, and reads `/api/door` plus `/api/desk/needs-you?fresh=1`. Its Room commitment does not cover the added action ID. Normal membership returns the fixed six refs; a mutant that skips `dedupAttention` returns 7 and includes `philo13-a2-dedup-A2` ([green](assets/story-03-needs-you/r4-c4-after.txt)). The shared/A2 Python selection collected and passed 132; seven focused web files passed 63; typecheck passed. All 12 Documentation Navigation commands and the operations, OpenAPI and graph reference checks passed ([generation](assets/story-03-needs-you/r4-final-generation.txt), [checks](assets/story-03-needs-you/r4-doc-navigation.txt)). PHILO-13-03 remains in-progress until A2-W merges; no face code changed in this r4 payment.
- 2026-10-02 — R2 actual Dock walk exposed a cache invalidation defect. Its second run showed a same-project Room milestone with the same title as the completed meeting action remaining visible. The r2 implementation briefly suppressed that row, but Muad'Dib's r3 R2 ruling rejected title as a relationship and required the suppression to be removed. The route fence still PATCHes only real A1 and checks the cached route rebuild and five-ref oracle; the current fixture has no title collision. Historical shots and observations remain in [r2 walks](walks-03-astra.md), with the superseding ruling and current regression proof recorded here. H-A2 remains pending Muad'Dib's check and A2-W; no done flip.
- 2026-10-01 — H-A2 built in Astra's lane; [handoff](handoff-a2-astra.md), [proof](lane-03-astra.md), [actual walks](walks-03-astra.md). DRAFT — UNCHECKED — awaiting Muad'Dib. Story remains in-progress until H-A2 and A2-W both merge; acceptance boxes remain open for that closing verification.
- 2026-10-01 — r2: Astra charter check r1 (DO-NOT-RATIFY) paid; see the status file, "Round two". The membership rule is Muad'Dib's ruling (the Chair's existing membership). `history/helpers.ts` and the Room headline are Muad'Dib's (A2-W), not this lane's.
- 2026-10-01 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
