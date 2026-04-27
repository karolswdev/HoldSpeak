# Phase 6 - Action Follow-Through Cockpit

**Last updated:** 2026-04-26 (HS-6-03 done - Actions now defaults to open needs-review work with status/review filters).

## Goal

Turn meeting intelligence outputs into reviewable, traceable work. Phase
2 created multi-intent routing and artifact synthesis; Phase 4 made the
web runtime the flagship surface; Phase 5 made dictation setup usable.
Phase 6 focuses on the next daily-use gap: action items and artifacts
should be easy to inspect, verify against their source meeting context,
review, filter, and carry forward.

## Scope

- **In:**
  - Action item provenance in history/detail views.
  - Review-state controls for action items and synthesized artifacts.
  - Filters for unreviewed/open/completed action items.
  - Meeting-detail affordances that keep action items tied to transcript
    and artifact context.
  - Small API/UI improvements that make action follow-through repeatable.
- **Out:**
  - External task-system sync (Jira, Linear, GitHub Issues).
  - Cloud collaboration or multi-user assignments.
  - New LLM providers.
  - Rewriting the dashboard/history frontend stack.

## Story Status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-6-01 | Action item provenance audit | done | [story-01-action-provenance-audit.md](./story-01-action-provenance-audit.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-6-02 | Action item review controls | done | [story-02-action-review-controls.md](./story-02-action-review-controls.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-6-03 | Action item filters and open-work view | done | [story-03-action-filters.md](./story-03-action-filters.md) | [evidence-story-03.md](./evidence-story-03.md) |
| HS-6-04 | Artifact/action detail linking | backlog | [story-04-artifact-action-links.md](./story-04-artifact-action-links.md) | pending |
| HS-6-05 | DoD sweep + phase exit | backlog | [story-05-dod.md](./story-05-dod.md) | pending |

## Where We Are

Phase 6 now has three shipped follow-through loops. HS-6-01 made action
item provenance visible by carrying source timestamps through summary
APIs and history views. HS-6-02 added browser review controls in the
global Action Items tab, project action-item lists, and selected meeting
detail action items. HS-6-03 made the Actions tab default to open
needs-review work and added status/review filters plus an Open Work reset.

The next story should connect artifacts and action items more directly
inside the meeting/project history surfaces.

## Initial Hypothesis

The strongest value loop is:

1. See unreviewed action items from recent meetings.
2. Open the source meeting/artifact context.
3. Mark the action item reviewed, completed, or needing follow-up.
4. Keep the state visible in history so outstanding work is obvious.
