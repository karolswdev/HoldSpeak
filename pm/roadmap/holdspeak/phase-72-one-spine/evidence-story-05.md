# Evidence — HS-72-05 — Retire the shadows

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-72-one-spine`)
- **Owner:** agent (Fable), owner-directed phase

## What was renamed / removed

- **`holdspeak/meeting.py` → `holdspeak/meeting_recorder.py`** (git mv). It
  is the live audio recorder layer (`MeetingRecorder`, `AudioChunk`,
  `DualStreamBuffer`) — the misleading near-namesake of the
  `meeting_session/` package. All nine importers updated (five
  `meeting_session/` modules, `main.py`, three test files) plus the two
  internal-doc references (`LINUX_PORT_EXECUTION.md`, `PLAN_MEETING_MODE.md`).
- **`holdspeak/runtime_activity.py` → `holdspeak/activity_tracker.py`**
  (git mv) — kills the `runtime/activity.py` near-namesake. All twelve
  importers updated (the runtime mixins, `web_runtime`, `desktop_presence`,
  `pages.py`, three test files incl. the renamed
  `test_activity_tracker.py`). **Deliberately NOT renamed:** the
  `runtime_activity` WebSocket frame type, the `_set_runtime_activity` /
  `_broadcast_runtime_activity` methods, and the `self.activity_tracker`
  attribute — those are wire/API names consumed by the web and iPad, not
  the module. (The first sweep renamed them too; `test_web_runtime`'s
  frame assertions caught it immediately and the API names were reverted —
  the tests doing exactly their job.)
- **The `dictation_runner.py` logger** is now `"dictation_runner"` — it was
  literally named `"dictation_runtime"`, the exact confusion the module's
  own docstring warns against.
- **`web/src/scripts/companion-app.js` deleted** (orphan — nothing imported
  it; `companion.astro` loads `companion-desk.js`).
- **`/design/check` deleted** (self-described as to-be-absorbed;
  `/design/components` is the kept gallery). The built-mount tests probed
  the deleted page and were repointed: the static-serve probe to
  `/_built/design/components/` ("Component gallery"), the aria-current
  probe to `/_built/dictation/` (the check page was the only reason that
  page existed).
- **`/activity` linked from the Studio index** — the page was reachable
  only by URL since Phase 70 folded activity into Dictation; it now has an
  honest one-line card ("Local work context: sources, rules, and records")
  under Studio. The four-door nav is untouched.

## Verification artifacts

- Rename-affected slice: **97 passed** (meeting session/chunks, activity
  tracker, web runtime incl. the frame-name assertions, desktop presence,
  device meeting session, dictation runner).
- `cd web && npm run build` → **18 pages** (was 19 — the dead page gone);
  built-mount + route pre-flight **8 passed**.
- Greps in evidence: zero `holdspeak.meeting `/`runtime_activity` module
  references outside git history; the wire frame `runtime_activity` intact
  everywhere it is consumed.
- Screenshot: `screenshots/05-studio-activity-card.png` — the Studio index
  with the Activity card rendered (served by the real app, Playwright).
- Full python suite at ship: **3061 passed, 37 skipped, 1 failed — and the
  one failure was the HS-72-02 manifest guard catching this story's page
  deletion** (an undeclared surface change, exactly its job); the manifest
  was regenerated and the guard is 5/5 green. No other failure.

## Acceptance criteria — re-checked

- [x] The two hub renames with every importer, patch target, and doc
      reference updated.
- [x] The two web deletions; build green; route pre-flight green.
- [x] `/activity` reachable from Studio; nav untouched.
- [x] Wire/API names untouched (proven by the web-runtime frame tests).

## Deviations from plan

- The story planned a sweep of "near-namesake" warnings in
  `ARCHITECTURE_BACKEND_RUNTIME.md`; that file does not exist in `docs/`
  (it was an exploration-report citation). `docs/ARCHITECTURE.md` carries
  no stale references to the renamed modules; the two internal plan docs
  that did were updated.

## Follow-ups

- HS-72-10 (docs) confirms the architecture map names the renamed modules.
