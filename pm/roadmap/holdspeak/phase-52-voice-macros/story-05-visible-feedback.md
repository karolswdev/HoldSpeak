# HS-52-05 — Visible feedback: matched macro as runtime activity

- **Project:** holdspeak
- **Phase:** 52
- **Status:** not started
- **Depends on:** HS-52-03
- **Unblocks:** HS-52-07
- **Owner:** unassigned

## Problem
A deterministic command should be visibly deterministic. When a macro fires, the user
should see that it matched (which command, what it did), so the layer feels predictable
rather than magic. The runtime already has an activity broadcast for exactly this.

## Scope
- **In:**
  - When the matcher fires, emit a runtime activity through the existing channel
    (`web_runtime.py:331-368` `_set_runtime_activity` / `_broadcast_runtime_activity`;
    contract `runtime_activity.py:79-156`), e.g. a state/label like
    "command: new paragraph". No new websocket message type.
  - Off-path when macros are off or no command matched (no spurious activity).
  - Focus-safe: this is an ambient signal, it never steals focus or blocks typing.
- **Out:** new presence UI (reuse what exists); the editor (HS-52-04).

## Acceptance criteria
- [ ] A matched macro surfaces as a runtime activity through the existing broadcast with
      a clear, human label naming the command.
- [ ] No activity emitted when macros are off or nothing matched.
- [ ] Focus-safe and side-channel: emitting the signal never changes the typed output.
- [ ] A test asserts the activity is emitted on a match and not otherwise.
- [ ] `npm run build` only if a presence view changed; 0 `_built/` tracked.

## Test plan
- Unit/integration: assert the activity broadcast on a matched command and its absence
  on no-match / macros-off (`uv run pytest -q -k "macro or runtime_activity or
  presence"`).

## Notes / open questions
- Keep the label product-facing and plain ("command: send it"), not an internal id.
- Reuse the existing activity states where they fit; add a minimal new one only if none
  reads right.
