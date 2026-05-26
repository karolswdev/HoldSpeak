# HS-23-05 — Reply Target Readiness Guard

- **Status:** done
**Opened:** 2026-05-26.
**Closed:** 2026-05-26.
**Owner:** Codex.

## Problem

Live dogfood showed a confusing state: when Codex/no-tmux was selected and GUI
text injection was unavailable, right-button voice capture still started and AI
PI displayed `Replying to Codex | holdspeak | no tmux`. The transcript was not
delivered, but the display implied a replyable target.

That violates the Phase 23 confidence rule: low-confidence or unavailable
targets must not look safe to answer.

## Outcome

HoldSpeak now rejects device voice capture for an awaiting agent session when
that selected session has no tmux pane and GUI text injection is unavailable.
The device gets a short `No reply target` status instead of entering a reply
capture flow.

## Scope

### In

- Add a runtime deliverability guard before device voice capture starts.
- Keep tmux targets replyable even when GUI text injection is unavailable.
- Keep normal dictation behavior unchanged when no agent target is waiting.
- Cover the no-tmux/no-TextTyper rejection with a unit test.

### Out

- Firmware-side disabled-button UX.
- Full web companion panel controls.
- Final voice reply dogfood into Claude; that remains HS-23-06.

## Acceptance Criteria

- [x] Selected tmux targets remain replyable.
- [x] Selected no-tmux targets are rejected when text injection is unavailable.
- [x] The runtime records a clear last error and sends a device-facing status.
- [x] Tests cover the rejection path.
- [x] Evidence records the live finding that caused the guard.

## Closeout

Implemented 2026-05-26. See [evidence-story-05.md](./evidence-story-05.md).
