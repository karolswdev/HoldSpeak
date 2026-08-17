# Phase 135 — The Comfy Chair: final summary

**Verdict sought:** complete (15/15), one day (2026-08-16/17), zero
regressions, the owner refining live throughout. Owner sitting
pending; counsel opinion recorded alongside.

## What shipped

**HoldSpeak opens on the Chair.** The jobs-first front door the owner
mandated ("fewer doors — and that door needs to be beautiful") is the
product's landing surface, built on the counsel-ruled law book and
refined against the owner's live screenshots the same evening:

- **The hub opens its own desk** (`eaa6e35c`): the 59→60 migration P0
  root-caused (v59-stamped DB with v58 mesh shape; the guard never
  fired) and fixed with an idempotent pre-schema column guard —
  verified by the orchestrator on a copy of the owner's real backup.
- **The law-book debts paid**: lamps wrap (`b70b0c3e`), wings look
  pressable, seven sizing tokens land with 21 sites migrated
  (`3ea9f9de`), sparse surfaces shed chrome (`fdd91aa3`).
- **The Chair itself**: shell + lane contract + single-instance
  windows (`e244c61b` + registry seam rider), Chair-is-home with the
  Floor one dock button away (`a506500a`), four lanes — Brief with the
  never-false-clear fence (`9000004d`), Follow-Through with the
  hidden Wave-2 verb slot (`68eeac6a`), Meetings with live pinning
  (`84e769db`), Agents blocked-first (`8de7e0ce`) — and the capture
  hero (`6c97f233`): tap records, "start meeting" by voice, Ask AI
  one tap, the ember gradient nowhere else.
- **The desk clicks** (`4aa53693`): six synthesized mechanical sounds
  (16.4KB), pool-capped sfx runtime, DESK SOUNDS toggle,
  reduced-motion mutes.
- **The chrome speaks Workbench** (`20d55b2d`): fifteen sprites cast
  through the owner-ratified bright mold ("AMIGA OS FOREVER"; the
  dark first mold rejected), contact-sheet-gated with two orchestrator
  rejections re-cast; mic states idle/listening/recording; Cadence
  gets its metronome identity; per-meaning empty states; the floor
  glyph; the editor mic aligned.
- **Creation operates** (`42e9eb2e` + the walk's fix-it): the joy
  audit's dead end had TWO real causes the walk exposed — the
  InlineEditor was never mounted on the Chair surface, and window
  shell focus stole the autoFocus. Both fixed; name-field focus
  proven on glass; Run ghosts with its reason; "No agents yet" with a
  working create loop.
- **The walk** (closing commit): committed harness, 24 shots at
  1440+960 with all four lanes populated, the empty-void polish (the
  hero holds the room; "Speak. The desk will file it."), zero console
  errors unfiltered, sound proof, and four owner riders refined live
  from screenshots (Brief count separators, BLOCKED/Answer gap, the
  invitation line, the workbench inlet rebuilt: mic seated in the
  row, RESOLVER CLOUD becomes a real EgressChip, the priority cycler
  explains itself, GO becomes Add).

## The stopwatch verdict (the phase's own justification)

| Job | Baseline (Floor) | The Chair | |
|---|---|---|---|
| Record a meeting | 1 action, no voice | 1 action, **voice NEW** | IMPROVED |
| Capture a 1:1 note | 7 actions | 5 | held (Cmd+N path) |
| Capture a TODO | 6 actions, no home | 5, still a note | held, honest — Wave 2 |
| Ask a question | 4 actions, wrong door likely | **2-3, one tap on the hero** | IMPROVED |
| Check on agents | 2 actions | **1 — blocked visible on landing** | IMPROVED |

Both chartered targets met (Record holds at 1 + voice; Ask beats the
baseline). Method caveat (counsel concern, acknowledged): the baseline
was a Playwright-instrumented run; the Chair's numbers are structural
action counts from the walk (a hero tap IS one action) — defensible
but less instrumented than the baseline. A fully instrumented re-run
rides the next leg's walk.

## Judgment calls the orchestrator made alone (for review)

1. Two owner-directed mid-phase amendments (stories 14, 15) — both
   from the owner's explicit screenshots-in-hand mandates; visible in
   the Amendments section.
2. The lane-registry and per-family-test amendments to keep seven
   parallel workers collision-free.
3. Contact-sheet quality control: two castings rejected on the
   orchestrator's eyes (pixel-noise mic-listening; invisible
   menu-mark) before the owner saw the final sheet.
4. The fix-it round's scope: four walk defects + four owner riders in
   one round rather than shipping a walk with named holes.
5. The Dashboard Door routing: the owner's module mandate (TODO
   kanban, upcoming meetings, schedule-recording) explicitly NOT
   absorbed — chartered as the next leg with the owner's agreement.

## The ledger

- Five distinct single-run xdist timing flakes across the arc's gates,
  each 3/3 green serially → BACKLOG Candidate Z.
- The final gate's only failure: the voice-rules guard catching the
  orchestrator's own em dashes. Fixed; recorded as the system working.
- The walk could not exercise: 393w (Phase 136 owns it); the
  note-editor shot captured a stale window (cosmetic; the editor is
  test-covered).
- Next leg (The Dashboard Door) carries: the owner's module mandate,
  the setup-joy redesign (jargon wall, progressive disclosure, session
  naming, Agent/Agents collision), the calendar-connector decision
  (held owner question), and the config-panel design work.

## Held for the owner sitting

1. Lane hiding/collapse (counsel Q2 deferral — confirm).
2. The tolerant mir_profile fallback retirement window (Phase 134
   leniency, counsel: one more wave).
3. The Dashboard Door charter's calendar-connector choice.

## Evidence pack

Fifteen evidence files; the ruled law book + counsel ruling + bright
icon mold + contact-sheet flow in assets/; 24 walk shots + the live
transcripts; the stopwatch table above from the walk's captured run;
harnesses committed: `scripts/chair_walk.py`.
