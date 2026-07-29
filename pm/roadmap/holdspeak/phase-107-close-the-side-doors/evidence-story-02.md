# Evidence - HS-107-02

- **Story:** HS-107-02 - The typing families — 10 sites through the kernel
- **Status:** done
- **Date:** 2026-07-28

## Proof

### Captured run — 2026-07-29T04:59:50Z

- **Command:** `uv run pytest -q tests/unit/test_dictation_commit_boundary.py tests/unit/test_kernel_effect_fence.py tests/unit/test_desktop_type_text_kernel.py tests/unit/test_delivery_commands.py tests/unit/test_process_input_kernel.py tests/unit/test_steering_chokepoint.py tests/unit/test_voice_macro_connector.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 03e58afb6179d1f828165f9c8e6305a0aba21463

```text
.............................................................            [100%]
61 passed in 3.39s
```

### Captured run — 2026-07-29T05:00:02Z

- **Command:** `uv run python scripts/measure_dictation_latency.py --runs 3 --warmups 1 --typing-mode driver --pipeline active --backend mlx`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 03e58afb6179d1f828165f9c8e6305a0aba21463

```text

Fetching 4 files:   0%|          | 0/4 [00:00<?, ?it/s]
Fetching 4 files: 100%|██████████| 4/4 [00:00<00:00, 63310.25it/s]
run=1 warmup=true capture_stop_ms=0.022 transcribe_ms=316.536 punctuation_ms=0.660 pipeline_ms=811.507 type_ms=202.171 release_to_landed_ms=1330.931
run=2 warmup=false capture_stop_ms=0.085 transcribe_ms=176.698 punctuation_ms=0.134 pipeline_ms=505.387 type_ms=184.379 release_to_landed_ms=866.767
run=3 warmup=false capture_stop_ms=0.030 transcribe_ms=176.359 punctuation_ms=0.144 pipeline_ms=498.915 type_ms=177.852 release_to_landed_ms=853.343
run=4 warmup=false capture_stop_ms=0.039 transcribe_ms=176.339 punctuation_ms=0.134 pipeline_ms=501.714 type_ms=174.720 release_to_landed_ms=852.982
HS107_BASELINE {"audio": "tests/fixtures/core_path_smoke_16k.wav", "audio_duration_ms": 2794.688, "live_owner_segment_not_measured": "physical key hold plus microphone acquisition; when typing_sink is the driver probe, focused-app landing is also unmeasured. The fixed WAV enters the same VoiceTypingSession end -> transcribe -> process -> pipeline -> desktop.type_text -> TextTyper driver path", "machine": {"machine": "arm64", "release": "25.2.0", "system": "Darwin"}, "model": {"backend": "mlx", "configured_backend": "faster-whisper", "load_ms": 1247.079, "name": "small"}, "pipeline": {"configured_enabled": true, "endpoint": "http://192.168.1.43:8080/v1", "mode": "active"}, "runs": 3, "samples_ms": [{"capture_stop_ms": 0.085, "pipeline_ms": 505.387, "punctuation_ms": 0.134, "release_to_landed_ms": 866.767, "transcribe_ms": 176.698, "type_ms": 184.379}, {"capture_stop_ms": 0.03, "pipeline_ms": 498.915, "punctuation_ms": 0.144, "release_to_landed_ms": 853.343, "transcribe_ms": 176.359, "type_ms": 177.852}, {"capture_stop_ms": 0.039, "pipeline_ms": 501.714, "punctuation_ms": 0.134, "release_to_landed_ms": 852.982, "transcribe_ms": 176.339, "type_ms": 174.72}], "schema": "holdspeak.dictation-latency/v1", "summary_ms": {"capture_stop_ms": {"max": 0.085, "median": 0.039, "min": 0.03}, "pipeline_ms": {"max": 505.387, "median": 501.714, "min": 498.915}, "punctuation_ms": {"max": 0.144, "median": 0.134, "min": 0.134}, "release_to_landed_ms": {"max": 866.767, "median": 853.343, "min": 852.982}, "transcribe_ms": {"max": 176.698, "median": 176.359, "min": 176.339}, "type_ms": {"max": 184.379, "median": 177.852, "min": 174.72}}, "transcript_sha256": ["sha256:ef537f25c895bfa782526529a9b63d97aa631564d5d789c2b765448c8635fb6c", "sha256:ef537f25c895bfa782526529a9b63d97aa631564d5d789c2b765448c8635fb6c", "sha256:ef537f25c895bfa782526529a9b63d97aa631564d5d789c2b765448c8635fb6c"], "typing_sink": "desktop_type_text_kernel_to_texttyper_driver", "warmups": 1}
```

### Captured run — 2026-07-29T05:00:13Z

- **Command:** `git diff --exit-code --stat -- holdspeak/kernel/broker.py holdspeak/kernel/admission.py holdspeak/kernel/journal.py holdspeak/kernel/model.py holdspeak/kernel/executor.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 03e58afb6179d1f828165f9c8e6305a0aba21463

