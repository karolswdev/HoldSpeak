# Phase 7 - Local Handoff Exports

**Last updated:** 2026-04-26 (HS-7-04 done - public docs describe local handoff exports and no external sync behavior).

## Goal

Turn reviewed meeting intelligence into portable local handoff material.
Phase 6 made action items and artifacts traceable and reviewable in the
browser. Phase 7 focuses on exporting that context in useful Markdown and
JSON shapes so the user can carry meeting outcomes into docs, pull
requests, planning notes, or external task systems manually before any
automatic SaaS sync exists.

## Scope

- **In:**
  - Meeting export renderer improvements for action provenance and review state.
  - Artifact-aware Markdown/JSON exports.
  - Browser/API affordances for saved-meeting handoff exports.
  - Tests that pin exported content and privacy-preserving local behavior.
- **Out:**
  - Direct Jira, Linear, GitHub Issues, Slack, or email publishing.
  - Cloud collaboration.
  - New artifact synthesis plugins.
  - PDF/DOCX rendering.

## Story Status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-7-01 | Handoff export renderer | done | [story-01-handoff-export-renderer.md](./story-01-handoff-export-renderer.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-7-02 | Saved meeting export API | done | [story-02-saved-meeting-export-api.md](./story-02-saved-meeting-export-api.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-7-03 | Browser handoff export action | done | [story-03-browser-handoff-export-action.md](./story-03-browser-handoff-export-action.md) | [evidence-story-03.md](./evidence-story-03.md) |
| HS-7-04 | Handoff export docs | done | [story-04-handoff-export-docs.md](./story-04-handoff-export-docs.md) | [evidence-story-04.md](./evidence-story-04.md) |
| HS-7-05 | DoD sweep + phase exit | backlog | [story-05-dod.md](./story-05-dod.md) | pending |

## Where We Are

Phase 7 has three shipped handoff foundations. HS-7-01 made the shared
meeting export renderer carry the data Phase 6 made trustworthy: action
review state, source timestamps, due dates, and optional synthesized
artifacts in Markdown/JSON outputs. HS-7-02 exposed that renderer through
a local saved-meeting export API. HS-7-03 added local Markdown/JSON
download controls to the selected meeting detail view in `/history`.
HS-7-04 documented the workflow in public meeting docs and clarified that
handoff exports are local downloads, not external task-system sync.

The next story is the Phase 7 DoD sweep.

## Initial Hypothesis

The strongest value loop is:

1. Review action items and artifacts in `/history`.
2. Export one meeting as local Markdown or JSON.
3. Paste or attach that handoff into the user's chosen downstream system.
4. Keep HoldSpeak local-first, with no automatic external side effects.
