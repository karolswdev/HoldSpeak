# HS-13-07 - Meeting-context pipeline pack

- **Project:** holdspeak
- **Phase:** 13
- **Status:** backlog
- **Depends on:** HS-13-06, HS-11-04, HS-11-05
- **Unblocks:** HS-13-08 (pre-meeting briefing surface)
- **Owner:** unassigned

## Problem

A user about to start a meeting on a project would benefit
from a 1-screen briefing: "since your last meeting, here's
what changed in the repos you visited, the tickets you
touched, and the calendar events you opened." The data is all
there — it lives in `activity_records`, gh/jira annotations,
calendar candidates — but it isn't fused. The pipeline
substrate from HS-13-06 lets us write the fusion as a single
pack.

## Scope

- **In:**
  - New `holdspeak/connector_packs/meeting_context.py` —
    a pipeline pack that:
    - Declares `kind: pipeline`,
      `capabilities: ["annotations"]`,
      `consumes: [(github_cli, annotations), (jira_cli,
       annotations), (calendar_activity, candidates)]`.
    - Reads activity_records since `last_run_at` (or last
      24h, whichever is shorter) filtered by current
      project (resolved via the
      `apply_activity_project_rules` mapping).
    - Reads upstream annotations + candidates for those
      records.
    - Synthesizes one `meeting_context` annotation per
      project: a deterministic markdown summary
      ("PRs touched: 3 (#42 in flight, #44 merged); tickets:
      HS-101 in review, HS-103 backlog; upcoming calendar:
      Architecture sync at 10:00").
  - Annotations are local-only and persist to
    `activity_annotations` with `source_connector_id =
    "meeting_context"` so HS-13-05's run history + clear
    flows already cover it.
  - Default project resolution: the `holdspeak doctor` cwd
    project rule (HS-3 territory).
- **Out:**
  - LLM-generated summaries — the synthesizer is
    deterministic markdown for now (templated bullets). An
    LLM-driven version is phase 14.
  - Multi-project briefings in one annotation. One annotation
    per project, scanned per-meeting.

## Acceptance Criteria

- [ ] `meeting_context.MANIFEST.kind == "pipeline"`,
  `consumes` covers gh + jira + calendar.
- [ ] `validate_manifest` accepts the pack.
- [ ] `PipelineRunner.run("meeting_context", db)` executes
  upstream packs (with freshness), collects their output, and
  produces one `meeting_context` annotation per active
  project.
- [ ] Empty upstream → empty briefing annotation (no
  exception).
- [ ] Output annotation is mutation-safe: re-running the
  pipeline updates the existing annotation in place rather
  than appending duplicates.
- [ ] Fixture coverage under `tests/fixtures/connectors/`:
  `meeting-context-happy-path.json` +
  `meeting-context-empty-upstream.json`.
- [ ] HS-13-05 run history shows three rows per pipeline run
  (gh, jira, calendar) plus one for the pipeline itself.

## Test Plan

- Unit: deterministic markdown synthesis (input → expected
  output).
- Integration: run the pipeline against a seeded DB; assert
  one annotation per active project.
- Fixture: dry-run produces the expected
  `proposed_annotations` shape; mutation count zero.
- Fixture: re-run on the same DB produces zero new annotations
  (in-place update path).

## Notes

This is the *visible* payoff of phase 13's framework work.
HS-13-08 will surface this annotation in the pre-meeting UI;
HS-13-09 in the cross-meeting `/history` view. But the pack
stands alone — even without the UI, the briefing annotation
is queryable via the existing `/api/activity/annotations`
shape (TBD if not yet exposed; if not, expose it).
