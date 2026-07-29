# Evidence - HS-107-01

- **Story:** HS-107-01 - Dictation's commit boundary — semantics before rerouting
- **Status:** done
- **Date:** 2026-07-28

## Proof

### Captured run — 2026-07-29T03:05:27Z

- **Command:** `uv run pytest -q tests/unit/test_dictation_commit_boundary.py tests/unit/test_kernel_effect_fence.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 08e4240a65c78e0986a5a68905915689b36cafd7

```text
...............                                                          [100%]
15 passed in 1.54s
```

### Captured run — 2026-07-29T03:05:36Z

- **Command:** `uv run python scripts/measure_dictation_latency.py --runs 3 --warmups 1 --typing-mode driver --pipeline active --backend mlx`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 08e4240a65c78e0986a5a68905915689b36cafd7

```text

Fetching 4 files:   0%|          | 0/4 [00:00<?, ?it/s]
Fetching 4 files: 100%|██████████| 4/4 [00:00<00:00, 8952.62it/s]
run=1 warmup=true capture_stop_ms=0.053 transcribe_ms=683.423 punctuation_ms=0.980 pipeline_ms=848.043 type_ms=168.310 release_to_landed_ms=1700.864
run=2 warmup=false capture_stop_ms=0.079 transcribe_ms=214.845 punctuation_ms=0.170 pipeline_ms=640.222 type_ms=155.796 release_to_landed_ms=1011.185
run=3 warmup=false capture_stop_ms=0.080 transcribe_ms=191.457 punctuation_ms=0.176 pipeline_ms=576.630 type_ms=157.892 release_to_landed_ms=926.297
run=4 warmup=false capture_stop_ms=0.027 transcribe_ms=186.845 punctuation_ms=0.137 pipeline_ms=514.995 type_ms=154.989 release_to_landed_ms=857.037
HS107_BASELINE {"audio": "tests/fixtures/core_path_smoke_16k.wav", "audio_duration_ms": 2794.688, "live_owner_segment_not_measured": "physical key hold plus microphone acquisition; when typing_sink is the driver probe, focused-app landing is also unmeasured. The fixed WAV enters the same VoiceTypingSession end -> transcribe -> process -> pipeline -> TextTyper driver path", "machine": {"machine": "arm64", "release": "25.2.0", "system": "Darwin"}, "model": {"backend": "mlx", "configured_backend": "faster-whisper", "load_ms": 2220.592, "name": "small"}, "pipeline": {"configured_enabled": true, "endpoint": "http://192.168.1.43:8080/v1", "mode": "active"}, "runs": 3, "samples_ms": [{"capture_stop_ms": 0.079, "pipeline_ms": 640.222, "punctuation_ms": 0.17, "release_to_landed_ms": 1011.185, "transcribe_ms": 214.845, "type_ms": 155.796}, {"capture_stop_ms": 0.08, "pipeline_ms": 576.63, "punctuation_ms": 0.176, "release_to_landed_ms": 926.297, "transcribe_ms": 191.457, "type_ms": 157.892}, {"capture_stop_ms": 0.027, "pipeline_ms": 514.995, "punctuation_ms": 0.137, "release_to_landed_ms": 857.037, "transcribe_ms": 186.845, "type_ms": 154.989}], "schema": "holdspeak.dictation-latency/v1", "summary_ms": {"capture_stop_ms": {"max": 0.08, "median": 0.079, "min": 0.027}, "pipeline_ms": {"max": 640.222, "median": 576.63, "min": 514.995}, "punctuation_ms": {"max": 0.176, "median": 0.17, "min": 0.137}, "release_to_landed_ms": {"max": 1011.185, "median": 926.297, "min": 857.037}, "transcribe_ms": {"max": 214.845, "median": 191.457, "min": 186.845}, "type_ms": {"max": 157.892, "median": 155.796, "min": 154.989}}, "transcript_sha256": ["sha256:ef537f25c895bfa782526529a9b63d97aa631564d5d789c2b765448c8635fb6c", "sha256:ef537f25c895bfa782526529a9b63d97aa631564d5d789c2b765448c8635fb6c", "sha256:ef537f25c895bfa782526529a9b63d97aa631564d5d789c2b765448c8635fb6c"], "typing_sink": "texttyper_driver_without_focused_app", "warmups": 1}
```

### Captured run — 2026-07-29T03:05:49Z

- **Command:** `git diff --exit-code --stat -- holdspeak/kernel/effect_ledger.json holdspeak/kernel/broker.py holdspeak/kernel/admission.py holdspeak/kernel/journal.py holdspeak/kernel/model.py holdspeak/kernel/executor.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 08e4240a65c78e0986a5a68905915689b36cafd7

```text
(no output)
```
