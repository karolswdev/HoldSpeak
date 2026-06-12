# Phase 63 — Backend Decomposition

**Status:** in progress (1/6). Opened 2026-06-12 on owner direction ("E,
puh-lease"): backlog row **E**, the backend twin of Phase 54. The two
god-objects — `web_runtime.py` (2,635 lines, regrown PAST its pre-Phase-52
size) and `meeting_session.py` (1,674) — carve into single-concern modules,
behavior-preserving, locked by a backend density guard.

**Last updated:** 2026-06-12 (**HS-63-01 done:** `meeting_session` is a
package (the planned `holdspeak/meeting/` name was taken by the
MeetingRecorder module — the package conversion keeps the import point
instead, strictly better); the five models live in `models.py` (240 lines,
bodies verbatim, proven by a body-line diff: 0 original lines lost);
**zero test edits** across the 38 importing files. A trap caught mid-story:
indented `try:` optional imports silently swallowed a packaging mistake
(intel became None; 8 tests failed loudly) — the lesson recorded for the
remaining carves. Suite **2768 passed, 17 skipped**. Earlier: scaffolded —
the concern maps, the monkeypatch census, and the test-edit policy are in
the brief §3.)

## The thesis — why this phase

The Phase-48 review called `WebRuntime` "the next central chip under
thermal load"; since then it has only absorbed more (wake word, devices,
routing glue) and sits 294 lines HEAVIER than when the warning was issued.
`meeting_session.py` is the un-flagged sibling: models, recording,
transcription, intel, persistence, and mutations in one file. Phase 54
proved the cure on the frontend and the density guard proved it sticks.
Same disease, same cure, same proof standard.

## Goal

`web_runtime.py` and `meeting_session.py` become thin assembly modules
(boot/lifecycle only) over single-concern mixin modules in
`holdspeak/runtime/` and `holdspeak/meeting/`; every method body moved
verbatim; the full suite is the behavior proof; a scoped backend density
guard locks the shape.

## Scope

- **In:** the meeting models carve (HS-63-01); MeetingSession mixins
  (HS-63-02); WebRuntime feature-glue mixins (HS-63-03); WebRuntime
  platform-glue mixins + the thin core (HS-63-04); the guard + docs
  (HS-63-05); the live closeout (HS-63-06).
- **Out:** `web_server.py` + the route modules (already carved in
  P26/P34; routes/meetings.py stays a watch item); any behavior change;
  any "improvement" to moved bodies; `holdspeak/__init__.py` and the MLX
  thread pinning (load-bearing, Phase 60).

## Exit criteria (evidence required)

- Both cores under the guard budget; every new module single-concern and
  under budget; the guard proven both ways. (HS-63-01..05)
- The full suite green with assertions byte-identical; the only test
  edits are monkeypatch target paths, each listed in evidence.
  (every story)
- The live closeout: the real runtime boots and serves; meeting
  start/stop + a dictation dry-run through the real routes; zero page
  errors. (HS-63-06)
- final-summary; BACKLOG E flipped; PR merged on green. (HS-63-06)

## Stories

| Story | Title | Status | Depends on |
|---|---|---|---|
| HS-63-01 | The meeting models | done | none |
| HS-63-02 | MeetingSession mixins | backlog | HS-63-01 |
| HS-63-03 | WebRuntime mixins: the feature glue | backlog | none |
| HS-63-04 | WebRuntime mixins: the platform glue + thin core | backlog | HS-63-03 |
| HS-63-05 | The backend density guard + docs | backlog | HS-63-01..04 |
| HS-63-06 | Closeout: the live boot proof + final-summary + PR | backlog | HS-63-01..05 |

## Where we are

The models are out. Next is **HS-63-02 — MeetingSession mixins**
(transcribe loop / intel / persistence / mutations out of the 1,460-line
session.py).
