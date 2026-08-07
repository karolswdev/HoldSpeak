# HS-118-08 — Browser mic pipeline

- **Project:** holdspeak
- **Phase:** 118
- **Status:** done
- **Depends on:** --
- **Unblocks:** --
- **Owner:** unassigned

## The thesis (the bar)

HoldSpeak has two mic paths. The desktop hotkey path
(press-key → sounddevice → Whisper → full dictation pipeline:
corrections, learning loop, target detection, intent routing →
polished text lands in the active app) is the premium experience.
The browser mic path (MicButton → AudioWorklet → WAV →
`/api/dictation/transcribe` → raw Whisper text → callback) returns
unprocessed transcription. Same user, same voice, two quality tiers.

The browser is a first-class surface. When the user clicks a mic icon
in the web UI, they're sitting at their computer, in front of the
browser, using HoldSpeak. Their speech deserves the same pipeline —
corrections, the learning loop, intent routing — that the hotkey path
provides. The source is different (browser MediaStream vs system
sounddevice); everything downstream should be identical.

When this ships, `POST /api/dictation/transcribe` accepts an optional
`pipeline: true` parameter. When set, the audio passes through
Whisper AND the full dictation pipeline before returning. The
MicButton sends `pipeline: true` by default. Every speak-to-fill
mic in the web UI — inlet, AskPanel, note editor, any future input —
gets the full experience.

**Articles served:** IV (voice as input — every text input can be
spoken into; the quality should not depend on the input method),
VI (honest by construction — two quality tiers for the same user is
a hidden asymmetry), XI (kernel admission — invoking a model for
pipeline processing is a consequential operation; the browser
transcription request enters the kernel with a terminal receipt),
III (honest egress — if the pipeline uses a non-local inference
target, the egress boundary must be reported; the MicButton shows
an egress badge when applicable).

## The two paths today

```
Desktop hotkey path:
  sounddevice → Whisper → dictation_runner.py
    → target detection
    → activity context
    → correction store
    → pipeline.run(Utterance)
    → journaling
    → polished text → pyperclip → desktop paste

Browser mic path:
  AudioWorklet → WAV → POST /api/dictation/transcribe
    → Whisper → raw text
    → returned to MicButton callback
```

The dictation runner processes the raw transcript through a pipeline
of stages that apply learned corrections, detect the active target
(editor, terminal, browser), and route by intent. The browser path
skips all of this.

## Deliverables

1. **Extend `/api/dictation/transcribe`.** Add an optional body
   parameter `pipeline: bool = False`. When `True`:

   a. Transcribe the audio via Whisper (existing path).
   b. Run the raw transcript through the dictation pipeline:
      ```python
      from holdspeak.dictation_runner import process_transcript

      corrected = await process_transcript(
          raw_text=raw,
          source="browser",
          context=request_context,
      )
      ```
   c. Return `{"success": true, "text": corrected, "raw": raw}`.
      The `raw` field lets the caller see both the original
      transcription and the pipeline-processed version.

   When `pipeline` is `False` (default), behavior is unchanged —
   backward compatible.

   **Intent routing scope.** The browser pipeline applies
   corrections and learning. It does NOT apply desktop intent
   routing (which editor/terminal/app to target) — the browser IS
   the target. If the dictation pipeline has intent-routing stages
   beyond target detection, those stages return their output as
   structured metadata alongside the corrected text. The MicButton
   receives text only; intent proposals are handled by the existing
   voice grammar system on the client side, not by the server
   pipeline.

   **Kernel admission.** When `pipeline=true`, the endpoint admits
   the transcription + correction operation through the kernel (the
   Whisper and correction models are consequential inference). The
   response includes the egress boundary of the inference target
   used. The MicButton renders an egress badge if the boundary is
   non-local.

2. **Factor out `process_transcript`.** The dictation pipeline today
   lives inside `dictation_runner.py` as part of the hotkey flow.
   Extract the transcript-processing stages (corrections, learning
   loop, journaling) into a standalone function that both the hotkey
   path and the browser path can call. The hotkey path retains its
   target detection and desktop paste stages; the browser path skips
   those (the browser is the target, and text insertion is handled
   by the MicButton callback).

   The factored function signature:
   ```python
   async def process_transcript(
       raw_text: str,
       source: str,           # "hotkey" | "browser"
       context: dict | None,  # optional context (active surface, etc.)
   ) -> str:
   ```

3. **MicButton: send `pipeline: true` by default.** Update
   `speakToFill.ts::transcribeWav()` to include
   `pipeline: true` in the request. The MicButton callback receives
   the pipeline-processed text.

   If the pipeline returns both `text` (processed) and `raw`, the
   MicButton uses `text`. The `raw` field is available for debug
   surfaces (e.g. the RAW fold) but is not shown to the user by
   default.

4. **Learning loop integration.** When the browser pipeline
   processes a transcript, corrections and adaptations are journaled
   the same way as hotkey transcriptions. The user's corrections in
   one mode benefit the other. The learning store is shared — no
   per-source silos.

5. **Source tagging in journal.** Every journal entry records
   `source: "browser"` or `source: "hotkey"` so the learning loop
   can distinguish if needed. The correction store doesn't
   discriminate by source — all corrections apply universally.

6. **Mic authority.** Only one mic can own the floor at a time
   (Article IV — visible single-mic authority). The existing floor
   arbitration (`audioFloor.ts`) already prevents simultaneous
   captures. The browser mic claims the floor via
   `claimAudioFloor()` in `beginHold()`. The hotkey mic checks
   `holdOwnsFloor()` before starting. Verify this contract with an
   automated contention test (see test plan).

7. **Hotkey parity regression.** Factoring `process_transcript` out
   of `dictation_runner.py` must not change hotkey behavior. Add
   parity tests that run representative transcripts through both the
   pre-factored and post-factored hotkey path and assert identical
   output.

## What NOT to do

- Do NOT add target detection to the browser path. The browser IS
  the target. Desktop presence detection (which app has focus) is
  irrelevant — the user is in the web UI.
- Do NOT add desktop paste to the browser path. The MicButton
  callback inserts text into the field directly.
- Do NOT make `pipeline: true` a user-facing toggle. It's always on
  for browser mic. The user doesn't choose quality tiers.
- Do NOT break the existing hotkey path. It continues to use
  sounddevice → dictation_runner.py unchanged. The factored
  `process_transcript` is an extraction, not a rewrite.

## Test plan

- `uv run pytest -q tests/ -k dictation` — existing tests pass.
- New test: `POST /api/dictation/transcribe` with `pipeline=true`
  → response contains both `text` (corrected) and `raw` (original).
- New test: `POST /api/dictation/transcribe` with `pipeline=false`
  or absent → response contains only `text` (raw Whisper), backward
  compatible.
- New test: browser-sourced transcript is journaled with
  `source: "browser"`.
- New test: correction learned from a hotkey session applies to a
  browser session and vice versa.
- New test: `process_transcript` with `source="browser"` skips
  target detection and desktop paste stages.
- New test: mic floor contention — browser mic active, hotkey
  capture attempted → hotkey is refused (floor occupied).
- New parity test: representative transcript through hotkey path
  before and after factoring → identical output.
- New test: `pipeline=true` response includes `egress_boundary`.
- `npx vitest run` — frontend tests:
  - `transcribeWav()` sends `pipeline: true` in request body.
  - MicButton callback receives pipeline-processed text.
- Visual at 1440: speak into the inlet mic, verify corrected text
  appears (if corrections exist in the learning store).
