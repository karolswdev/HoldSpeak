# HSM-17-02 — Hooks: inject into the live Claude/Codex instances (capture)

- **Project:** holdspeak-mobile
- **Phase:** 17
- **Status:** todo
- **Depends on:** HSM-17-01 (the `AgentSession` contract — the shape the hooks must report into), the
  existing capture spine (`holdspeak/commands/agent_hook.py`, `holdspeak/agent_context/` `AgentSession` +
  `~/.config/holdspeak/agent_sessions.json`, `holdspeak/agent_device.py`).
- **Unblocks:** HSM-17-03 (nothing surfaces on the desk until live sessions actually report in).
- **Owner:** unassigned

## Problem

"We inject ourselves by running our hooks on our Claude and Codex instances." The hook **templates**
exist (`agent_hook.py` emits them) but the loop is not live: a running Claude Code / Codex CLI instance
must continuously report its state — *working*, *has a question*, *idle*, *ended* — up to the desktop so
the desk can show it. That is the capture half of agent sync.

## The design

- **The hook payload → `AgentSession` state.** Make the hooks report the fields HSM-17-01 defined:
  session id, agent kind, cwd/project, a `state`, and — critically — the **pending question** when the
  coder is blocked waiting on the human. Map the agent's own lifecycle events (prompt-needed / tool-
  permission / idle / exit) onto `working` / `waiting(question)` / `idle` / `ended`.
- **Install ergonomics.** A one-command install that wires our hooks into a user's Claude Code and Codex
  config (the `agent_hook.py` template path), idempotent and reversible. The "inject ourselves" step must
  be a single documented action, not hand-editing configs.
- **Desktop ingestion.** The hook writes through `agent_context` (`agent_sessions.json` today) and the
  desktop serves the live set via the HSM-17-01 endpoint, formatted by `agent_device.py`. Stale sessions
  (no heartbeat) decay to `idle`, dead ones to `ended` (tombstone).
- **Both agents.** Claude **and** Codex, per the owner. `SUPPORTED_AGENTS = {claude, codex}` already; the
  hook templates and the state mapping cover both.

## Scope

- **In:** the live hook payload (state + question + heartbeat) for Claude Code and Codex; the one-command
  idempotent install/uninstall; desktop ingestion + staleness decay; serving live sessions in the
  HSM-17-01 shape.
- **Out:** the desk rendering (17-03); the answer/inject (17-04+). This story ends when a question asked
  inside a live coder is observable from the HSM-17-01 endpoint.

## Acceptance criteria

- [ ] A live Claude Code session and a live Codex session, with our hooks installed, appear in the
      desktop's live-session endpoint with correct `agent`, `cwd/project`, and `state`.
- [ ] When the coder blocks on a question, the session flips to `waiting` and the **question text** is
      captured into the `AgentSession`.
- [ ] When the coder resumes / exits, the session returns to `working`/`idle` / tombstones to `ended`
      within a bounded staleness window.
- [ ] The install is one command, idempotent, reversible; documented (feeds HSM-17-07).
- [ ] Secret-safe: a captured question is filtered the same way the dictation journal filters secrets
      (reuse the existing filter), never leaking tokens/keys into the synced state.

## Test plan

- Real metal: install the hooks on the Mac, start a Claude Code session, drive it to a question
  (e.g. a tool-permission / clarification prompt), confirm the desktop endpoint shows `waiting` + the
  question; resume and confirm it clears. Repeat for Codex.
- Unit: the lifecycle-event → `state` mapping; staleness decay; the secret filter on a captured question.
