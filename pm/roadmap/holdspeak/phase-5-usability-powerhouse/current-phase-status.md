# Phase 5 — Usability Powerhouse

**Last updated:** 2026-04-26 (HS-5-16 DoD complete - **PHASE 5 DONE**; evidence bundle at `docs/evidence/phase-usability-powerhouse/20260426-1755/`; focused sweep 121 passed; full sweep 1107 passed / 13 skipped).

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
| HS-5-09 | Model/runtime install guidance | done | [story-09-runtime-install-guidance.md](./story-09-runtime-install-guidance.md) | [evidence-story-09.md](./evidence-story-09.md) — missing backend/model warnings now show copyable install/model guidance; 2 new integration tests |
| HS-5-10 | Current cwd project visibility | done | [story-10-cwd-project-visibility.md](./story-10-cwd-project-visibility.md) | [evidence-story-10.md](./evidence-story-10.md) — `/dictation` now shows cwd-detected project context before override; 1 new integration test |
| HS-5-11 | Doctor runtime guidance parity | done | [story-11-doctor-runtime-guidance.md](./story-11-doctor-runtime-guidance.md) | [evidence-story-11.md](./evidence-story-11.md) — doctor now reports concrete runtime install/model commands; 2 updated unit assertions |
| HS-5-12 | Runtime guidance shared source | done | [story-12-runtime-guidance-shared-source.md](./story-12-runtime-guidance-shared-source.md) | [evidence-story-12.md](./evidence-story-12.md) — readiness and doctor now reuse one runtime guidance helper; 4 new unit tests |
| HS-5-13 | Runtime guidance docs route | done | [story-13-runtime-guidance-docs-route.md](./story-13-runtime-guidance-docs-route.md) | [evidence-story-13.md](./evidence-story-13.md) — runtime guidance links now open a served local setup page; 2 new integration assertions |
| HS-5-14 | Runtime guidance copy bundle | done | [story-14-runtime-guidance-copy-bundle.md](./story-14-runtime-guidance-copy-bundle.md) | [evidence-story-14.md](./evidence-story-14.md) — multi-command runtime guidance now has a copy-all setup command; 2 new assertions |
| HS-5-15 | Runtime docs backend deep links | done | [story-15-runtime-docs-deep-links.md](./story-15-runtime-docs-deep-links.md) | [evidence-story-15.md](./evidence-story-15.md) — runtime setup docs links now jump to backend-specific anchors; 3 new assertions |
| HS-5-16 | DoD sweep + phase exit | done | [story-16-dod.md](./story-16-dod.md) | [evidence-story-16.md](./evidence-story-16.md) — phase evidence bundle; focused sweep 121 passed; full sweep 1107 passed / 13 skipped |

## Where We Are

**Phase 5 is complete.** HS-5-16 captured the phase evidence bundle at
`docs/evidence/phase-usability-powerhouse/20260426-1755/`, including a
focused Phase 5 sweep (`121 passed`) and the full non-Metal regression
(`1107 passed, 13 skipped`).

What Phase 5 shipped: the dictation cockpit now handles project
selection, cwd project visibility, readiness, starter blocks, starter
Project KB, disabled-pipeline enablement, runtime install/model
guidance, local setup docs, copy-all setup commands, and dry-run loops.
`holdspeak doctor` provides matching terminal setup guidance through the
same shared runtime guidance implementation.

Next phase selected: Phase 6 - meeting action follow-through.
