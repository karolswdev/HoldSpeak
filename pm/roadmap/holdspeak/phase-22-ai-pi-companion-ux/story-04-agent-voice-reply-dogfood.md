# HS-22-04 — Agent Voice-Reply Hardware Dogfood

- **Project:** holdspeak
- **Phase:** 22
- **Status:** done
- **Depends on:** HS-22-01, HS-22-02, HS-22-03
- **Unblocks:** HS-22-05
- **Owner:** unassigned

## Problem

The bridge can now poll companion status and show waiting-agent state, but Phase
22 is not meaningful until the physical device completes a real reply loop:
Claude/Codex asks a question, AI PI shows that attention state, the user speaks
an answer through the device, and HoldSpeak inserts the answer into the intended
agent target.

## Scope

### In

- Run a real Claude/Codex awaiting-response scenario.
- Confirm AI PI paints the waiting-agent question on the LCD middle zone.
- Use right hold-to-talk or remote `voice-typing` to initiate the reply path.
- Confirm HoldSpeak routes the spoken reply through the agent-aware dictation path.
- Record logs, device behavior, and any product gaps.

### Out

- Autonomous replies.
- New direct Claude/Codex API transport.
- Hosted orchestration.
- Cross-network device transport.

## Acceptance Criteria

- [x] A real captured Claude/Codex waiting question is visible through `/api/companion/status`.
- [x] AI PI shows the waiting agent/question without clobbering bottom activity.
- [x] User voice capture starts from the physical device or the remote hardware simulation path.
- [x] The dictated answer lands in the correct agent context.
- [x] Stale or cleared agent state no longer appears actionable on AI PI.
- [x] Evidence records commands, logs, observed LCD state, and remaining gaps.

## Test Plan

- Start `holdspeak web --no-open`.
- Run the bridge from the unified repo with the active web port.
- Trigger or capture a real agent waiting state.
- Use `scripts/aipi_bridge.sh --press voice-typing` if physical right-button
  access is inconvenient; otherwise use the physical button.
- Record `/api/companion/status`, bridge logs, and final insertion behavior.

## Notes

- The default `aipi-lite/bridge.env` currently pins `HOLDSPEAK_PORT=45965`.
  For dogfood, either update that local ignored file to the active web runtime
  port or launch the bridge with `HOLDSPEAK_PORT=<active-port>`.
- If the web runtime keeps choosing random ports, consider a small follow-up to
  make HoldSpeak web port selection configurable for device workflows.
- 2026-05-24 dogfood produced a partial pass. Claude waiting-state display,
  physical AI PI capture, audio ingress, and transcription worked. Insertion
  back into Claude was blocked because the web runtime was launched from the
  background Codex environment without GUI text injection. See
  [evidence-story-04.md](./evidence-story-04.md).
- 2026-05-24 desktop-runtime retry confirmed GUI text injection was available
  and the answer transcribed, but Claude did not receive the paste. The likely
  cause was Linux terminal paste semantics (`Ctrl+Shift+V` vs `Ctrl+V`), now
  patched for Claude/Codex/terminal agent replies. Retest is pending once AI PI
  is reachable again.
- 2026-05-24 terminal-paste retest succeeded: the answer pasted into Claude,
  but it did not submit. Agent replies now request an Enter press after
  insertion; non-agent dictation does not auto-submit.
- 2026-05-24 tmux transport retest succeeded over an SSH/tmux workflow. AI PI
  answers landed in the captured Claude tmux pane without GUI focus.
