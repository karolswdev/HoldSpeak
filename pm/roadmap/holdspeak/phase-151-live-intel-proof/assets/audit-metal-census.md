# Phase 151 audit A — the metal census (condensed)

Read-only opus audit, 2026-08-30, against `feat/hs151-live-intel-proof`
(= main `3a37e484`). Full transcript died with the session; every
load-bearing fact preserved here with its anchor. Companion:
[audit-loop-census.md](./audit-loop-census.md),
[metal-probes.md](./metal-probes.md).

## 1. Transcription metal — READY

- Runtimes: mlx-whisper (darwin arm64, pyproject.toml:41),
  faster-whisper (linux, :66); resolution
  holdspeak/transcribe.py:66-96.
- THIS Mac: **mlx_whisper 0.4.3 AVAILABLE** (probed);
  faster_whisper absent; sounddevice/numpy/scipy present.
- **The audio-file door exists** — no mic needed:
  `import_meeting()` (holdspeak/meeting_import.py:201) takes WAV
  natively (+ mp3/m4a/… via ffmpeg, :60), transcribes through the
  normal Transcriber window-by-window. CLI `holdspeak import x.wav`
  (commands/import_recording.py:84); HTTP
  `POST /api/meetings/import` (web/routes/meeting_import.py:52).
  Transcript files (.vtt/.srt/.txt) via `import_transcript()`
  (:395). Both share the persistence tail: save_meeting + deferred
  intel enqueue (meeting_session/persistence.py:84-103).
- tests/e2e/test_metal.py: needs live mic + pyperclip + pynput;
  generates its own WAV via macOS `say`; excluded because mic legs
  hang headless.

## 2. Intel metal — the modern path (and the stale precedent)

- Chain: persistence.py:92 enqueue → IntelQueueWorker
  (intel_queue.py:620) → process_next_intel_job (:503) →
  _bound_claim (:117) → MeetingDeferredQueueBinder.prepare
  (services/meeting_deferred_queue_binding.py:114) → capability
  `meeting.deferred_analysis` (inference_capabilities.py:1063) →
  _process_bound_intel_job (:297-500) → bound.execute (:339) →
  the assigned profile's endpoint; semantic adapter parses
  {summary, topics, action_items}
  (services/inference_semantic_adapters.py:144-176).
- Engine: intel/engine.py:96-240 (provider local = in-process GGUF;
  cloud = any OpenAI-compatible via openai pkg); self-hosted key
  placeholder "sk-no-key-required" (intel/models.py:96); endpoint
  resolution intel/providers.py:596-614; placement
  resolve_meeting_placement (:666-726).
- **Fresh-HOME minimum for .43 dispatch**: (a) a `profiles` row
  kind=openAICompatible base_url=http://192.168.1.43:8080/v1
  (schema.py:1304; ProfileRecord db/models/knowledge.py:141-148);
  (b) an inference assignment binding `meeting.deferred_analysis`
  to it (inference_adoption_service.py); (c) MeetingConfig
  placement resolves it. fresh-desk.yaml seeds ZERO profiles.
- **P55/P57 harnesses are STALE**: their dogfood scripts pass
  `cloud_model/cloud_base_url/...` kwargs that
  `process_next_intel_job` (intel_queue.py:503-511) no longer
  accepts. The pattern (temp DB, real config, MeetingWebServer,
  shots) is reusable; the dispatch composition is not.

## 3. Vision rider

Audit verdict was "defers" (no mlx_vlm; 8080 completion-only) —
**OVERRULED by the orchestrator's 8081 probe** (metal-probes.md):
the box already held the Qwythos-9B + mmproj pair; the snapshot
capability `calendar.snapshot_extract` (inference_capabilities.py:
1078, vision=True) admits openAICompatible profiles via
`_vision_capable()` (calendar_snapshot_service.py:428-434).

## 4. Audio fixtures on the shelf

- `dogfood/_audio/` — 38 WAVs incl. REAL multi-speaker meeting
  recordings (meeting-pylon-incident-warroom.wav,
  meeting-ledgerline-incident-retro.wav,
  meeting-questline-balanced-sync.wav, …) with .script.txt files.
- `tests/fixtures/core_path_smoke_16k.wav` (93 KB, 16 kHz smoke).
- No image fixtures for the snapshot adapter anywhere (its unit
  tests use base64 "AAAA") — vision-probe-week.png is the first.
