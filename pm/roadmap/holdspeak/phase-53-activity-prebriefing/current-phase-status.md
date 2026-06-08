# Phase 53 — Activity Pre-Briefing

**Status:** SCAFFOLDED (0/6). Opened 2026-06-08 on user direction, right after Phase 52
closed + merged (PR #39). From the [project backlog](../BACKLOG.md): candidate **F**
(local activity as pre-briefing fuel), picked by the user as the next phase.

**Last updated:** 2026-06-08 (phase scaffolded: AGENT-BRIEF + this status doc + 6 story
files written; the activity layer mapped + seams verified against the live tree. No story
started yet.)

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
| HS-53-01 | The nudge engine + dismissal store | not started | none |
| HS-53-02 | The nudges API | not started | HS-53-01 |
| HS-53-03 | Dictate with this as context | not started | HS-53-01 |
| HS-53-04 | The nudge UI (dictation surface) | not started | HS-53-02, HS-53-03 |
| HS-53-05 | Docs: the pre-briefing guide | not started | HS-53-04 |
| HS-53-06 | Closeout: dogfood + final-summary + PR | not started | HS-53-01..05 |

## Where we are

Scaffolded on 2026-06-08, on the `phase-53-activity-prebriefing` branch. Nothing started.
Start with HS-53-01 (the engine is the brain everything surfaces; build it read-only,
source-cited, gated by the activity toggle, with a simple honest relevance heuristic,
fully unit-tested). Read [`AGENT-BRIEF.md`](./AGENT-BRIEF.md) first.

## Open decisions (defaults chosen; flag to change)

- **Relevance is a deterministic heuristic** (recency + entity type + project match), not
  an LLM score. Quiet beats noisy: a weak-signal nudge does not appear.
- **Dismissal persists** in a small store (table or settings field), per record/nudge.
- **The primary surface is the dictation cockpit**; the home briefing is an optional
  second surface in HS-53-04.
- **Nudge cap 1 to 3** so the surface never becomes a feed.
