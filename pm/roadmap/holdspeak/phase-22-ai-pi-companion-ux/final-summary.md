# Phase 22 — Final Summary

- **Phase opened:** 2026-05-24
- **Phase closed:** 2026-05-25
- **Chunks shipped:** 6

## Goal — was it met?

Original goal:

> Make AI PI feel like a real HoldSpeak companion: a small physical surface
> that shows the right local state at the right time and lets the user answer
> or act by voice without guessing what the device is doing.

**Yes, for the first real local-agent loop.** Phase 22 defined the companion
state model, documented the gesture contract, wired bridge polling/display
behavior, dogfooded physical AI PI voice replies, and replaced fragile GUI
focus assumptions with tmux-pane delivery for terminal agents.

Evidence per story:
[01](./evidence-story-01.md) ·
[02](./evidence-story-02.md) ·
[03](./evidence-story-03.md) ·
[04](./evidence-story-04.md) ·
[05](./evidence-story-05.md) ·
[06](./evidence-story-06.md).

## Exit criteria — final state

- [x] A companion state model is documented and implemented across bridge/display behavior — [evidence-story-01](./evidence-story-01.md).
- [x] The button/gesture contract is documented and covered by bridge tests — [evidence-story-02](./evidence-story-02.md).
- [x] AI PI can visibly show a waiting Claude/Codex question and clear stale state predictably — [evidence-story-03](./evidence-story-03.md).
- [x] AI PI can initiate a voice reply to a waiting agent through the shipped HoldSpeak companion path — [evidence-story-04](./evidence-story-04.md).
- [x] Live hardware dogfood records at least one real Claude/Codex answer flow — [evidence-story-05](./evidence-story-05.md).
- [x] Phase closeout records what became product-ready and what remains experimental — [evidence-story-06](./evidence-story-06.md).

## Stories shipped

| ID | Title | Commit/PR | Date |
|---|---|---|---|
| HS-22-01 | Companion state model and LCD priority contract | this working set | 2026-05-24 |
| HS-22-02 | Gesture contract for agent and meeting actions | this working set | 2026-05-24 |
| HS-22-03 | Bridge companion polling and display wiring | this working set | 2026-05-24 |
| HS-22-04 | Agent voice-reply hardware dogfood | this working set | 2026-05-24 |
| HS-22-05 | tmux agent reply transport | this working set | 2026-05-25 |
| HS-22-06 | Phase exit and product handoff | this working set | 2026-05-25 |

## Ready now

- Companion state model:
  - idle, connected, meeting, agent-waiting, reply, and error states.
- Gesture contract:
  - remote and physical intent names for agent replies, meeting cycling,
    bookmark, and stale clear behavior.
- Bridge behavior:
  - `/api/companion/status` polling, LCD priority mapping, stale clearing, and
    companion status helpers.
- Agent reply path:
  - AI PI starts device-originated voice capture for a waiting agent.
  - HoldSpeak routes the transcript through agent-aware reply handling.
  - tmux-backed sessions receive literal text plus Enter via `tmux send-keys`.
  - GUI text insertion remains the fallback.
- Installation docs:
  - `docs/AGENT_HOOK_INSTALL.md` documents hook installation and tmux reply
    delivery expectations.

## Still rough

| Topic | Current behavior | Re-targeted to |
|---|---|---|
| Long agent questions | Display path shortens text, often hiding the useful tail. | Phase 23 marquee/windowed display |
| Multiple agent sessions | Hook/runtime can know sessions, but AI PI does not make the answer target obvious enough. | Phase 23 multi-session identity |
| Session preview | No device or browser companion surface to browse active Claude/Codex sessions. | Phase 23 preview/browser UX |
| Companion status shape | Nested runtime state can show text insertion enabled while the top-level companion status reports unknown. | Phase 23 API cleanup |
| Push vs poll | Polling works for v1 and dogfood. | Phase 23 cadence decision |

## Handoff

Phase 23 should be a UX-quality phase. The core loop now works, so the next
work should help the user understand what AI PI is showing and exactly which
agent/session will receive their spoken answer.

The first Phase 23 questions:

- how long Claude/Codex prompts should be displayed, windowed, or scrolled;
- how AI PI names sessions when two Codex panes and one Claude pane are active;
- whether the device can browse/preview active sessions before answering;
- what web companion panel is needed for richer preview and debugging;
- how to make status freshness and target confidence visible without clutter.

## Final asset / test posture

- Root focused regression: `.venv/bin/python -m pytest tests/unit/test_agent_context.py tests/unit/test_tmux_transport.py tests/unit/test_web_runtime.py tests/unit/test_typer.py tests/integration/test_web_dictation_settings_api.py -q` — `57 passed in 1.23s`.
- AIPI regression: `scripts/aipi_test.sh -q` — `195 passed in 7.54s`.
- Diff hygiene: `git diff --check` — passed.
