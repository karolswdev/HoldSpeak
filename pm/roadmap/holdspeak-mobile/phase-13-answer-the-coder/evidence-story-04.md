# Evidence — HSM-13-04 (Answer-the-coder gate) — CLOSED by voice

**Date:** 2026-06-20 · **Status:** done

The companion track's payoff, proven on real metal end to end: a coding agent's
question, surfaced on a physical iPad, **answered by a native voice note**, transcribed
**on-device**, and delivered into that live coder session — on an explicit send, never
autonomously. (Earlier delivery wiring + the typed-answer half are in
[`realmetal-log-gate`](./realmetal-log-gate.md); this is the voice closeout.)

## What shipped (the voice last mile)

- **A real on-device voice answer app:** `apple/App/CompanionAnswerApp.swift` —
  surfaces the waiting question (`GET /api/companion/status`), records via the Phase-2
  `AudioCaptureService`, transcribes **on-device with WhisperKit**, lets you review/
  edit, and delivers via the HSM-13-01 inject path. It drives the **real** HSM-13-02
  `VoiceNoteComposer` — capture → transcribe → review → deliver — so the owner's "never
  before an explicit send" rule holds structurally.
- **`WhisperKitTranscriber`** (in the app): the concrete `ITranscriber` the composer's
  factory builds over the captured `AudioChunk`s — converts 16 kHz PCM16 → floats, runs
  `WhisperKit(WhisperKitConfig(model: "base"))`, maps segments to `Segment`.
- **`WhisperText.clean`** (`apple/Sources/Providers/Transcription/Transcription.swift`):
  a pure, unit-tested cleaner that strips WhisperKit control tokens
  (`<|startoftranscript|>`, `<|en|>`, `<|0.00|>`, `<|endoftext|>`) so the coder gets
  clean prose. **A real-metal run caught the token leak** — see below.
- **Build pipeline:** `gen-companion-answer.rb` (Contracts+Providers+RuntimeCore + the
  WhisperKit 0.11.0 package, no LLM), `Answer-Info.plist` (mic + ATS local networking),
  `companion-answer-device.sh`.

## Tests (ran)

- Swift: `swift test` → **122 passed / 6 skipped / 0 failed** (+5 `WhisperTextTests`,
  including the exact token-leaked string a device run delivered before the fix).
- The voice answer app **builds + signs + links** for device (WhisperKit + Tokenizers +
  swift-transformers + Jinja resolved): `** BUILD SUCCEEDED **`.
- Delivery + composer host tests remain green (5 delivery, 10 composer).

## Real-metal proof (physical iPad Air M4 → on-device Whisper → live tmux coder)

Desktop on `192.168.1.28:8000` with the HSM-13-04 delivery wiring; a real Stop-hook
awaiting session at a live tmux pane (`agent-hook ingest`, the question:
*"Should I use Redis or Postgres for the cache layer, and what TTL do you want?"*).

**Run 1 (the loop, proven — and the bug it caught):** the question surfaced on the iPad;
spoken answer → on-device WhisperKit → delivered into the tmux coder pane. The content
was right but carried Whisper's control markup, exactly as a raw-segment read would:
```
<|startoftranscript|><|en|><|transcribe|><|0.00|> I want very low TTL. Thank you.<|6.08|><|endoftext|>
```
This is the value of proving on metal — a no-LLM plumbing pass would have hidden it.
Fixed with `WhisperText.clean` (unit-tested against this exact string) and redeployed.

**Run 2 (clean, on the redeployed `WhisperText.clean` build):** the owner spoke a fresh
answer; it was transcribed on-device and delivered into the tmux coder pane as **clean
prose, no control tokens**:
```
I want you to use postgres for the cash layer and the TTL is 5 minutes.
```
(WhisperKit's only slip is the homophone "cash" for "cache" — on-device recognition, not
a delivery defect.) The token-leak fix is therefore confirmed **live on real metal**, not
just at the unit level.

The gate's standard — *the agent actually receives an iPad-spoken answer* — is met, and
the delivered text is clean.

## Never autonomous

The answer is delivered only on the user's explicit **Send** (`VoiceNoteComposer.send()`
from `.review`); recording → transcription → review never auto-sends; capture +
transcription are on-device, only the resulting text leaves (honest egress badge).

## What this closes

The Track N gate's core: **answer the coder by voice from the iPad, landing in a live
coding session.** Companion-board target *selection* (HSM-13-03's `select`/`pin` across
multiple waiting sessions) remains a separate story; this gate surfaced the waiting
question and delivered to it.
