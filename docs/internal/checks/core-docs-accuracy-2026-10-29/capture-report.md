# Capture lane accuracy report

Audit date: 2026-10-29  
Lane: capture  
Source base: `4dce2796d`  
Scope: the 18 capture documents listed in `lanes.json`; no product source,
defaults, tests, generated files, canon, or historical records were changed.

The per-document evidence is in
[`capture-audit.json`](capture-audit.json). Eight documents received concrete
corrections, nine were source-checked without a text change, and
`docs/PLATFORMS.md` was checked as generated and left read-only.

## Anchor revalidation

Root rechecked five audit anchors. The audit now uses only existing files and
in-range lines:

* `MEETING_ARCHITECTURE.md`: route package `holdspeak/web/routes/meetings/__init__.py:1-44`
  and import route `holdspeak/web/routes/meeting_import.py:58-146` (the former
  endpoints had exceeded each file by one or two lines).
* `AUTHORITY.md`: `holdspeak/phone/service.py:1-45` is the actual Phone
  service; the nonexistent `holdspeak/services/phone_service.py` was removed.
* `SECURITY_MODEL.md`: startup recovery is established by the active startup
  orchestration in `holdspeak/web_server.py:1883-1915,1931-1935`, kernel
  liveness in `holdspeak/kernel/liveness.py:86-95`, parent reconciliation in
  `holdspeak/kernel/parent_run.py:323-350`, and gate preview handling in
  `holdspeak/coder_gate.py:191-236`; the nonexistent
  `holdspeak/kernel/recovery.py` was removed.
* `STORAGE_AND_MIGRATIONS.md`: database construction/reconciliation is
  `holdspeak/db/core.py:263-285`; startup recovery ordering is the active
  `web_server.py` and `kernel/liveness.py` path above.

These corrections do not change the substantive conclusions: Phone and
Programs remain separate optional reach surfaces, startup recovery is
source-established but not live-observed, and missing receipts do not become
success. The corrected audit is the authority for exact anchors.

## Principal corrections

| Document | Correction | Active source |
|---|---|---|
| `MEETING_MODE_GUIDE.md` | Terminal export maps only `markdown`, `txt`, and `json`; shared config accepts `srt`, but the terminal exporter falls back to `txt`. The local model path, `intent_router_enabled=true`, provider fallback, and full recovery route are now exact. | `holdspeak/config/meeting.py:19-51,91-99`; `holdspeak/main.py:854-880`; `holdspeak/intel/providers.py:640-738`; `holdspeak/web/routes/meetings/crud.py:202-206` |
| `MEETING_INTELLIGENCE.md` | Deferred intelligence still reads `meeting.intel_provider` (`local`, `cloud`, or `auto`) when no adopted destination overrides it. | `holdspeak/services/meeting_intel_service.py:142-150`; `holdspeak/intel/providers.py:222-243,640-738` |
| `MEETING_AFTERCARE.md` | The old Slack route is parked and returns `slack_moved_to_channel`; the active operation is the channel route. | `holdspeak/web/routes/meetings/aftercare.py:53-61`; `holdspeak/web/routes/channels.py:136-139` |
| `DICTATION_PIPELINE_GUIDE.md`, `DICTATION_ARCHITECTURE.md` | A skipped model stage leaves current text unchanged. A non-fatal stage exception resets to the original utterance; a fatal speech-session signal propagates and publishes nothing. `auto` tries MLX only with the required Apple/MLX/model prerequisites, then llama.cpp, otherwise reports unavailable. | `holdspeak/plugins/dictation/pipeline.py:27-46,124-157`; `holdspeak/plugins/dictation/runtime.py:66-142` |
| `VOICE_COMMANDS.md` | `/api/commands/test` is action-specific: `open_url`, `launch_app`, and `shell` execute through the bounded connector; `type_text` and `desk_verb` are preview-only. | `holdspeak/web/routes/system/voice.py:339-382`; `holdspeak/plugins/voice_macro_connector.py:125-187` |
| `ACTIVITY_PREBRIEFING.md` | Replaced absent Use/Dismiss pre-briefing UI with the active Activity Records/Candidates and connectors faces, Start meeting/Dry run controls, and the actual candidate-status API. | `web/src/pages/cores/ActivityCore.tsx:50-73,199-209,245-277,329-367`; `holdspeak/web/routes/activity/candidates.py:29-65`; `holdspeak/web/routes/activity/ledger.py:19-47` |
| `DEVICE_PROTOCOL.md` | LCD helpers truncate to 150; the low-level status emitter passes through, and runtime query responses cap at 500. | `holdspeak/device_status.py:73-90,239-299`; `holdspeak/runtime/device_glue.py:186-192,321-339`; `holdspeak/device_audio_ws.py:182-187,501-506` |

## Architecture handoff: exact capture facts

These are the facts relevant to the root-owned `ARCHITECTURE.md`. This lane did
not edit that document.

### Dictation stage order and defaults

`DictationPipelineConfig` defaults are `enabled=True`,
`stages=["intent-router", "kb-enricher"]`, `max_total_latency_ms=600`,
`target_profile_override="auto"`, `rewrite_passes=1`,
`corrections_enabled=True`, `target_detect_llm_enabled=False`,
`target_detect_llm_below=0.8`, `journal_enabled=True`, and
`journal_retention=500` (`holdspeak/config/meeting.py:357-386`). The known stage
IDs also include `project-rewriter` (`holdspeak/config/meeting.py:288-289`),
but it is not in the default list.

Assembly preserves the configured order. It creates `intent-router` and
`project-rewriter` only when a runtime is available, while `kb-enricher` is
non-LLM (`holdspeak/plugins/dictation/assembly.py:103-139`). Therefore the
default executed order is intent-router then kb-enricher when an admitted model
runtime exists; with no runtime, the model stage is skipped and the non-LLM
stage can still run.

