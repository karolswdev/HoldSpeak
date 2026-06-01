# Phase 24 — AI PI Companion Productization

**Status:** active 2026-06-01 (opened 2026-05-26; HS-24-01, HS-24-02, and HS-24-06 closed). Remaining product stories are hardware-gated on physical AI PI access.

Phase 24 turns the working AI PI companion loop into a more operable product
surface. Phase 22 proved the physical reply loop, and Phase 23 made that loop
understandable across long prompts and multiple sessions. This phase should
make the loop easier to supervise, recover, and trust during real multi-agent
work.

## Where to look first

- `current-phase-status.md` — goal, scope, proposed stories, risks, and pickup order.
- `story-01-ai-pi-companion-surface-overview.md` — closed read-only portal surface story.
- `evidence-story-01.md` — build, test, and live runtime evidence for `/companion`.
- `story-06-companion-public-docs-and-artwork.md` — closed public docs + PixelLab artwork story.
- `evidence-story-06.md` — commit trail and image/reference verification for companion docs.
- `../phase-23-ai-pi-companion-ux-polish/final-summary.md` — Phase 23 handoff and rough edges.
- `../../../docs/AGENT_HOOK_INSTALL.md` — current hook and tmux install guidance.
- `../../../aipi-lite/` — firmware and Python bridge source.

## Phase boundaries

This phase owns companion productization around the existing local loop: web
overview, session lifecycle controls, confidence/display affordances, and
display update cadence. It does not own hosted orchestration, autonomous agent
replies, direct Claude/Codex APIs, cross-network reach, or new hardware.
