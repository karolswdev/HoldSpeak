# Phase 7 - Local Handoff Exports

**Last updated:** 2026-04-26 (HS-7-01 done - shared handoff renderer now includes action provenance/review state and optional synthesized artifacts).

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
| HS-7-02 | Saved meeting export API | backlog | [story-02-saved-meeting-export-api.md](./story-02-saved-meeting-export-api.md) | pending |
| HS-7-03 | Browser handoff export action | backlog | [story-03-browser-handoff-export-action.md](./story-03-browser-handoff-export-action.md) | pending |
| HS-7-04 | Handoff export docs | backlog | [story-04-handoff-export-docs.md](./story-04-handoff-export-docs.md) | pending |
| HS-7-05 | DoD sweep + phase exit | backlog | [story-05-dod.md](./story-05-dod.md) | pending |

## Where We Are

Phase 7 is open with its first shipped foundation story. HS-7-01 made
the shared meeting export renderer carry the data Phase 6 made
trustworthy: action review state, source timestamps, due dates, and
optional synthesized artifacts in Markdown/JSON outputs.

The next story should expose this renderer through a saved-meeting local
API so browser handoff export controls can use the same code path.

## Initial Hypothesis

The strongest value loop is:

1. Review action items and artifacts in `/history`.
2. Export one meeting as local Markdown or JSON.
3. Paste or attach that handoff into the user's chosen downstream system.
4. Keep HoldSpeak local-first, with no automatic external side effects.
