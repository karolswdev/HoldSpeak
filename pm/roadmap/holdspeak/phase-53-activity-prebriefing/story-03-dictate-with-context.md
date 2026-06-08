# HS-53-03 — Dictate with this as context

- **Project:** holdspeak
- **Phase:** 53
- **Status:** done
- **Depends on:** HS-53-01
- **Unblocks:** HS-53-04
- **Owner:** unassigned

## Problem
The point of a per-record nudge is the action: "dictate a reply with this issue as
context". The dictation pipeline already receives an activity context bundle, but there
is no way to say "use this specific record" when a user picks one from a nudge.

## Scope
- **In:**
  - Extend the activity-context path so a **nudge-selected `ActivityRecord`** is injected
    into the dictation pipeline as context. Either an override parameter on
    `ActivityContextProvider` / `build_activity_context` (`activity_context.py:45,86`) that
    pins/boosts the selected record, or a small endpoint the dictation flow consumes to
    build a one-record context bundle.
  - The selected record's entity (e.g. `github_issue owner/repo#123`, title, url) is
    available to the rewrite stage when the user dictates after picking it.
  - **Default unchanged:** with no selection, dictation builds context exactly as today
    (byte-identical). The override only applies when a record is explicitly chosen.
- **Out:** the nudge UI button wiring (HS-53-04 calls this); the engine (HS-53-01).

## Acceptance criteria
- [x] A selected `ActivityRecord` can be injected as dictation context; the rewrite path
      sees its entity/title/url.
- [x] With no selection, the context build is unchanged (a test asserts the default path
      is byte-identical).
- [x] The override is local + read-only (it reads an existing record; it does not fetch
      anything new).
- [x] Unit/integration tested (selected-record context vs. default).
- [x] `npm run build` n/a; 0 `_built/` tracked.

## Test plan
- Unit/integration: build context with an override record id -> the bundle contains that
  record; build with none -> unchanged (`uv run pytest -q -k "activity_context or
  dictation"`).

## Notes / open questions
- Reuse `ActivityRecord` straight from the repository; do not re-fetch from the browser.
- Keep the override explicit and narrow so the default daily path stays byte-identical
  (the DIR-01 invariant).
