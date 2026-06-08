# Phase 53 — Activity Pre-Briefing

**Status:** CLOSED (7/7). Opened and closed 2026-06-08 on user direction, right after
Phase 52 closed + merged (PR #39). From the [project backlog](../BACKLOG.md): candidate
**F** (local activity as pre-briefing fuel), picked by the user as the next phase. See
[`final-summary.md`](./final-summary.md).

**Last updated:** 2026-06-08 (HS-53-07 done: **closed the loop for real.** Chasing a
real-metal proof exposed that "Dictate with this" did not actually feed the model — the
live dictation path never read the pin, and the rewriter never consumed activity records.
Fixed both ends: a process-local one-shot selection pin (`dictation_selection.py`) set by
`POST /api/activity/nudges/select` and consumed by `run_dictation_pipeline`, which now
passes `selected_record_id` to `build_activity_context`; the project-rewriter names the
selected record in both the draft + refine prompts. Proven on the `.43` Qwen3.5-9B-Q6
endpoint: the same generic dictation, run with vs. without a selected `github_issue`,
yields a control task grounded in the generic ledger context vs. a treatment task
*"Implement the `--since` flag … as requested in HoldSpeak#412"* — the selection
demonstrably changes the model output (`dogfood-real-llm-transcript.txt`, RESULT: PASS).
Byte-identical default when no pin. +17 tests; full suite 2540 passed; `npm run build`
clean. **HS-53-05 (prior):** the pre-briefing user guide.
`docs/ACTIVITY_PREBRIEFING.md` is a short product-tense guide naming what the cards
are, the local + source-cited + dismissible + never-acts contract, the
dictate-with-this action, the deterministic relevance rule, and the activity tracking
toggle gate; linked from `docs/README.md` under the Dictate journey. The
roadmap-vocab guard scans the new doc and is happy; no em/en dashes; the humanizer
pass rewrote the two inline-header bullet lists (pattern #16) into flowing prose +
plain bullets. Full suite green at 2523 passed.) **HS-53-04 (prior, 2026-06-08):** the nudge UI on the dictation surface. A
`role="region"` "Pre-briefing" block above the cockpit tabs hosts JS-rendered
`role="note"` cards with an accented glyph, the title/summary, and a citation line that
names the entity (accent-colored) + browser/profile + last-seen date. Each record card
offers **Dictate with this** + **Dismiss**; the windowed-summary card offers Dismiss
only. **Dictate with this** sets a localStorage pin and renders a visible confirmation
banner — *"Your next dictation will include &lt;entity&gt;"* with a **Clear**. The shell
is hidden until `/api/activity/nudges` returns at least one nudge AND
`activity_enabled !== false`. Three PNGs committed: `nudges-populated.png`,
`nudges-pinned.png`, `nudges-off.png`. Layout bug from the first grid pass caught and
fixed by swapping to flexbox. Page-content lock test added. `npm run build` clean; 0
`_built/` tracked. Full suite at 2523 passed.)

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
| HS-53-02 | The nudges API | done | HS-53-01 |
| HS-53-03 | Dictate with this as context | done | HS-53-01 |
| HS-53-04 | The nudge UI (dictation surface) | done | HS-53-02, HS-53-03 |
| HS-53-05 | Docs: the pre-briefing guide | done | HS-53-04 |
| HS-53-07 | Close the loop: selection feeds the model (real metal) | done | HS-53-03, HS-53-04 |
| HS-53-06 | Closeout: dogfood + final-summary + PR | done | HS-53-01..05, HS-53-07 |

## Where we are

HS-53-01 → HS-53-05 + **HS-53-07** shipped on 2026-06-08. The engine + HTTP surface +
dictation-context override + UI card stack + user guide are in place, and the loop is now
**closed for real**: "Dictate with this" parks a server-side selection, the live dictation
runner consumes it, and the project-rewriter grounds the rewrite in the selected record —
proven on the `.43` Qwen3.5-9B-Q6 endpoint (treatment references the issue, control does
not). Full suite at **2540 passed, 17 skipped**; `npm run build` clean; doc guards green.

Two dogfoods green: `dogfood.py` (the engine math, no LLM) and `dogfood_real_llm.py`
(the closed loop on real metal).

Next is **HS-53-06 — closeout**: final-summary, phase CLOSED, README + BACKLOG candidate
F flipped to shipped, PR to `main` merged on green.

## Open decisions (defaults chosen; flag to change)

- **Relevance is a deterministic heuristic** (recency + entity type + project match), not
  an LLM score. Quiet beats noisy: a weak-signal nudge does not appear.
- **Dismissal persists** in a small store (table or settings field), per record/nudge.
- **The primary surface is the dictation cockpit**; the home briefing is an optional
  second surface in HS-53-04.
- **Nudge cap 1 to 3** so the surface never becomes a feed.
