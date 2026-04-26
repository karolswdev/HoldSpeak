# Phase 5 — Usability Powerhouse

**Last updated:** 2026-04-26 (HS-5-08 done — disabled-pipeline readiness warnings now expose an Enable pipeline action that saves through the existing Runtime settings path; full sweep 1098 passed / 13 skipped).

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
| HS-5-06 | Readiness starter actions | done | [story-06-readiness-starter-actions.md](./story-06-readiness-starter-actions.md) | [evidence-story-06.md](./evidence-story-06.md) — no-blocks readiness warning can create + dry-run the recommended starter; 2 new integration tests |
| HS-5-07 | Project KB starter action | done | [story-07-project-kb-starter-action.md](./story-07-project-kb-starter-action.md) | [evidence-story-07.md](./evidence-story-07.md) — starter Project KB endpoint + readiness/editor actions; 4 new integration tests |
| HS-5-08 | Runtime readiness action | done | [story-08-runtime-readiness-action.md](./story-08-runtime-readiness-action.md) | [evidence-story-08.md](./evidence-story-08.md) — disabled pipeline warning can enable Runtime through existing settings; 3 new integration tests |

## Where We Are

HS-5-08 closes the obvious readiness-fix loop for the dictation
cockpit. Missing blocks, missing Project KB, and disabled pipeline
warnings now have direct browser actions, while settings mutation still
flows through the existing config endpoints. The setup loop is now
browser-first across project selection, readiness, starter blocks,
starter KB, runtime enablement, and dry-run.

Next likely chunks:

1. Meeting/user action follow-through: surface action item provenance
   and review states more prominently in history/detail views.
2. Browser project switcher follow-up: optional file-picker integration
   or explicit current-cwd project display on page load.
3. Model/runtime install guidance for missing backend or model-file
   warnings.
