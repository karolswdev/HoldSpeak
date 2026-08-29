# HANDOVER — one tap, one honest loop (written 2026-08-29)

For the next agent. Supersedes the "many calendars" handover of
2026-08-28 (historical). Read this whole file, then orient
(`.githooks/dw context holdspeak --compact`; the README "Current
phase" line is truth), then go. The owner's verb this arc was the
strongest yet: **"push this as much as you can, without any of my
prompts"** — a standing goal carried the merge word in advance. Run
whole arcs; put menus up only for genuinely-owner decisions.

## 1. What the world looks like now

- **Phase 147 (One-Tap Record) chartered AND closed inside one
  open-throttle day** (2026-08-28 late → 2026-08-29), 7/7, on
  `feat/hs147-one-tap-record`, merged on the pre-given word right
  after this handover — check `git log main`.
- **The product now:** the flywheel is WHOLE. An UPCOMING rail
  event carries **Record this** — one tap creates an event-linked
  Phase-136 one-shot computed entirely server-side (title, duration
  w/ remainder rule + 480 cap, `next_fire_at = start − 60 s`), the
  row wears **ARMED** + two-beat **Cancel?**, refusals are named
  in-flow (**ALREADY ARMED / EVENT ENDED / EVENT NOT FOUND**). The
  arm FOLLOWS the feed (R1 refresh-in-place incl. end-time-only
  extensions; R2 nearest-uid rebind; R3 `event_removed` cancel; X1:
  a live arming/recording is NEVER yanked; D3b idempotence).
  Snapshot UIDs are content-deterministic (re-imports keep
  identity). The fired meeting carries `calendar_event_id` through
  the explicit `pending_calendar_event_id` seam and wears
  **FROM \<SOURCE\> · \<EVENT\>** on the Meetings surface, with the
  field surviving the sync wire (round-trip fixed + pinned this
  arc). One intent renders ONE row (linked schedule suppressed
  while its event is on the rail). The two 146 snapshot ledger
  riders shipped (422 surfacing; vision pre-filter, zero wasted
  dispatch).
- **The record:** `phase-147-one-tap-record/` — audits, the
  counsel-ruled settled design (§2b BEFORE build: RATIFY-W-C, zero
  must-fix, three should-fixes absorbed pre-code), evidence 01–07
  each with an orchestrator triage note, final-summary.md, the walk
  under `assets/story-07-walk/` (8/8 ×3), shots in
  `assets/story-02-shots/` + the walk dir.
- **Close counsel: RATIFY-WITH-CONCERNS, ZERO must-fix**; all five
  orchestrator judgment calls ACCEPTED; human-compliance verdict:
  *"The one tap does what it says."*

## 2. The consolidated ledger (owner-visible, carried)

| Item | Class |
|---|---|
| Adjacent recurring arms colliding on an R2 rebind (L1 refuses the second honestly; re-armable) | design counsel |
| Identical snapshot events collapse to one deterministic uid | design counsel |
| Rare pre-read-failure R2→R3 degrade (loud, re-armable; needs a DB read failure inside one tick) | story-03 triage |
| Reappear-claim wording over-broad (reconciliation closes the gap in practice) | close counsel |
| Fire-seam setattr-chain lambda fragile by construction (refactor note, not a bug) | close counsel |
| hs144-era in-world schedule row's STARTS label rendered an odd instant in the walk fixture (pre-existing leg, 8/8 ×3 green) | recorded note, polish candidate |
| No real-vision-model probe has ever run (snapshot adapter) | carried from 146 |
| Phase 145/144 carried items stand | carried |

**Flake families:** unchanged (hs143 s5, hs141 thought-workbench,
refinement recovers-owner); serial ×2 protocol; recurrence beyond =
DIAGNOSE. Inherited baseline: still the 143 file; close sweep was
baseline-subset (11 names), 6862 passed.

## 3. What to work on next (menu for the owner)

1. **Event → recording → intelligence on real metal** — the loop
   exists; a real fired meeting through a real model on `.43` is the
   control-vs-treatment moment (pairs with the still-unrun vision
   probe).
2. **The rail polish set** — the STARTS-label oddity; the counsel
   wording/refactor notes; maybe the armed row surfacing its
   duration.
3. **BACKLOG.md** — JIRA Desk Sync (W, plan filed) was the runner-up
   in the 147 menu; Candidate Z (inherited ledger) still stands.

Standing charter questions: **"will you use this on a tired
Tuesday?"** and **"does this operate with joy?"**

## 4. Standing laws (all prior eras', plus this arc's)

1. Everything in the 146 handover §4 stands (YOLO bar + tie-breaker;
   models law; stub law; cross-read shots; ISO-offset law;
   guard-forced registration; baseline-guard stash-compare).
2. **Guard files are ORCHESTRATOR-owned (new):** lane briefs must
   say so explicitly — a builder saw census fallout, called it
   "pre-existing", and was wrong TWICE this arc; the orchestrator
   triages every guard failure personally. Remap only verified 1:1
   drift (five remaps this arc, all clean).
3. **The design beat pays before code exists (proven):** the
   pre-build counsel caught the invisible-extension defect (R1
   refresh-in-place) that would have shipped wrong.
4. **The shot cross-read is a design instrument (proven again):** it
   minted the one-intent-one-row ruling mid-story.
5. **Tool timeouts kill background sweeps at 10 min** — run full
   sweeps detached (`nohup … & disown` + a done-file watcher), or
   they die at 98%.
6. **Stalled subagents:** a whole wave can wedge ~1 min in on one
   API hiccup (three at once this arc). SendMessage to the stopped
   id RESUMES with context intact — stop + resume beats relaunch.
   Arm a transcript-growth watchdog for waves.

## 5. Mechanics (unchanged + additions)

- Sweep recipe, isolated HOME, asset-clobber restore (now incl.
  phase-147 dirs), repo-root cwd law — all per the 146 handover.
- The cold walk is `scripts/door_walk_hs144.py`, now EIGHT legs
  (`one-tap` added; appends its calendar source beside existing
  ones and restores — never replace the list, click-depth asserts
  on the calendar leg's fixture). Rerun before any Door-touching
  flip.
- New glass proof: `tests/e2e/test_hs147_one_tap_glass.py` (rig
  selectors: door-record-this / door-armed-chip / door-cancel-prompt
  / door-cancel-confirm / door-arm-refusal; origin line:
  `[data-meeting-origin="calendar-event"]`).
- Walk-report pair machinery requires `--out` INSIDE the repo.
- Memory: `~/.claude/.../memory/project_phase147_one_tap_record.md`
  holds the arc details; MEMORY.md Active list current.

Go get the owner's next word. The rail has a verb, the arm follows
the truth, and a tired Tuesday is one tap from a meeting that
remembers where it came from.
