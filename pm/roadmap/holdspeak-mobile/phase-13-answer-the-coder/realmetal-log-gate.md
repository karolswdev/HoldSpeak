# Real-metal log — HSM-13-04 (Answer-the-coder gate, interim)

> Interim progress log, not a closeout `evidence-story-04.md` — that ships when the
> gate is **done** (the iPad answers by voice).

**Date:** 2026-06-20 · **Status:** in-progress (delivery half proven on real metal;
native on-device-voice leg deferred — see "Remaining")

The companion track's payoff, proven as far as it honestly goes today: an answer that
**originates on a physical iPad** is delivered through the inject path into a **waiting
coding-agent's live tmux session**, on an explicit send, never autonomously. The one
piece not yet real is the *native voice note* itself (on-device Whisper) — the iPad
sent typed text, not a spoken note.

## What shipped (this story)

- **Real delivery wiring (the keystone HSM-13-01 deferred):**
  `WebRuntime._deliver_remote_dictation` (`holdspeak/runtime/dictation_capture.py`)
  delivers a companion answer into the waiting coder using the **exact** path local
  dictation uses — `_try_tmux_agent_reply` (→ `tmux send-keys`) with a `typer`
  fallback. Deliver-only (the `/api/dictation/remote` route already ran the rich
  pipeline — no double-processing). **Raises** when undeliverable, so the client sees
  an honest failure rather than a false ack. Wired through
  `WebRuntimeCallbacks.on_remote_dictation` → `WebContext.on_remote_dictation`.
- **iPad answer affordance:** `CompanionProbeApp` grew an "Answer the coder" card —
  type a reply, deliver it via `IDesktopClient.sendRemoteDictation`. An explicit Send
  button is the real affordance; an `HS_ANSWER` env path auto-delivers on launch so
  the device-origin proof is captureable hands-off.

## Tests (ran)

- Python: `uv run pytest tests/unit/test_remote_dictation_delivery.py` → **5 passed**
  (tmux delivery; typer fallback when no pane; types-into-focused when nobody waiting,
  no auto-submit; raises when undeliverable; empty text rejected). Broader sweep
  `-k "dictation or remote or web_runtime or web_server or companion"` → **315 passed**.
- Swift: the extended `CompanionProbe` harness builds + signs for the device
  (`** BUILD SUCCEEDED **`); the package suite is unchanged (`swift test`
  117/6-skip/0-fail).

## Real-metal proof (physical iPad Air M4 → desktop → live tmux coder)

Desktop: `HOLDSPEAK_WEB_HOST=0.0.0.0 holdspeak web` on `192.168.1.28`, running the new
delivery wiring. A **real** awaiting agent session was created via the actual Stop-hook
ingestion (`holdspeak agent-hook ingest --agent claude --capture-messages`) with an
assistant message that reads as a question — `/api/companion/status` then reported
`agent_waiting: true`, `tmux_reply_available: true`, `target_confidence: high`, pointing
at a live tmux pane (`%0`, a session running `cat`).

Control (curl as the client):
```
POST /api/dictation/remote {"text":"Use Redis for the cache layer, with a 24h TTL."}
  -> {"success":true,"final_text":"…","delivered":true}
tmux capture-pane:  Use Redis for the cache layer, with a 24h TTL.   # landed in the coder
```

Treatment (the iPad as the origin):
```
iPad launches the CompanionProbe (auto-connects to 192.168.1.28:8000), delivers
  HS_ANSWER = "From the iPad: use Redis for the cache, 24h TTL."
tmux capture-pane:  From the iPad: use Redis for the cache, 24h TTL.  # landed in the coder
```

The answer originated on the device and landed in the waiting agent's tmux session,
on an explicit (env-armed) send. (The iPad re-locks between runs; the DDI won't mount
on a locked device, so a retry-until-unlock loop launched it on unlock — same standing
device gotcha.)

## Never autonomous

Delivery fires only on the client's POST; `_deliver_remote_dictation` raises rather
than inventing a target; the production composer (`VoiceNoteComposer.send()`, HSM-13-02)
delivers only from `.review` on an explicit send. No autonomous path exists or was
exercised.

## Remaining (why this story is in-progress, not done)

- **Native on-device voice note** — the iPad sent typed text, not a spoken note.
  Closing this needs on-device Whisper capture wired + proven (a pending Phase-3 device
  gate); the `VoiceNoteComposer` seam is ready for it. **This is the gate's last mile.**
- **Companion board surfacing (HSM-13-03)** — the agent's question shown on the iPad
  with explicit target selection before send.
- **Live rich-pipeline transform in delivery** — the route runs the pipeline (proven
  in HSM-13-01); a delivery demo with a configured correction/block applied is still
  to capture.

The delivery engine and the device→coder loop are real and proven; the gate closes
when the iPad answers **by voice**.
