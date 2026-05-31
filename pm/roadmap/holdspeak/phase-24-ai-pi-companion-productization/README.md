# Phase 24 — AI PI Companion Productization

**Status:** paused 2026-05-31 (opened 2026-05-26; HS-24-01 closed, HS-24-02 next). Paused to prioritize Phase 25 (Trust & Hardening); resume after Phase 25 closes.

Phase 24 turns the working AI PI companion loop into a more operable product
surface. Phase 22 proved the physical reply loop, and Phase 23 made that loop
understandable across long prompts and multiple sessions. This phase should
make the loop easier to supervise, recover, and trust during real multi-agent
work.

## Where to look first

- `current-phase-status.md` — goal, scope, proposed stories, risks, and pickup order.
- `story-01-ai-pi-companion-surface-overview.md` — closed read-only portal surface story.
- `evidence-story-01.md` — build, test, and live runtime evidence for `/companion`.
- `../phase-23-ai-pi-companion-ux-polish/final-summary.md` — Phase 23 handoff and rough edges.
- `../../../docs/AGENT_HOOK_INSTALL.md` — current hook and tmux install guidance.
- `../../../aipi-lite/` — firmware and Python bridge source.

## Phase boundaries

This phase owns companion productization around the existing local loop: web
overview, session lifecycle controls, confidence/display affordances, and
display update cadence. It does not own hosted orchestration, autonomous agent
replies, direct Claude/Codex APIs, cross-network reach, or new hardware.
