# Evidence — HS-78-03 — Talk to the waiting coder

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-78-talk-to-the-desk`)

## What changed

- **The coder pull-out answers by voice**: a `Hold to answer` mic
  (the HS-78-02 grammar) → `speakToCoder` selects the session
  (`POST /api/coders/select`) and injects the transcript through the
  existing remote seam (`POST /api/dictation/remote`,
  `target_mode: "agent"` — the HSM-13 path, byte-identical). The state
  whispers `Sent`; the hotkey-select verb remains beside it
  (`Use the hotkey`).
- **The question rides the desk now**: `fromCoderStatus` reads
  `last_assistant_text` (the real wire key the agent-context sessions
  carry) — the audit of this story found the mapper only read keys the
  payload never emits, so the waiting coder's question NEVER showed on
  the desk. Fixed.

## Verification artifacts — THE MARQUEE, REAL

One session: a REAL waiting Claude session (seeded through the real
`ingest_agent_hook_event` path with a real JSONL transcript ending on a
question — `capture_messages` + the question heuristic exercised for
real), the REAL local Whisper behind the transcribe route, the fixture
wav as the browser microphone:

- The coder object stood on the desk; its pull-out showed **"Should I
  merge the branch or wait for review?"** (`03-coder-waiting.png`).
- Held the mic, the fixture spoke, released → the state read **Sent**
  (`03-answered-by-voice.png`) and the remote seam received the spoken
  words targeted at `"agent"` — the full pipeline ran (the intent-router
  degraded gracefully when the LAN endpoint was unreachable from the
  sandbox, and delivery still happened, exactly the designed posture).
- Zero page errors. Two seeding gotchas found and recorded: the awaiting
  flag derives from the TRANSCRIPT file (not a payload message) and only
  under `capture_messages`; the question's wire key is
  `last_assistant_text`.
- vitest 9/9; web build green. The manifest guard fired on the store's
  new call sites (regenerated, 5/5). Full suite: **3099 passed + that
  one guard, 37 skipped** — clean after the regen.

## Acceptance criteria — re-checked

- [x] Mic → transcribe → inject through the existing remote seam,
      against a real seeded waiting session.
- [x] A latent desk bug fixed en route (the question never rendered).
