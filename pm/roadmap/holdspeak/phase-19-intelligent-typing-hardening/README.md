# Phase 19 — Intelligent Typing Daily-Use Hardening

**Status:** done (opened 2026-05-10; closed 2026-05-24).

Phase 19 turns the Phase 18 intelligent-typing substrate into a daily-use product loop. The focus is not adding broad new knobs; it is making project-aware dictation dependable, inspectable, and useful during real Codex/Claude/browser/editor work.

## Where to look first

- `current-phase-status.md` — goal, scope, story table, risks, and pickup order.
- `final-summary.md` — shipped scope, final validation, and handoff.
- `story-05-endpoint-dogfood-and-exit.md` — closed real endpoint dogfood and phase exit.
- `story-04-target-profile-override.md` — closed target profile override and refinement.
- `story-03-latency-fallback-telemetry.md` — closed latency and fallback visibility in readiness/dry-run.
- `story-02-web-suggestion-review.md` — closed web review/apply/dismiss flow for suggested `.hs/.../*.md` updates.
- `pm/roadmap/holdspeak/phase-18-intelligent-typing-copilot/final-summary.md` — handoff from the previous phase.
- `holdspeak/project_doc_suggestions.py` — project documentation suggestion contract.
- `holdspeak/dictation_telemetry.py` — readiness/dry-run telemetry normalization.
- `holdspeak/target_profile.py` — target profile detection and manual override contract.
- `holdspeak/plugins/dictation/builtin/project_rewriter.py` — injection point for coding-agent dictation.
- `holdspeak/web_server.py` — review/apply/dismiss API for suggested project documentation updates.

## Phase boundaries

HS-19 owns intelligent-typing hardening: documentation suggestions, telemetry, target-profile refinement, real endpoint dogfooding, and safe user-reviewed project memory workflows. It does not own AIPI-Lite device reach or meeting-side synthesizer work.
