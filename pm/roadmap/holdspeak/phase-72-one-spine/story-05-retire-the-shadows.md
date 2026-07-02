# HS-72-05 — Retire the shadows

- **Status:** todo
- **Priority:** MED (each item is small; together they are why newcomers mis-patch)
- **Depends on:** —

## Goal

Remove or rename everything that exists twice under confusable names, plus
the confirmed orphans. These are the traps the architecture docs warn about
in prose; after this story the prose warnings can be deleted because the
traps are gone.

## Scope

- **In (hub):** rename `holdspeak/meeting.py` → `holdspeak/meeting_recorder.py`
  (verified live: the recorder layer imported by five `meeting_session/`
  modules + `main.py:439` — a rename with import updates, NOT a deletion);
  rename `holdspeak/runtime_activity.py` → `holdspeak/activity_tracker.py`
  (kills the `runtime/activity.py` near-namesake; grep tests for patch
  targets); fix the `dictation_runner.py:28` logger name
  (`dictation_runtime` → `dictation_runner`).
- **In (web):** delete `web/src/scripts/companion-app.js` (orphan — nothing
  imports it; `companion.astro` loads `companion-desk.js`); delete
  `web/src/pages/design/check.astro` (self-described as to-be-absorbed;
  `/design/components` is the kept gallery); resolve the `/activity` orphan —
  the page is reachable only by URL since Phase 70 "folded it into
  Dictation": link it from the Studio index as the activity admin surface
  (deferred-decision default; flag to the owner if folding its
  domains/connectors panes into Settings looks better while in there).
- **Out:** `meetings.py` (HS-72-06); the two JS-loading conventions sweep
  (recorded direction only); deleting `/api/activity/*` (live: consumed by
  the dictation partials and the iPad).

## Tasks

- [ ] The two hub renames + logger fix, with every importer, patch target,
      and doc reference updated (grep `tests/` for the old dotted paths —
      the Phase-63 lesson).
- [ ] The two web deletions; `npm run build` green; route pre-flight green
      (no dead links to `/design/check`).
- [ ] `/activity` linked from `/studio` with an honest one-line card; nav
      untouched (the four doors stay).
- [ ] Sweep the architecture docs' "beware the near-namesake" prose that the
      renames obsolete (`ARCHITECTURE_BACKEND_RUNTIME.md`).

## Proof required

Zero grep hits for the old module paths outside git history; full suite
green; web build + route pre-flight green; a screenshot of the Studio index
showing the activity entry; the docs diff removing the obsoleted warnings.
