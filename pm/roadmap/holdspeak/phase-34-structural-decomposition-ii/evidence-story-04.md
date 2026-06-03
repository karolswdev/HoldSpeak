# Evidence — HS-34-04 (Decompose `intel.py` → `intel/` package)

**Shipped:** 2026-06-03. The 1,066-line `intel.py` is now an `intel/` package with a
**full re-export `__init__`**, mirroring the Phase-31 db split. No caller or test
import changed; the intel suite (incl. the egress-invariant test) stays green.

## What changed

`holdspeak/intel.py` → `holdspeak/intel/` (acyclic: `models` ← `parsing`/`providers`
← `engine`; `providers.build_configured_meeting_intel` imports the engine lazily to
break the providers↔engine cycle):

| Module | Lines | Holds |
|---|---|---|
| `models.py` | 88 | `MeetingIntelError`, `ActionItem`, `IntelResult`, `_generate_action_item_id` + the `DEFAULT_INTEL_*` / `VALID_INTEL_PROVIDERS` / `SELF_HOSTED_…` constants |
| `parsing.py` | 209 | JSON coercion/parsing helpers (`_extract_json`, `_coerce_action_items`, `_describe_cloud_exception`, …) |
| `providers.py` | 267 | provider resolution + egress posture (`resolve_intel_provider`, `get_*_runtime_status`, `resolve_llm_capability`, `build_configured_meeting_intel`, `intel_egress_posture`) |
| `engine.py` | 547 | the `MeetingIntel` engine |
| `__init__.py` | 111 | the optional-dependency import head (`Llama`/`OpenAI`) + full re-export |

Old: **1,066 lines, one module.** New: **1,222 lines across 5 files** (the +156 is
per-module imports/docstrings; the biggest file is now `engine.py` at 547).

## Method + the monkeypatch hazards (tests unchanged)

Decorator-aware AST extraction (as HS-34-03), call graph computed to assign each of
the 24 defs. The intel suite patches three names on the **package** — all preserved:

- **`OpenAI` / `Llama`** (`test_intel_cloud`, `test_intel_egress_invariant`,
  `test_intel_streaming`, `test_runtime_knob_audit`). The optional-dependency
  `try: from … import …` head lives in `__init__` (the patch target); `providers`
  and `engine` read them as `_intel_pkg.OpenAI` / `_intel_pkg.Llama` (and
  `_intel_pkg._OPENAI_IMPORT_ERROR` / `_intel_pkg._IMPORT_ERROR`) at call time, so a
  package-level patch reaches both. A committed test asserts the engine's cloud
  guard sees a package patch of `OpenAI`.
- **`resolve_intel_provider`** (`test_plugin_host_llm_capability`). Re-export makes
  the package attr patchable; the one *intra-package* caller (`resolve_llm_capability`
  in `providers`) calls it via `_intel_pkg.resolve_intel_provider` so the patch
  reaches it too. (This was the only test that initially failed; fixed by the
  package-routed call — no test changed.)

Relative imports gained one dot (`.config` → `..config`, `.logging_config` →
`..logging_config`). Imports trimmed via `ruff --fix`; residual undefined names
resolved via `ruff --select F821` (caught `_IMPORT_ERROR`, `socket`, and the
`MeetingIntel` forward-ref → a `TYPE_CHECKING` import). The re-export imports follow
the import head, marked `# noqa: E402`.

## Tests ran

- Intel-sensitive suites: `test_intel_egress_invariant`, `test_intel_cloud`,
  `test_intel_command`, `test_intel_queue`, `test_plugin_host_llm_capability`,
  `test_runtime_knob_audit`, `test_intel_streaming` → **89 passed.**
- New `tests/unit/test_intel_package.py` (surface + patch-target + engine-reads-via-
  package guards) → **4 passed.**
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **1962 passed, 15 skipped**
  (= the post-HS-34-03 baseline; no regression).
- `uv run ruff check holdspeak/intel/` (+ `--select F821`) → **All checks passed!**

## Done-when

- [x] `intel.py` → an `intel/` package (models / providers / parsing / engine).
- [x] `__init__` re-exports the full public surface; no caller or test import
      changed; egress-invariant + intel suite green.
- [x] Full suite green; package ruff-clean.

## Decisions / deviations

- **`OpenAI`/`Llama` import head stays in `__init__`** (not a submodule) because
  it's the canonical patch target the whole intel suite uses; `providers`/`engine`
  read through the package.
- **`build_configured_meeting_intel` imports the engine lazily** to keep the
  providers↔engine edge acyclic at import time.
