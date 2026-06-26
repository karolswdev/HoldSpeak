# HSM-15-08 — The Agent Desk (your live agents + the question each is asking)

- **Project:** holdspeak-mobile
- **Phase:** 15
- **Status:** backlog
- **Depends on:** the agent-hook loop + `AgentSession` (`holdspeak/agent_context/sessions.py`),
  `GET /api/companion/status` + select/pin/dismiss (`web/routes/system.py`), the iPad `CompanionBoard`
  (HSM-13-03) + `HTTPDesktopClient.companionStatus`, the Queue HUD (Phase 15 craft).
- **Owner:** unassigned

## Grounding (2026-06-22) — the machinery already exists

The desktop already tracks live coding agents: each `AgentSession` carries `agent`, `cwd`/`repo_root`,
`tmux_pane`, `awaiting_response`, `last_assistant_text` (the question), `pinned`, and staleness; the
hook (`holdspeak agent-hook ingest`) updates it on every SessionStart/UserPromptSubmit/Stop.
`GET /api/companion/status` is the ready-made oracle (waiting sessions, `tmux_reply_available`,
`text_injection_enabled`, `blockers`). The iPad already has a `CompanionBoard` over `/api/companion/*`
and a voice-answer path (HSM-13). **So this story is not new plumbing — it is making the desk a
first-class, glanceable, premium surface** (the reactive answer path exists; the *desk* does not).

## Vision (owner)

> "If you are hooked up to HoldSpeak and running an agent who might now be waiting on a question, this
> app reacts to that… your vibe code desk… you're linked to your agents on top of our extreme
> intelligence application. Start thinking about this as a proper product."

The Agent Desk is HoldSpeak's third pillar beside dictation and meetings: a command surface for the
AI coding agents you run. Not a terminal — a **desk** that shows, at a glance, every agent you have
in flight and what it needs from you.

## The design

- **The desk surface** (iPad first-class screen + the web `/companion` portal recrafted to match): a
  card per live agent — repo/cwd, the agent (Claude/Codex), a **state chip** (working / **waiting on
  you** / idle / stale), and, when waiting, the **question** (`last_assistant_text`, tightened — no
  prose). Waiting agents sort to the top and pulse.
- **One tap to answer** — voice (the existing on-device Whisper → `/api/dictation/remote` → the
  agent's tmux pane) or type. Pin/dismiss/clear reuse the existing companion routes.
- **Signal craft** — the desk uses the same depth/glyph/motion vocabulary as the rest of the app
  (elevated cards, the waiting-state pulse, a glyph per agent), not a plain list. Premium, native.
- **Feeds the Queue HUD** — a waiting agent is a first-class HUD item (a third lane beside jobs and
  approvals), so even when you're in scribble mode mid-meeting, the pill tells you an agent is waiting
  (HSM-15-09 owns the proactive surfacing; this story owns the desk it expands into).

## Acceptance criteria

- [ ] **The desk** — a first-class iPad surface listing every live agent with repo, agent, state, and
      (when waiting) the question; waiting sorts first + pulses. Simulator-shot + LAN-proven against a
      real `/api/companion/status`.
- [ ] **Answer in one tap** — voice or type from a desk card delivers into that agent's session
      (reuses HSM-13 delivery). LAN-proven (a real spoken answer lands in a real tmux coder).
- [ ] **Manage** — pin / dismiss / clear-stale from the desk (existing routes).
- [ ] **Signal craft** — depth/motion/glyph parity with the app; no prose; the waiting question is a
      tight quote, not a paragraph.
- [ ] **HUD link** — a waiting agent shows as a HUD lane item (handoff to HSM-15-09).

## Build plan

1. Model the desk off `companionStatus()` (already on `HTTPDesktopClient`); map sessions → desk cards.
2. The iPad desk surface (Signal cards, state chips, the waiting question, sort/pulse).
3. Answer-in-one-tap (reuse the HSM-13 voice/type delivery + companion select).
4. Wire a waiting agent into the Queue HUD as a lane item.
5. Simulator shots (idle / one-waiting / several) + a LAN proof against a real awaiting agent.

## Test plan

- Host: the sessions→desk-cards mapping + waiting-sort/staleness logic unit-tested with a fake client
  (assert waiting sorts first, stale is flagged, the question is tightened).
- LAN/device: a real coder in tmux asks a question → it appears on the desk → a one-tap voice answer
  lands back in the coder (the HSM-13 loop, now driven from the desk).

## Notes

- This is the **proper-product** pillar the first phase draft under-weighted. It reuses the entire
  HSM-13 answer-the-coder spine; the new work is the **surface** + the HUD link.
- Cross-mesh: the **web `/companion` portal** must be recrafted to this same desk bar — tracked in the
  web-convergence parity map (Phase 68). The desk is a mesh-wide surface, not iPad-only.
