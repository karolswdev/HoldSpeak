# Phase 23 — AI PI Companion UX Polish

**Status:** done (opened 2026-05-25; closed 2026-05-26).

Phase 23 is the follow-up to the first working AI PI companion loop. Phase 22
proved that AI PI can notice a waiting Claude/Codex session, capture a spoken
answer, and deliver it through tmux. Phase 23 makes that loop understandable
when real work gets messy: long agent prompts, multiple sessions, stale state,
and the need to preview what is happening before speaking.

## Where to look first

- `current-phase-status.md` — goal, scope, proposed stories, risks, and pickup order.
- `interaction-model.md` — Phase 23 product thesis and device interaction model.
- `story-01-long-prompt-display.md` — closed story for long-prompt display behavior.
- `story-02-multi-session-identity.md` — closed story for agent/session identity.
- `evidence-story-02.md` — identity rules, implementation notes, and validation.
- `story-03-session-preview-list.md` — closed story for the session preview list.
- `evidence-story-03.md` — preview list contract and validation.
- `story-04-device-browse-selected-target.md` — closed story for selected target gestures.
- `evidence-story-04.md` — gesture contract, selected target rules, and validation.
- `story-05-reply-target-readiness-guard.md` — closed story for rejecting unavailable answer targets.
- `evidence-story-05.md` — readiness guard validation and live finding.
- `story-06-live-dogfood-and-closeout.md` — closed live dogfood and phase-closeout story.
- `evidence-story-06.md` — live hardware observations, including display flash-hold validation.
- `final-summary.md` — final Phase 23 outcome, rough edges, and next-phase handoff.
- `../phase-22-ai-pi-companion-ux/final-summary.md` — shipped companion loop and handoff.
- `../../../docs/AGENT_HOOK_INSTALL.md` — current hook and tmux install guidance.
- `../../../aipi-lite/` — firmware and Python bridge source.

## Phase boundaries

This phase owns the user experience around an already-working companion loop:
long text display, session identity, browsing/preview, status confidence, and
multi-session dogfood. It does not own autonomous replies, hosted agent
orchestration, cross-network transport, or a new hardware design.
