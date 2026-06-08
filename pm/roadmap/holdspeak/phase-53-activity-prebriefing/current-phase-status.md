# Phase 53 — Activity Pre-Briefing

**Status:** IN PROGRESS (1/6). Opened 2026-06-08 on user direction, right after Phase 52
closed + merged (PR #39). From the [project backlog](../BACKLOG.md): candidate **F**
(local activity as pre-briefing fuel), picked by the user as the next phase.

**Last updated:** 2026-06-08 (HS-53-01 done: the nudge engine + dismissal store; pure
reader over the existing ledger + meeting window, source-cited, deterministic heuristic,
off-when-activity-off, dismissals persisted in a new tiny table; 10 unit tests; full
suite green at 2509 passed.)

## The thesis — why this phase

HoldSpeak already watches local activity and stores source-cited records, but they live
on the `/activity` ledger you go and inspect. The value is bringing the relevant bit to
you when it helps. Grounded in the live tree:

- **The records are already source-cited and windowable.** `ActivityRecord`
  (`db/models.py:207`) carries `source_browser` / `source_profile` (the citation),
  `last_seen_at` (the window key), and `entity_type` / `entity_id` (e.g. `github_issue`
  + `owner/repo#123`). `MeetingSummary` (`:25`) carries `started_at`/`ended_at`, so
  "since last meeting" is computable.
- **The dictation-context path already exists.** `ActivityContextProvider`
  (`activity_context.py:45`) injects activity into the dictation pipeline; "dictate with
  this as context" extends it with a selected record.
- **There is a proven dismissible-nudge UI** to clone: `#kn-nudge`
  (`dictation.astro:42`), a `role="note"` card that never steals focus.

So: a small reader that computes source-cited, dismissible nudges from the activity that
already exists, surfaced quietly on the daily surfaces, with one action that feeds a
record into dictation.

## Goal

Surface local activity as concrete, source-cited, dismissible pre-briefing nudges on the
daily surfaces ("what you touched since last meeting"; "dictate a reply with this issue
as context"), gated by the existing activity privacy toggle, read-only (never acts on its
own), local. No change to meeting capture, intel, plugins, or synthesis behaviour.

## Scope

- **In:** the nudge engine + dismissal store (HS-53-01); the nudges API (HS-53-02);
  dictate-with-this-as-context (HS-53-03); the nudge UI on the dictation surface
  (HS-53-04); a user guide (HS-53-05); closeout (HS-53-06).
- **Out:** a second activity watcher (read the records that exist); a new always-on
  surface (nudges are gated by the activity toggle); LLM-scored relevance (use a simple
  honest heuristic); auto-acting on a nudge (it only ever offers); any
  meeting/intel/plugin/synthesis change.

## Exit criteria (evidence required)

- A nudge engine computes 1 to 3 source-cited, windowed nudges from recent activity, each
  carrying its `ActivityRecord` citation; a dismissal store keeps a dismissed nudge gone;
  off when activity is off; unit-tested. (HS-53-01)
- `GET /api/activity/nudges` + `POST /api/activity/nudges/{id}/dismiss`, empty when
  activity is off; tested. (HS-53-02)
- A selected activity record is injected into the dictation pipeline as context without
  changing the default; tested. (HS-53-03)
- A dismissible, source-cited nudge card on the dictation surface with "Dictate with this"
  + "Dismiss"; quiet, focus-safe; `npm run build` clean; screenshot evidence. (HS-53-04)
- A product-tense user guide that passes the Phase-51 guard; `humanizer` run; linked in
  the index. (HS-53-05)
- A dogfood proving the engine end to end; full suite green; `final-summary.md`; phase
  CLOSED; PR merged; BACKLOG candidate F flipped to shipped. (HS-53-06)

## Invariants

- **Read-only and consenting.** A nudge surfaces and offers; only what the user clicks
  fires.
- **Gated by the activity toggle.** Activity off -> no records -> no nudges.
- **Source-cited, always.** Every nudge names its browser/profile, entity, and when.
- **Dismissible + quiet + focus-safe.** A `role="note"` card; dismissal persists.
- **Local-only.** Nothing egresses.

## Stories

| Story | Title | Status | Depends on |
|---|---|---|---|
| HS-53-01 | The nudge engine + dismissal store | done | none |
| HS-53-02 | The nudges API | not started | HS-53-01 |
| HS-53-03 | Dictate with this as context | not started | HS-53-01 |
| HS-53-04 | The nudge UI (dictation surface) | not started | HS-53-02, HS-53-03 |
| HS-53-05 | Docs: the pre-briefing guide | not started | HS-53-04 |
| HS-53-06 | Closeout: dogfood + final-summary + PR | not started | HS-53-01..05 |

## Where we are

HS-53-01 shipped on 2026-06-08. The engine (`holdspeak/activity_nudges.py`) is a pure
reader over the existing `ActivityRepository` + the meeting window: it returns 1–3
source-cited `Nudge`s (a windowed summary + per-record suggestions), filters by a
persisted dismissal store (new `activity_nudge_dismissals` table), uses a deterministic
relevance heuristic (recency bucket + entity-type bonus + project match), and returns
`[]` when the activity privacy toggle is off. 10 focused unit tests; full suite at
**2509 passed, 17 skipped**. The schema snapshot is regenerated and green.

Next is **HS-53-02 — the nudges API**: `GET /api/activity/nudges` (compute + drop
dismissed + return top N with citations) and `POST /api/activity/nudges/{id}/dismiss`.
The engine's `Nudge.to_dict()` is already JSON-safe; the API is a thin route over it.

## Open decisions (defaults chosen; flag to change)

- **Relevance is a deterministic heuristic** (recency + entity type + project match), not
  an LLM score. Quiet beats noisy: a weak-signal nudge does not appear.
- **Dismissal persists** in a small store (table or settings field), per record/nudge.
- **The primary surface is the dictation cockpit**; the home briefing is an optional
  second surface in HS-53-04.
- **Nudge cap 1 to 3** so the surface never becomes a feed.