```text
(no output)
```

## Live proofs (implementation session, this machine, 2026-07-29)

Recorded verbatim from the real-metal implementation session (temporary
journals; the closeout re-proves these beats in one staged session).

- **Dictation → agent pane through `process.input@1`** (real MLX
  transcription of the fixture WAV, real tmux): op
  `op_f30b416661a24783b0250faec2f32323`, native receipt
  `authority_basis=direct_gesture`, `payload_head="terminal text 44
  bytes submit=True"`, `payload_sha256=sha256:6ec038df…`, outcome
  `delivered`; kernel receipt `rcpt_d947567e…` state `succeeded`.
  Pane landed: `DICTATION_AGENT_LANDED The quick brown fox jumps over
  the lazy dog.`
- **Cadence reply → real tmux pane** through the real FastAPI route
  (authenticated owner, real awaiting-session row): op
  `op_d4b158faad4a44db950e03f3582cdad9`, pane `%1319`, native receipt
  `direct_gesture` / `terminal text 30 bytes submit=True`, kernel
  receipt `rcpt_63c07b55…` `succeeded`. Pane landed:
  `CADENCE_REPLY_LANDED HS107 live Cadence reply proof`.
- **Wake typing act into real TextEdit** (mic segment driven
  programmatically with fixed audio; `_transcribe_wake`,
  `desktop.type_text@1`, focus binding, TextTyper, macOS driver all
  real): op `op_26f21a614b2c417eba252e484c110b14`,
  `gesture=wake_utterance`, `head="desktop text 28 bytes
  submit=False"`, kernel receipt `rcpt_bc933d3e…` `succeeded`.
- **Named refusal** (valid companion-send gesture, no desktop driver):
  op `op_f25d854efb884e6faac22edd489c087c`, outcome
  `desktop_type_driver_unavailable`, kernel receipt `rcpt_f30aacc9…`
  state `refused`. No text typed.

## Latency verdict

Baseline (HS-107-01 evidence) vs migrated (captured above), medians:
release_to_landed **926.297 → 853.343 ms (improved)**; transcribe
191.457 → 176.359; pipeline 576.630 → 501.714; type 155.796 → 177.852
(+22 ms — the type component now honestly includes durable admission,
inline gesture warrant/claim, and focus recheck; disclosed, not
hidden). No hold, no confirmation, no new visible step on the owner's
path.

## Full suite (implementation session)

`uv run pytest -q --ignore=tests/e2e/test_metal.py` →
`2 failed, 4313 passed, 37 skipped in 956.82s`; the two failures are
the pre-existing `tests/uat/test_build_ledger.py::
test_committed_ledger_is_up_to_date` and `tests/uat/test_voice_notes.
py::test_transcribe_up_but_unreachable_is_honest`. No new failures.
