# HS-53-01 — The nudge engine + dismissal store

- **Project:** holdspeak
- **Phase:** 53
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-53-02, HS-53-03, HS-53-04, HS-53-05, HS-53-06
- **Owner:** unassigned

## Problem
The activity HoldSpeak stores is only inspectable on the `/activity` ledger. There is no
component that reads recent activity and turns it into a small, source-cited, dismissible
set of "here is what is relevant right now" nudges. That reader is the brain everything
else surfaces.

## Scope
- **In:**
  - A new module (e.g. `holdspeak/activity_nudges.py`) that computes a small set (1 to 3)
    of nudges from recent activity:
    - a **windowed summary** ("you touched N things since your last meeting"), using the
      previous `MeetingSummary.ended_at` (`db/models.py:25`) as the lower bound and a
      sensible recent-window fallback when there is no prior meeting;
    - a **per-record suggestion** ("you were looking at `github_issue owner/repo#123`")
      for the most relevant recent records.
  - Each nudge carries its **source citation** (the originating `ActivityRecord` id +
    `source_browser`/`source_profile` + entity + `last_seen_at`) so the UI can name where
    it came from and a user can verify it on `/activity`.
  - A simple, deterministic **relevance heuristic** (recency, entity type, project match)
    that decides which records become nudges and in what order. A weak-signal record does
    not become a nudge. No LLM.
  - A **dismissal store** (a small table or settings field) so a dismissed nudge stays
    dismissed across reloads.
  - **Off when activity is off**: if the activity privacy toggle is disabled (no records),
    the engine returns no nudges.
- **Out:** the API (HS-53-02); the context override (HS-53-03); the UI (HS-53-04).

## Acceptance criteria
- [x] The engine reads existing `ActivityRecord`s (no new watcher) and the meeting window;
      returns 1 to 3 nudges, each with a source citation + the originating record id.
- [x] A dismissed nudge does not return again (dismissal persisted).
- [x] With activity tracking off, the engine returns no nudges.
- [x] The relevance heuristic is deterministic and unit-tested (window boundary, ordering,
      weak-signal suppression).
- [x] `npm run build` n/a; 0 `_built/` tracked.

## Test plan
- Unit: seed activity records + a prior meeting -> a windowed nudge with a citation; a
  dismissed nudge is filtered; activity-off returns empty; the heuristic ordering
  (`uv run pytest -q -k "activity and nudge"`).

## Notes / open questions
- Keep the engine a pure reader over the repository + a dismissal store. No imports, no
  egress. The citation must be honest about its coarseness (last visit to a URL, not a
  per-session timestamp).
