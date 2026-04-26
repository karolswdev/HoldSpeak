# Phase 5 — Usability Powerhouse

**Last updated:** 2026-04-26 (HS-5-05 done — `/dictation` now validates project-root overrides before saving, exposes recent browser-local roots, and adds a project-context API; full sweep 1092 passed / 13 skipped).

## Goal

Turn the web-first HoldSpeak runtime into a daily-use cockpit: fewer
restarts, less YAML/source-diving, clearer setup loops, and faster
iteration from "I have an idea for a dictation workflow" to "I can
test it safely in the browser."

## Scope

- **In:**
  - Project selection / switching for dictation configuration.
  - Setup and readiness affordances that reduce dogfood friction.
  - Browser-first testing loops for voice typing and meeting workflows.
  - Small, high-leverage UI/API improvements that make the existing
    feature set easier to use repeatedly.
- **Out:**
  - New transcription engines.
  - Hosted/multi-user deployment.
  - Large frontend framework migration unless vanilla JS becomes a
    blocker for a concrete story.

## Story Status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-5-01 | Dictation project-root override | done | [story-01-project-root-override.md](./story-01-project-root-override.md) | [evidence-story-01.md](./evidence-story-01.md) — API + `/dictation` UI override; 4 new integration tests |
| HS-5-02 | Dictation readiness panel | done | [story-02-dictation-readiness.md](./story-02-dictation-readiness.md) | [evidence-story-02.md](./evidence-story-02.md) — readiness API + UI checklist; 5 new integration tests |
| HS-5-03 | Starter block templates | done | [story-03-starter-block-templates.md](./story-03-starter-block-templates.md) | [evidence-story-03.md](./evidence-story-03.md) — templates API + UI picker; 5 new integration tests |
| HS-5-04 | Template create + dry-run loop | done | [story-04-template-create-dry-run.md](./story-04-template-create-dry-run.md) | [evidence-story-04.md](./evidence-story-04.md) — one-click template create + sample dry-run; 3 new integration tests |
| HS-5-05 | Browser project switcher polish | done | [story-05-project-switcher-polish.md](./story-05-project-switcher-polish.md) | [evidence-story-05.md](./evidence-story-05.md) — project-context validation API + recent roots selector; 3 new integration tests |

## Where We Are

HS-5-05 makes project switching less brittle. The browser now validates
manual project roots before saving them, remembers recent roots locally,
and exposes a project-context API that gives the UI resolved project
identity plus expected blocks/KB paths. The setup loop is now: choose
project, inspect readiness, create a starter block, and dry-run it
without leaving the browser.

Next likely chunks:

1. Meeting/user action follow-through: surface action item provenance
   and review states more prominently in history/detail views.
2. Readiness next-action deep links that preselect starter templates or
   dry-run samples based on the warning that triggered them.
3. Browser project switcher follow-up: optional file-picker integration
   or explicit current-cwd project display on page load.
