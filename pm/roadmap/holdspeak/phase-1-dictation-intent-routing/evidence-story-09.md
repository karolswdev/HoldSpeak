# Evidence — HS-1-09 (Doctor checks)

**Story:** [story-09-doctor.md](./story-09-doctor.md)
**Date:** 2026-04-25
**Status flipped:** backlog → done

## What shipped

- `holdspeak/commands/doctor.py`:
  - `_check_dictation_runtime(config)` — DIR-DOC-001. Calls
    `runtime.resolve_backend` (with the requested
    `dictation.runtime.backend`), then verifies the configured
    model file exists with `Path.exists()`. No cold-load on every
    doctor run. Returns `PASS` (disabled / model available) or
    `WARN` (resolve failure / missing model) — never `FAIL`
    (DIR-DOC-003).
  - `_check_dictation_constraint_compile(config)` — DIR-DOC-002.
    `resolve_blocks(global, None)` → `to_block_set()` →
    `StructuredOutputSchema.from_block_set()` → `to_outlines` (mlx)
    or `to_gbnf` (llama_cpp). Pure-Python compile is cheap so the
    doctor runs it eagerly. Returns `PASS` (disabled / no blocks /
    compile clean) or `WARN` (any compile-side exception) — never
    `FAIL` (DIR-DOC-003).
  - `collect_doctor_checks` appends both checks between the meeting
    intel checks and the hotkey check, keeping LLM-runtime checks
    visually grouped.
- `tests/unit/test_doctor_command.py` — 8 new cases:
  - Disabled-state PASS for both checks.
  - Backend-unresolvable WARN with `holdspeak[dictation-*]` fix
    hint.
  - Model-missing WARN with download fix hint.
  - Model-available PASS with backend + path in the detail.
  - No-blocks-file PASS for the compile check.
  - Valid-blocks PASS naming the active backend + block count.
  - Compiler-raises WARN with the
    `holdspeak dictation blocks validate` hint.

## DIR requirements verified in this story

| Requirement | Verified by |
|---|---|
| `DIR-DOC-001` Doctor reports resolved backend, model id, load status (loaded\|available\|missing) | `test_dictation_runtime_check_pass_when_model_available`, `test_dictation_runtime_check_warn_when_model_missing` (detail names path + status; reason includes the resolution path for `auto`) |
| `DIR-DOC-002` Doctor reports constraint-compile success against the active backend | `test_dictation_compile_check_pass_for_valid_blocks`, `test_dictation_compile_check_warn_when_compiler_raises` |
| `DIR-DOC-003` Both checks INFO/WARN, never FAIL when DIR-01 is disabled | `test_dictation_runtime_check_pass_when_pipeline_disabled`, `test_dictation_compile_check_pass_when_pipeline_disabled` (status == "PASS") |

## Test output

### Targeted (doctor)

```
$ uv run pytest -q tests/unit/test_doctor_command.py
................                                                         [100%]
16 passed in 0.22s
```

### Full regression

```
$ uv run pytest tests/ --timeout=30 -q
... [progress dots elided]
1 failed, 903 passed, 13 skipped, 3 warnings in 17.03s
FAILED tests/e2e/test_metal.py::TestWhisperTranscription::test_model_loads
```

Pre-existing hardware-only Whisper-loader failure (recorded as the
known baseline since HS-1-03). Pass delta: 895 → 903 (+8 new doctor
cases).

## Files in this commit

- `holdspeak/commands/doctor.py` (modified — two new checks +
  registration in `collect_doctor_checks`)
- `tests/unit/test_doctor_command.py` (extended)
- `pm/roadmap/holdspeak/phase-1-dictation-intent-routing/story-09-doctor.md` (new — story authored, status flipped to done in same commit)
- `pm/roadmap/holdspeak/phase-1-dictation-intent-routing/evidence-story-09.md` (this file)
- `pm/roadmap/holdspeak/phase-1-dictation-intent-routing/current-phase-status.md` (story table + "Where we are" + last-updated)
- `pm/roadmap/holdspeak/README.md` (last-updated line)

## Notes

- The doctor's `DoctorCheck.status` enum is `PASS|WARN|FAIL` — the
  spec's "INFO" maps onto `PASS` with informational detail, the
  same convention `_check_runtime` already uses. Extending the enum
  to a separate `INFO` value would force a `_summarize` change and
  a doctor output redesign with no functional gain (DIR-DOC-003 is
  already honored).
- The compile check intentionally falls through to compiling
  against `llama_cpp` even when `resolve_backend` raises. The
  `LLM runtime` check is the canonical surface for the resolve
  failure; reporting it again here would double-bill the user. The
  fall-through still gives block authors a "your YAML is
  structurally valid" signal.
- `tests/integration/test_runtime_*.py` already exercise
  `to_outlines` / `to_gbnf` against real backends. The doctor
  tests stay unit-level: monkeypatch
  `holdspeak.plugins.dictation.runtime.resolve_backend` and
  `…assembly.DEFAULT_GLOBAL_BLOCKS_PATH` so tests run without
  installing either extra.
