# HS-22-05 — tmux Agent Reply Transport

- **Project:** holdspeak
- **Phase:** 22
- **Status:** done
- **Depends on:** HS-22-04
- **Unblocks:** HS-22-06
- **Owner:** unassigned

## Problem

GUI focus-based text insertion proves the AI PI agent-reply loop, but it is not
usable for real terminal workflows. Claude/Codex sessions often run inside tmux,
and the user cannot reliably keep a GUI terminal focused just so a physical
device reply lands in the right place.

## Scope

### In

- Capture `TMUX_PANE` from Claude/Codex hook execution environment.
- Persist tmux pane metadata on `AgentSession`.
- Prefer tmux delivery for device-originated agent replies when a waiting agent
  session has a captured pane.
- Send the reply text literally and submit it with Enter.
- Fall back to existing GUI text insertion when tmux delivery is unavailable.

### Out

- Remote tmux over SSH.
- Multiplexing multiple possible panes when no hook-provided pane exists.
- Terminal output scraping.
- Direct Claude/Codex API transport.

## Acceptance Criteria

- [x] Agent hook ingest records `tmux_pane` when `TMUX_PANE` is present.
- [x] Agent session JSON remains backward-compatible with older records.
- [x] Device-originated agent replies prefer `tmux send-keys` when `tmux_pane`
  is known.
- [x] tmux delivery sends literal text and Enter.
- [x] GUI paste remains the fallback for sessions without tmux metadata or when
  tmux delivery fails.
- [x] Live AI PI dogfood verifies reply delivery into a Claude/Codex tmux pane.

## Test Plan

- Unit: agent hook ingest captures and preserves tmux pane metadata.
- Unit: tmux transport invokes `tmux send-keys -l` and `Enter`.
- Unit: web runtime prefers tmux delivery over `TextTyper` for agent replies
  with a captured pane.
- Live: run Claude/Codex inside tmux, ask a waiting question, answer through AI
  PI, confirm the reply lands and submits in the original pane.
