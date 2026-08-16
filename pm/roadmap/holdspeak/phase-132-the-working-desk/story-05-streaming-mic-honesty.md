# HS-132-05 — The streaming mic is honest

- **Project:** holdspeak
- **Phase:** 132
- **Status:** done
- **Depends on:** HS-132-04
- **Unblocks:** HS-132-14
- **Owner:** unassigned

## Problem

The browser click-to-toggle mic (every desk text field) has five verified
defects:

1. **Floor lease expires mid-capture.** The WS session claims the audio floor
   for 30 s (`holdspeak/web/routes/system/voice_support.py:75`) and nothing
   in `ws_dictation_stream` (`voice.py:386-560`) renews it; the HTTP open-mic
   leg heartbeats every 10 s (`web/src/lib/openMic.ts:85-93`). Past 30 s the
   hotkey, wake listener, or a meeting can seize the mic mid-utterance.
2. **A full Whisper pass every 600 ms, thrown away.** Each chunk is
   transcribed independently (`voice.py:468-478`) on the same
   `transcription_lock` the hotkey needs; the only client consumer of
   partials is a ref nobody sets (`MicButton.tsx:224`; `onPartial` appears
   only inside MicButton).
3. **Named refusals collapse.** The server sends `reason`,
   `failure_category`, `mic_interval: closed` (`voice.py:474-480, 527-545`);
   the client type has none of those fields
   (`web/src/lib/micStreamSession.ts:11-14`), and after an error the empty
   final overwrites the real failure with "No words were detected"
   (`MicButton.tsx:259-263`).
4. **Retained-audio recovery is dead UI.** `savePendingVoice` is only called
   from a path with no production callers; the "Captured audio is retained
   locally." copy and Retry button can never activate
   (`MicButton.tsx:96,207,295,324`).
5. **The lamp lies.** Each chunk tick suspends the AudioContext and zeroes
   the level meter (`micStreamSession.ts:75-83` → `micSession.ts:175-188`),
   so the phase lamp reads SUSPENDED ~1.6×/s during active capture.

## Scope

### In

- Floor heartbeat on the WS path (reuse the open-mic renew pattern).
- **Design beat (held owner question #2):** partials become real (progressive
  fill with cumulative context) or per-chunk transcription is deleted and the
  session pays one Whisper pass per utterance. Orchestrator default: delete.
- Client refusal type carries `reason`/`failure_category`/`mic_interval`;
  mapped to the named failure registry; an errored session never reports
  `no_speech`.
- Retained-audio recovery: persist streamed audio before the final send so
  Retry works — or remove the promise and the button.
- Capture-graph churn fixed so the lamp reads held while held.

### Out

- Whisper model or VAD changes; the desktop hold-to-talk path (healthy).

## Acceptance criteria

- [ ] A 60 s streaming dictation retains the floor throughout (test clock or
  shortened lease in test).
- [ ] Every server refusal surfaces to the user with its name; the
  empty-final path preserves the original failure.
- [ ] Per the design ruling: either partials render progressively in the
  target field, or exactly one transcription pass occurs per utterance.
- [ ] Retry-retained-audio either works on the streaming path or does not
  appear.
- [ ] The mic phase lamp never reads SUSPENDED during an active capture.

## Test plan

- vitest: micStreamSession event mapping, MicButton failure surfacing, lamp
  phase sequence.
- `HOME=$(mktemp -d) uv run pytest -q tests/ -k "voice and (floor or stream)" --tb=short` (scoped; add a lease-renewal test).
- Real-browser mic behavior rides HS-132-14's walk.
