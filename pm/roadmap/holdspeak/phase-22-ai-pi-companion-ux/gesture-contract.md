# AI PI Gesture Contract

HS-22 keeps AI PI user-driven. Gestures can reveal context, start voice capture,
bookmark meetings, or clear stale state, but they must not answer Claude/Codex
without explicit speech from the user.

Source code contract: `aipi-lite/bridge/companion_gestures.py`.

## Physical Gestures

| Gesture | Remote simulation | Owner | Meaning |
|---|---|---|---|
| Left single tap | `left-short` | bridge | Context action: bookmark during meeting, show agent question outside meeting, otherwise show last segment. |
| Left double tap | — | bridge + firmware detector | Cycle meeting stats during meeting; no-op outside meeting. |
| Left long press | `left-long` | firmware | Existing AP-mode/provisioning behavior. |
| Right hold-to-talk | `voice-typing` | firmware capture, HoldSpeak processing | Start explicit voice capture. If an agent is waiting, the captured speech is the agent reply path; otherwise it is normal dictation. |

## State Table

| State | Left single tap | Left double tap | Right hold-to-talk | Left long press |
|---|---|---|---|---|
| `disconnected` | `last_segment` query cannot complete until link returns | no-op | normal capture cannot complete until link returns | AP mode |
| `idle_connected` | show last segment (`last_segment`) | no-op | normal dictation capture (`start`/`stop`) | AP mode |
| `meeting_recording` | bookmark meeting (`long_press`) | cycle meeting stats (`double_left_click`) | normal meeting/dictation capture (`start`/`stop`) | AP mode |
| `agent_waiting` outside meeting | show full agent question (`agent_question`) | no-op | start agent reply capture (`start`/`stop`) | AP mode |
| `agent_waiting` during meeting | bookmark meeting (`long_press`) | cycle meeting stats (`double_left_click`) | start agent reply capture (`start`/`stop`) | AP mode |
| `reply_capture` | show last segment unless meeting is active, then bookmark | no-op unless meeting is active | active capture is already owned by firmware | AP mode |
| `transcribing_rewrite_pending` | show last segment unless meeting is active, then bookmark | no-op unless meeting is active | normal capture is suppressed by HoldSpeak busy/error handling if unavailable | AP mode |
| `error_busy` | suppress | suppress | suppress | AP mode |
| `stale_cleared` | clear stale agent context | no-op | no-op; stale context is not replyable | AP mode |

## Decisions

- The primary agent-reply gesture is right hold-to-talk while
  `agent_waiting` is fresh. This reuses the existing voice-assistant
  `start`/`stop` wire path and keeps the reply explicitly user-spoken.
- Left single tap keeps meeting bookmark priority whenever a meeting is active,
  even if an agent is waiting. This preserves the shipped meeting gesture.
- Outside a meeting, left single tap upgrades from `last_segment` to
  `agent_question` only while a fresh agent is waiting.
- Stale agent context cannot be answered. Left single tap may clear it; right
  hold-to-talk is a no-op for the stale agent state.
- Left long press stays firmware-owned AP/provisioning behavior in every state.

## Follow-Up Implementation Notes

- HS-22-03 should adapt `resolve_gesture(...)` into `DeviceLeg` instead of
  duplicating the table in conditionals.
- Bridge behavior needs a fresh/stale agent signal before it can switch the
  outside-meeting left tap from `last_segment` to `agent_question`.
- Remote simulation already covers `left-short`, `left-long`, and
  `voice-typing`. A future double-tap simulation can be added if hardware
  dogfood needs it, but the current firmware-side `left_double_tap_event`
  remains the production detector.
