# Phase 18 — Intelligent Typing Copilot

**Status:** done (opened 2026-05-10; closed 2026-05-10). See [final-summary.md](./final-summary.md).

This phase makes HoldSpeak a local intelligent typing layer, not only a meeting-intelligence tool. The work centers on target-profile detection, Claude Code / Codex hook context, optional external-agent summarization, project-local `.hs` conventions, OpenAI-compatible rewriter runtimes, and the web interface needed to inspect and maintain those pieces.

The phase closed with evidence for every story and a broad regression baseline. Future work should read [final-summary.md](./final-summary.md) before extending intelligent typing.

## Where to look first

- `current-phase-status.md` — goal, scope, story table, risks, and pickup order.
- `story-01-agent-hooks-target-profile.md` — current in-progress story and the substrate for profile-aware typing.
- `story-06-external-agent-summarizer.md` — optional Codex / Claude CLI context summarization bridge.
- `docs/USER_GUIDE.md` — user-facing documentation that should become the canonical product walkthrough.
- `holdspeak/target_profile.py` — target-profile detection work.
- `holdspeak/agent_context.py` and `holdspeak/commands/agent_hook.py` — agent context capture surfaces.
- `holdspeak/plugins/dictation/` — dictation rewriter/runtime work.
- `web/src/pages/Dictation.astro` — web cockpit surface for dictation and agent setup.

## Phase boundaries

HS-18 does not own AIPI-Lite active-device frames, cross-network device reach, or the remaining meeting synthesizer plugins. Those remain HS-17, HS-15, and HS-16 respectively. HS-18 owns the daily typing experience: what happens after a user speaks and before text lands in the target application.
