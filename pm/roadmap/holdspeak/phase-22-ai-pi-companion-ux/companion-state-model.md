# AI PI Companion State Model

HS-22 treats AI PI as a small physical companion surface, not as a generic
status mirror. The bridge resolves the current facts into a zone-aware LCD plan:
top-right link, middle attention, and bottom persistent baseline.

Source code contract: `aipi-lite/bridge/companion_state.py`.

## LCD Zones

| Zone | Owner | Lifetime | Purpose |
|---|---|---|---|
| Top-left mode | firmware | sticky | Local firmware mode such as normal/AP/provisioning. |
| Top-right link | bridge | sticky | HoldSpeak WebSocket link state: online, connecting, or offline. |
| Middle attention | bridge from HoldSpeak facts | sticky/flash/persist | Agent questions, reply target, errors, stale clear notices, transcript flashes. |
| Bottom activity | bridge from HoldSpeak status | sticky | Persistent baseline: ready, meeting recording, reply capture, or transcription. |

## State Table

| State | Owner | Trigger | Display | Clear condition |
|---|---|---|---|---|
| `disconnected` | bridge | HoldSpeak WebSocket is connecting or offline. | Top-right link icon shows offline/connecting; bottom keeps last sticky state if available. | Handshake succeeds and bridge republishes link/activity. |
| `idle_connected` | bridge | Bridge and HoldSpeak are connected with no active meeting or agent question. | Top-right online icon, bottom `Ready`, middle clear. | Meeting starts, agent waits, reply capture starts, or an error arrives. |
| `meeting_recording` | HoldSpeak | HoldSpeak emits `Recording ...` sticky status or runtime reports active meeting. | Bottom sticky recording timer; middle remains available for flashes or agent attention. | Meeting stops and HoldSpeak emits a non-recording sticky status. |
| `agent_waiting` | HoldSpeak | Captured Claude/Codex session has `awaiting_response=true` inside the freshness window. | Middle sticky agent label/question; bottom continues to show meeting or ready state. | Agent session clears, user starts reply capture, or freshness exceeds stale TTL. |
| `reply_capture` | firmware | User starts voice capture for an agent reply. | Bottom `Listening...`; middle `Replying to <agent>`. | Firmware stops capture and HoldSpeak enters transcription/rewrite pending. |
| `transcribing_rewrite_pending` | HoldSpeak | HoldSpeak is transcribing or running the dictation rewrite pipeline. | Bottom `Transcribing...`; middle keeps higher-priority attention if present. | Text insertion completes, fails, or HoldSpeak returns to ready/recording. |
| `error_busy` | bridge | HoldSpeak sends `session_busy` or another device-facing error. | Middle flash with busy/error text; link and bottom baseline remain readable. | Flash TTL expires or a newer middle-priority message replaces it. |
| `stale_cleared` | bridge | Agent question is older than the accepted freshness window. | Middle flash `Agent stale; cleared`; then middle clears. | Stale-clear flash TTL expires or a fresh agent question arrives. |

## Priority Rules

Top-right is independent and always reflects the HoldSpeak link.

Bottom is the sticky baseline, ordered:

1. `reply_capture`
2. `transcribing_rewrite_pending`
3. `meeting_recording`
4. `idle_connected`

Middle is the attention surface, ordered:

1. `error_busy`
2. `reply_capture` target
3. `stale_cleared`
4. `agent_waiting`
5. transcript/status flash
6. clear

If the link is disconnected, primary state is `disconnected` even if the bridge
still has old bottom or middle context. That prevents stale agent or meeting
state from looking actionable while the host connection is down.

## Stale Agent Handling

HoldSpeak currently reports companion readiness with a 120-second captured-agent
freshness window. The bridge mirrors that as `AGENT_STALE_AFTER_S = 120`.

An agent question at exactly 120 seconds is still fresh. Anything older is not
actionable: the middle zone must show `Agent stale; cleared` as a short flash
and the follow-up bridge story must clear or stop presenting the old question
before accepting a voice reply.

## Follow-Up Implementation Notes

- HS-22-02 should map gestures onto this state model without inventing new
  state names.
- HS-22-03 should adapt `/api/companion/status` plus existing `status` and
  `query` frames into `CompanionSignals`, then paint the returned LCD plan.
- Existing `agent_status` and `agent_question` query names are enough for the
  first agent-facing bridge work; this story does not require a new wire frame.
