# Phase 5 — Usability Powerhouse

**Last updated:** 2026-04-26 (HS-5-04 done — starter templates can now create a block and immediately run the sample dry-run from `/dictation`; combined API returns created block ID, sample input, trace, and final output; full sweep 1089 passed / 13 skipped).

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

## Where We Are

HS-5-04 closes the first-test loop. A user can choose a starter
template, create a duplicate-safe block in global or project scope, and
immediately see that template's sample utterance move through the
pipeline trace to final output. The readiness panel, starter picker,
project-root override, and dry-run surface now form one browser-first
setup path.

Next likely chunks:

1. Meeting/user action follow-through: surface action item provenance
   and review states more prominently in history/detail views.
2. Browser-side project switcher polish: recent project roots,
   validation feedback, and faster switching.
3. Readiness next-action deep links that preselect starter templates or
   dry-run samples based on the warning that triggered them.
