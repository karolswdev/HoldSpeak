# HS-1-09 — Step 8: Doctor checks (LLM runtime + structured-output compile)

- **Project:** holdspeak
- **Phase:** 1
- **Status:** done
- **Depends on:** HS-1-04 (runtime + grammars), HS-1-05 (blocks loader), HS-1-08 (assembly helper)
- **Unblocks:** HS-1-11 (DoD — doctor green-state check is part of the DoD smoke)
- **Owner:** unassigned

## Problem

Spec §9.5 calls for two new `holdspeak doctor` checks that surface
the DIR-01 install state without requiring the user to dig through
config or run the dictation CLI:

- `DIR-DOC-001` — `LLM runtime`. Reports the resolved backend
  (`mlx` | `llama_cpp`), model id/path, and a load-status tag
  (`loaded` | `available` | `missing`). For `auto`, the resolution
  reason is included.
- `DIR-DOC-002` — `Structured-output compilation`. Reports whether
  the constraint artifact compiled from the resolved `blocks.yaml`
  is accepted by the active backend (GBNF for `llama_cpp`,
  JSON-schema for `mlx`).
- `DIR-DOC-003` — Both checks MUST be `INFO`/`WARN`-only (never
  `FAIL`) when DIR-01 is disabled, since the pipeline is opt-in
  and a clean install with `pipeline.enabled = false` should not
  produce a doctor failure.

The shared `assembly` helper (HS-1-08) already knows how to resolve
blocks + the runtime; this story wraps both primitives in
doctor-shaped check renderers and slots them into
`collect_doctor_checks`. No new modules; the doctor picks up two
new lines.

The doctor's `DoctorCheck.status` field is `PASS|WARN|FAIL`. The
spec's "INFO" maps onto `PASS` with informational detail (the
existing convention — see `_check_runtime`). `FAIL` is reserved
for hard failures that block the user even with the feature off
(e.g. broken installation), which is **never** the right verdict
for an opt-in DIR-01 (DIR-DOC-003).

## Scope

- **In:**
  - `holdspeak/commands/doctor.py`:
    - `_check_dictation_runtime(config)` — uses
      `runtime.resolve_backend` to pick the backend (when enabled
      explicitly or `auto`), then checks `Path.exists()` against the
      configured model path. Returns:
      - `PASS` — disabled (`detail="dictation pipeline disabled
        (opt-in)"`).
      - `PASS` — enabled, backend resolved, model file present.
      - `WARN` — enabled but backend can't resolve **or** model
        file missing. Includes a `fix` hint pointing at the
        relevant extra (`holdspeak[dictation-mlx]` /
        `holdspeak[dictation-llama]`) or the conventional model
        download path.
    - `_check_dictation_constraint_compile(config)` — loads blocks
      via `resolve_blocks(global, None)`, projects to a `BlockSet`
      via `LoadedBlocks.to_block_set()`, calls the active
      backend's compiler (`to_outlines` for `mlx`, `to_gbnf` for
      `llama_cpp`). Returns:
      - `PASS` — disabled or no blocks file (`detail` names which).
      - `PASS` — compile succeeded; detail names backend + block
        count.
      - `WARN` — `GrammarCompileError` or any other compile-side
        exception, with the offending message + a `fix` hint
        pointing at `holdspeak dictation blocks validate`.
  - `collect_doctor_checks` appends both checks (after the meeting
    intel checks, before the hotkey check — keeps related
    LLM-runtime checks visually grouped).
  - `tests/unit/test_doctor_command.py` — six new cases covering
    each branch (disabled, enabled+pass, enabled+resolve-fail,
    enabled+model-missing, compile-pass, compile-fail).
- **Out:**
  - Actually loading the model from disk inside the doctor —
    deferred (cold-load cost is unacceptable for a doctor run; the
    dictation `runtime status` CLI is the discovery surface, the
    HS-1-11 manual end-to-end is the verification).
  - Doctor JSON output / machine-readable mode — already missing
    project-wide; orthogonal to DIR-01.
  - The cross-runtime "are both backends present" check — DIR-02
    (the existing single-backend check is sufficient for DIR-01).

## Acceptance criteria

- [x] `doctor` output includes a line `[PASS|WARN|FAIL] LLM runtime: ...`
      and `[PASS|WARN|FAIL] Structured-output compilation: ...`.
- [x] With `dictation.pipeline.enabled = false`, both checks return
      `PASS` (DIR-DOC-003 — never `FAIL` when disabled).
- [x] With `pipeline.enabled = true` and backend resolvable + model
      file present, `LLM runtime` returns `PASS` and the detail
      includes the resolved backend + the resolution reason.
- [x] With `pipeline.enabled = true` and backend not resolvable,
      `LLM runtime` returns `WARN` with a `fix` hint pointing at
      the right `holdspeak[dictation-*]` extra.
- [x] With `pipeline.enabled = true` and backend resolvable but
      model file missing, `LLM runtime` returns `WARN` naming the
      missing path.
- [x] With a valid `blocks.yaml` and resolvable backend, the
      compile check returns `PASS` and the detail names the
      backend + block count.
- [x] With a malformed-from-the-compiler-perspective `BlockSet`,
      the compile check returns `WARN` with a `fix` hint pointing
      at `holdspeak dictation blocks validate`.
- [x] `uv run pytest -q tests/unit/test_doctor_command.py` → all green.
- [x] Full regression: 895+N passed, 13 skipped, 1 pre-existing
      hardware-only Whisper-loader fail.

## Test plan

- **Unit:** new cases in `tests/unit/test_doctor_command.py`.
- **Regression:** `uv run pytest -q tests/`.
- **Manual:** None (HS-1-11's DoD smoke is the manual cross-check
  against a real install).

## Notes / open questions

- The `LLM runtime` check uses `Path.exists()` rather than calling
  `build_runtime` to avoid paying the cold-load cost on every
  `holdspeak doctor` invocation. The trade-off: the doctor reports
  "available" when the file is on disk but doesn't verify the
  weights loadable. The CLI's `dictation runtime status` makes the
  same trade-off; HS-1-11's manual smoke is the actual load
  verification.
- The compile check **does** call `to_gbnf` / `to_outlines` because
  those are pure-Python and cheap; surfacing a malformed
  `extras_schema` early matters more than the few-ms compile cost.
- `INFO` is intentionally collapsed onto `PASS` here. A separate
  `INFO` status would force a `_summarize` change and a doctor
  output redesign — out of scope. The spec's "INFO/WARN, never
  FAIL" intent is honored: a disabled or missing-blocks state
  produces `PASS` with an informational detail.
- The two checks are deliberately positioned **after** the meeting
  intel checks in `collect_doctor_checks` — they share the
  "LLM/runtime" mental category, and meeting intel is more central
  to today's user flow.
