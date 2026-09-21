# HS-202-02 - First-use doors and truthful state

- **Project:** holdspeak
- **Phase:** 202
- **Status:** done
- **Depends on:** none
- **Unblocks:** (optional)
- **Owner:** unassigned

## Problem

From the surface inventory of 2026-09-20 (`docs/internal/SURFACE-INVENTORY-2026-09-20.md`, §6 story 02; appendices 01–04; Astra's check `docs/internal/checks/surface-inventory-astra.md`). The Seven Tenets govern: first-use first (2), one obvious move (3), the component framework (5), Workbench 2.0+ (6); Articles III and VI; UX-CANON A.

## Scope

- **In:** each item names the job it unblocks (docs/internal/SURFACE-INVENTORY-2026-09-20.md §6 story 02, as re-cut after Astra's round two): job 1 the microphone recovery; job 2 the record refreshing on assignment and run, EgressChip NOT SET by default, the false badges on the path, tokened startup URLs; job 3 Write a thought opens a note and saving confirms; job 4 ⌘K commits the typed match, Desk memory shows the desk's memory; job 5 the assignments door, the LAN placeholder removed; all jobs at 393 the dock fits and the four menus open; the arrival's Generate badged and receipted, one Ask AI door.
- **Out:** everything the inventory's §6 ledger records; faces the five owner jobs do not touch; the broad census numbers as gates (they are diagnostics re-run at phase close).

## Acceptance criteria

- [ ] each item with a fence red first; the first-use smoke green at both widths
- [ ] Every change has a fence proven red first on a real isolated hub; shots at 1440 and 393 in this story's assets; the first-use smoke (story 01) green after the change.
- [ ] Every verb the library Button; no prose; no modal; no counter of zero; one filled primary per window; labels in ASD-STE100.

## Test plan

- **Unit:** the fences the story names; vitest for face rules.
- **Integration:** the first-use smoke at both widths; the focused rigs the story touches.
- **Manual / device:** shots; story 06 is the owner's sitting.

## Notes / open questions

### Counsel fix round 2 — what changed and what is still open

- **Fixed, each fenced red-then-green:** the cold-desk recovery registry
  (`SurfaceWindows.tsx:61`), the brief receipt surviving success
  (`ChairHome.tsx:1114`) and its count reading the brief's real
  `sections`, the stale-selection guards in `HistoryCore` AND
  `useMeetingData`, `LiveCore`'s runtime-status subscription, the visible
  failure on a refused note create, the RECENT read over every memory
  kind (`db/memory.py` `recent()`), one live row per name in ⌘K, the
  microphone wording, the first-value vocabulary debt paid in full, the
  import announcing itself (`meeting_service.py`), and the folded Go menu
  scrolling so its Object and Window entries are reachable at 393.
- **Found by this story's own walk and fixed:** opening the doctor from
  the cold card and then pressing `Continue later` left the card spinning
  forever — a recovery window was still on glass when first value handed
  over. `FirstWords.dismiss` clears surface windows first.
- **STILL RED:** the first-use smoke's `import-refresh` leg at both
  widths. The hub now emits `desk_changed` on import completion (proved
  in-process, and traced live inside the smoke's own hub with
  `root=True`), and the face merges rather than replaces, but the open
  record still does not expose `Run summary` inside the fence's 2.5 s
  window without a reopen. Every other leg of that smoke passes (35 PASS
  lines). Next step for whoever picks it up: instrument the client's
  `desk_changed` handler in the smoke's browser — the frame leaves the
  hub, so the remaining gap is between the bus and `refreshFace`.
- **Inherited, not mine (evidence in the report):**
  `tests/unit/test_doc_drift_guard.py` (dangling links in
  `docs/internal/checks/surface-inventory-astra.md`, present unchanged at
  the base commit), `tests/e2e/test_hs154_call_glass.py` (the `tts` extra
  IS installed in this worktree's venv, so the "not installed" copy is
  correctly absent), `tests/unit/test_hs175_calendar_sources.py` (a
  local-week boundary case on a Sunday evening),
  `tests/e2e/test_hs170_meetings_glass.py::test_meetings_face` (needs an
  open action item to draw the facet; my diff touches no line of that
  path).

### Ledger — classifications and homes (Astra's counsel on PR #595)

- **PAID HERE, not deferred:** the first-value failure vocabulary
  (`holdspeak/db/onboarding.py:17-33`). Naming `no_microphone` on the face
  made `POST /api/setup/first-value/<id>/finish` answer 400; the same gap
  already existed for the three HS-132-05 streaming refusals
  (`mic_interval_closed`, `provider_failure`, `audio_floor_held`), which
  the face has been able to send since that story. All five names are now
  accepted and fenced against drift in
  `tests/unit/test_hs202_first_value_failure_vocabulary.py`. Nothing is
  left with "next lane" as its home.
- **(a) honest test updates** (the behaviour changed, so the fence did):
  `web/src/pages/cores/__tests__/speakRoom.test.tsx:420` (the footer no
  longer claims a placement), `web/src/desk/__tests__/menuGlyphs.test.tsx:174`
  (4/11 -> 4/12 Go tools, because `configure-setup` was unparked and given
  a door), `web/src/lib/dictationRecovery.test.ts` and
  `web/src/desk/components/FirstWords.test.tsx` (the microphone wording
  now claims only what the exception supports),
  `web/src/desk/chair/__tests__/briefBadgeReceipt202.test.tsx` (the
  receipt counts the brief's real `sections`, not an `items` field
  `MondayBrief` never had).
- **(a) rig change, opt-in:** `scripts/walk_working_desk.py` gained
  `HOLDSPEAK_WALK_SKIP_BRIEF=1`, so a walk can photograph the arrival's
  `No brief yet` + `Generate` branch. Unset, the seed is byte-identical.
- **Design debt, named not scheduled:** the first-run card's species
  mixing (four button species, three font stacks, a 20x20 orphan mic on
  the pad) — the owner raised it on 2026-09-20. It is a design beat that
  needs the canvas and his ratification first (UX-CANON A: design before
  build); story 05 settles the type scale it depends on.


Lanes are assigned at build time under TWO-BRAINS §4 (default: Astra takes the backend and verification-harness work, Muad'Dib the faces; either brain checks the other's built lane before merge).