The correction seam runs before the stage loop and is not a StageResult
(`holdspeak/plugins/dictation/pipeline.py:124-157,231-258`). A skipped model
stage leaves the current text unchanged. A non-fatal exception marks the stage,
sets `short_circuited`, restores the original utterance text, and stops later
stages. Fatal speech-session signals are re-raised, so they do not become a
successful raw-text publication.

### Corrections and thresholds

Routing corrections (`intent`, `target`) use Jaccard token overlap with a
default minimum similarity of `0.5` (`holdspeak/plugins/dictation/corrections.py:31-46,101-133`;
`holdspeak/plugins/dictation/builtin/intent_router.py:31-34,208-224`). A routing
correction with fewer than two tokens is refused (`corrections.py:346-347`),
because a one-token gist cannot safely match a sentence. A `text` correction is
an exact, boundary-checked phrase rewrite; a one-word `text` key is legal
(`corrections.py:135-173,346-347`). The in-memory/durable correction cap is 20
entries and a stored gist is bounded to 200 characters (`corrections.py:39-46,95-99`).

The intent nudge uses confidence `0.85` after a `0.5` similarity match, so it
clears the normal block default threshold `0.6`; block files can set a
per-block threshold (`holdspeak/plugins/dictation/builtin/intent_router.py:31-34,208-224`;
`holdspeak/plugins/dictation/blocks.py:193-209,319-324`;
`holdspeak/plugins/dictation/builtin/kb_enricher.py:122-134`). This is distinct
from `target_detect_llm_below=0.8`, which controls optional model-assisted target
detection (`holdspeak/config/meeting.py:379-386`).

### Journal behavior

The journal is local and best-effort. With `journal_enabled=True` and a
repository it records one row per run for `dictation`, `dry_run`, `browser`, or
`hotkey`; transcript and final text are secret-filtered before persistence, and
each insert prunes to the configured last-N retention (`holdspeak/plugins/dictation/journal.py:1-17,28-49,182-239`;
`holdspeak/db/journal.py:1-14,64-137,303-313`). A missing repository or disabled
journal is a no-op and cannot change typed output. Pipeline-off runs still write
a passthrough row when the journal is enabled, with no stages and final text
equal to the transcript (`holdspeak/dictation_runner.py:347-364,547-558`).
Journal or broadcast failures are swallowed and cannot break typing
(`holdspeak/plugins/dictation/journal.py:182-239`).

### Microphone and remote paths

* Local desktop hotkey: `AudioRecorder` uses the local PortAudio/sounddevice
  input stream and returns mono float32 audio at 16 kHz, falling back to the
  device default rate and resampling (`holdspeak/audio.py:1-5,90-105,119-124,200-218`).
  The accepted hotkey press owns the shared audio floor; release ends capture
  and starts one transcription. Unadmitted or raced-away audio is discarded
  (`holdspeak/runtime/dictation_capture.py:485-595`).
* Browser one-shot: `POST /api/dictation/transcribe` accepts one 16 kHz mono
  16-bit PCM WAV body, size-capped; it uses the runtime transcriber and does not
  persist raw audio (`holdspeak/web/routes/system/voice.py:106-119,136-169`).
* Browser stream: authenticated `WS /ws/dictation/stream` receives raw 16 kHz
  mono 16-bit PCM binary frames, accumulates one utterance, and performs one
  final transcription after `{"type":"end"}`. A `start` frame declares whether
  the pipeline is requested; speak-to-fill is verbatim/no journal, while
  dictate-for-delivery runs the pipeline once (`holdspeak/web/routes/system/voice_stream.py:96-130,175-225,300-420`).
  The browser floor lease defaults to 20 seconds and is capped at 120 seconds
  (`holdspeak/web/routes/dictation/floor.py:30-38,69-104`).
* Remote companion: `POST /api/dictation/remote` receives text, not microphone
  bytes. It requires a stable `delivery_id`, claims it before pipeline and
  delivery work, and returns the stored terminal result on retry
  (`holdspeak/web/routes/dictation/pipeline.py:556-620`).
* Device audio is a separate remote PCM source for device/meeting capture, not
  the companion text relay: `/api/devices/audio` accepts pushed 16 kHz mono
  int16 little-endian frames into `RemoteAudioRecorder`
  (`holdspeak/device_audio.py:1-10,84-153`; `holdspeak/device_audio_ws.py:115-163`).

## Cross-lane findings

* `docs/API_SURFACE.md:554` still lists the parked
  `/api/meetings/{meeting_id}/export/slack` route as an active-looking API
  surface. The aftercare source returns `slack_moved_to_channel`; root should
  inspect or regenerate that root-owned/generated inventory.
* `docs/PLATFORMS.md:3-5` is generated from the pinned
  `docs/internal/philo/snapshot.json:4` commit
  `675401a857b85336d4acaa8c65383dfc9636e4c8`, which predates this branch. It
  was read-only here; root should decide whether the generated file is due for
  regeneration and inspect resulting drift.
* The root-owned architecture documentation must not describe the dictation
  correction seam as a stage, must not claim prior-text fallback for a failed
  stage, and must distinguish browser mic/stream capture from remote text relay.

## Verification and hold

Allowed documentation check completed:

```text
Documentation navigation: 18 files checked; local targets and Markdown headings resolve.
```

`git diff --check` completed with no output. No tests, browser/Desk calls,
microphone, provider, launch, send, hardware action, install, staging, or commit
was performed. Unknowns remain deployment and physical-observation questions;
the source review is not a live-operation certification. Hold for SHIP.
