# HS-1-02 — Step 1: Transducer contracts

- **Project:** holdspeak
- **Phase:** 1
- **Status:** ready
- **Depends on:** HS-1-01 (spike must validate the latency assumption first)
- **Unblocks:** HS-1-03 (pipeline executor needs the contracts)
- **Owner:** unassigned

## Problem

DIR-01 introduces a new plugin kind, `transducer`, defined in spec §6.4
(`Utterance`, `IntentTag`, `StageResult`, `Transducer` Protocol). The
existing `holdspeak/plugins/contracts.py` defines the `Plugin` Protocol
and shared types for the meeting-side MIR-01 work; we extend it without
breaking it.

Per spec §4 (Relationship to Existing Plans) item 1: "Implementations
MUST share `holdspeak/plugins/contracts.py` types where they overlap."

## Scope

- **In:**
  - New module `holdspeak/plugins/dictation/contracts.py` defining `Utterance`, `IntentTag`, `StageResult`, and the `Transducer` Protocol exactly as specified in DIR-01 §6.4.
  - Extend `Plugin.kind` enum (or string set) in `holdspeak/plugins/contracts.py` to allow the value `"transducer"` alongside existing kinds.
  - `__init__.py` files for `holdspeak/plugins/dictation/` package.
  - Unit tests at `tests/unit/test_dictation_contracts.py`: type construction, immutability (`@dataclass(frozen=True)`), `Transducer` Protocol structural-conformance check via `isinstance` against a minimal stub.
- **Out:**
  - The pipeline executor (HS-1-03).
  - Any concrete `Transducer` implementation (HS-1-06).
  - The runtime / grammar modules (HS-1-04).
  - Block config (HS-1-05).

## Acceptance criteria

- [ ] `holdspeak/plugins/dictation/__init__.py` and `holdspeak/plugins/dictation/contracts.py` exist.
- [ ] `Utterance`, `IntentTag`, `StageResult` are `@dataclass(frozen=True)`; field names and types match DIR-01 §6.4 exactly.
- [ ] `Transducer` is a `typing.Protocol` with the three attributes and the `run` method spec'd in §6.4.
- [ ] `Plugin.kind` accepts `"transducer"` without breaking existing MIR-01 kinds. Verify with a quick search that no MIR-01 code paths regress.
- [ ] `tests/unit/test_dictation_contracts.py` exists with ≥4 cases (one per dataclass + one Protocol conformance check) and all pass.
- [ ] `uv run pytest tests/unit/test_dictation_contracts.py -q` exit code 0; output captured in `evidence-story-02.md`.

## Test plan

- **Unit:** `uv run pytest tests/unit/test_dictation_contracts.py -q` — new file, ≥4 cases.
- **Regression:** `uv run pytest tests/ -q` — must remain green; specifically existing tests under `holdspeak/plugins/` (MIR-01 contracts).
- **Manual:** `python -c "from holdspeak.plugins.dictation.contracts import Transducer, Utterance, IntentTag, StageResult; print('ok')"` — quick import smoke.

## Notes / open questions

- `IntentTag.extras: dict[str, Any]` is the open-ended bag where blocks stash captured fields (e.g., `{"stage": "buildout"}`). It's `Any`-typed by design — the GBNF grammar (HS-1-04) is the structural guarantee, not the type hint.
- `StageResult.metadata` is for introspection; ring-buffer storage (DIR-F-009) is not in this story — that lives in the pipeline executor (HS-1-03).
- The `Transducer.requires_llm: bool` flag exists so the pipeline can short-circuit LLM-needing stages when the runtime is disabled (DIR-F-011). Do not remove it as "unused" — HS-1-03 will use it.
