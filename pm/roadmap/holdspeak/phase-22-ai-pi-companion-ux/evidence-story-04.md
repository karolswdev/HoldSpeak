# Evidence — HS-22-04 Agent Voice-Reply Hardware Dogfood

Date: 2026-05-24

## Scope Exercised

- Started HoldSpeak web locally on `127.0.0.1:36093`.
- Started the unified `aipi-lite` bridge against the plugged-in AI PI.
- Installed the Claude agent hooks and captured a real Claude waiting-response
  question.
- Used the physical AI PI voice path to answer the waiting Claude question.

## Runtime

```text
holdspeak web --no-open
http://127.0.0.1:36093

cd aipi-lite && .venv/bin/python -m bridge
connect.holdspeak.handshake.ok
connect.device.ok host=aipi-green.local
udp.allowlist ips=["192.168.1.19"]
update_link.ok
update_screen.ok msg="Ready"
subscribe.voice_assistant.ok
```

`holdspeak agent-hook latest` showed a real Claude session:

```text
agent: claude
awaiting_response: true
hook_event_name: Stop
last_assistant_text_at: 2026-05-25T03:36:16.463464Z
```

`/api/companion/status` reported:

```text
device_connected: true
agent_waiting: true
dictation_pipeline_enabled: true
ready_for_agent_reply: false
blockers: ["text_injection_status_unknown"]
```

## Observed Hardware Flow

- The AI PI displayed the Claude waiting question in the middle LCD zone.
- Voice capture started from the device at `2026-05-25T03:36:36Z`.
- The bridge received audio and forwarded frames to HoldSpeak:

```text
device.voice_assistant.start
audio.first_chunk bytes=1024 ms_after_va_start=798
audio.forwarded bytes=16384 frames=16
audio.forwarded bytes=16384 frames=16
audio.forwarded bytes=35840 frames=35
device.voice_assistant.stop cancelled=true capture_duration_ms=3894 first_audio_seen=true
```

- HoldSpeak transcribed the spoken reply as:

```text
Follow with a notion for me, brother.
```

## Gaps Found

- The reply did not land in Claude. The HoldSpeak web runtime was launched from
  the background Codex process, where GUI text injection was unavailable:

```text
pynput could not be initialized
no X server or Wayland unsupported
```

- The companion poller cleared the middle LCD line while capture started because
  it only painted waiting/stale agent states. The state model already resolved
  this as `Replying to Claude`; the poller now paints `REPLY_CAPTURE` too.
- `/api/settings` partial updates dropped persisted `device.psk` because the
  settings endpoint rebuilt `Config` without preserving the `device` block.
  The endpoint now keeps `DeviceConfig` through partial settings updates.
- HoldSpeak logged remote audio queue overflow warnings near capture stop. The
  answer still transcribed, but the overflow should remain visible in follow-up
  dogfood if transcript quality degrades.

## Second Desktop-Runtime Attempt

HoldSpeak was restarted from a desktop X11 environment on
`http://127.0.0.1:38535`; runtime status reported:

```text
global_hotkey_available: true
text_injection_enabled: true
```

The bridge connected the physical AI PI and captured a fresh Claude question:

```text
2026-05-25T04:14:43Z update_middle.ok
Claude waiting: AI PI almost work. Words show on screen. You...
```

The user answered through AI PI:

```text
2026-05-25T04:14:57Z device.voice_assistant.start
2026-05-25T04:14:57Z update_middle.ok "Replying to Claude"
2026-05-25T04:15:01Z device.voice_assistant.stop
2026-05-25T04:15:01Z ws.status.recv "What time it is?"
```

`/api/runtime/status` then reported:

```text
last_transcription: "What time it is?"
last_error: ""
text_injection_enabled: true
text_injection_error: ""
```

The text still did not appear in Claude. The most likely cause is Linux terminal
paste semantics: `TextTyper` sent generic `Ctrl+V`, but Claude Code was running
inside a terminal where paste is normally `Ctrl+Shift+V`. The runtime has been
patched so agent-targeted Claude/Codex/terminal replies use `Ctrl+Shift+V` on
Linux while generic browser/editor targets keep using `Ctrl+V`.

## Third Attempt

After reconnecting AI PI to the patched runtime on
`http://127.0.0.1:37689`, the user confirmed the answer pasted into Claude.
Bridge evidence:

```text
2026-05-25T04:27:37Z update_middle.ok "Claude waiting: Ugg. Phase 22 almost done..."
2026-05-25T04:27:50Z device.voice_assistant.start
2026-05-25T04:27:51Z update_middle.ok "Replying to Claude"
2026-05-25T04:27:54Z device.voice_assistant.stop
2026-05-25T04:27:55Z ws.status.recv "Another follow-up question?"
```

Remaining gap: HoldSpeak pasted the reply but did not submit it. Agent replies
now request `submit=True`, which makes `TextTyper` press Enter after insertion.
Normal non-agent dictation still inserts text without auto-submit.

## Final tmux Path

The GUI-focus blocker was resolved by HS-22-05's tmux transport. Claude was
launched in tmux and the hook captured:

```text
session_id: dd4e9f15-4225-4e0e-810d-ad13186a0ac9
tmux_pane: %1
tmux_session: 1
tmux_window: 0
tmux_pane_current_path: /home/karol/dev/HoldSpeak
```

AI PI replies then landed in Claude without relying on focused GUI text
injection. User confirmation: "it did work ... this even works over ssh".

## Result

Partial pass.

- Agent hook capture -> AI PI display: passed.
- Physical AI PI voice capture -> HoldSpeak audio ingress: passed.
- HoldSpeak transcription: passed.
- Insertion back into Claude: passed via tmux transport.

## Follow-Up

- Carry tmux transport into HS-22 closeout as the preferred terminal-agent
  delivery path.
- Keep GUI insertion as a fallback for non-tmux sessions.
