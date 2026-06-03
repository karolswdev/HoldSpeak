# Phase 34 — Structural Decomposition II — Final Summary

**Status:** CLOSED ✅ — 5/5 stories shipped. **Closed:** 2026-06-03.

The twin of Phases 26 (web-server), 31 (db), and 32 (web-runtime). Those tamed the
biggest god-objects; this phase finished the **explicitly-deferred** finer split
Phase 26 named in its own follow-ups ("the three large route modules could be
sub-split if they impede navigation later") plus the two largest remaining
non-route modules. Behavior-preserving throughout: every import path and HTTP route
is unchanged.

## What shipped

| Story | Target → result |
|---|---|
| **HS-34-01** | `web/routes/dictation.py` (1,607L, 26 routes) → `routes/dictation/` (intents · agent · project_docs · blocks · kb · pipeline + a ctx-free `_helpers.py`); shared suggestion store threaded explicitly. |
| **HS-34-02** | `web/routes/activity.py` (1,319L, 38 routes) → `routes/activity/` (ledger · rules · enrichment · candidates · plugin_jobs); no shared state to thread. |
| **HS-34-03** | `agent_context.py` (1,381L, 46 funcs) → `agent_context/` package (`_common` ← `models` ← `hs_context`/`hooks` ← `sessions`), full re-export. |
| **HS-34-04** | `intel.py` (1,066L) → `intel/` package (`models` ← `parsing`/`providers` ← `engine`), full re-export. |
| **HS-34-05** | Closeout — invariants re-verified, this summary. |

## By the numbers

**Before:** four single files, **5,373 lines combined** (largest 1,607).
**After:** four packages totalling 6,159 lines across 24 modules; the largest
single file is now `intel/engine.py` at 547 (was 1,607). The +786 is per-module
import/docstring/`build_*_router` boilerplate — the win is navigability, not line
count.

| Target | before | after (package) | largest module |
|---|---|---|---|
| dictation routes | 1,607 | 1,854 (8 files) | `_helpers.py` 594 |
| activity routes | 1,319 | 1,457 (6 files) | `enrichment.py` 614 |
| `agent_context` | 1,381 | 1,626 (6 files) | `sessions.py` 791 |
| `intel` | 1,066 | 1,222 (5 files) | `engine.py` 547 |

## Conventions reused / lessons

- **Route splits** (Phase-26 pattern): each `build_*_router(ctx)` registers absolute
  `/api/...` paths; the package `__init__` composes them via `include_router`, so the
  full `(path, method)` table is byte-identical. Locked by committed invariant tests
  — dictation hash `0a0b26562cf25a36` (26 routes), activity `d4332051064ff059` (38).
- **Module→package splits** (Phase-31 pattern): full re-export `__init__`, so
  `from holdspeak.X import Y` is unchanged. Done via **decorator-aware AST
  extraction** (functions were interleaved by domain) — `ast.get_source_segment`
  silently drops decorators, which would have stripped `@dataclass(frozen=True)`;
  caught and guarded by a test.
- **Monkeypatch targets honored with tests unchanged** (the phase's hardest
  constraint): a name patched on the *package* but read inside a submodule is routed
  through the package at call time —
  `agent_context.sessions` reads `AGENT_CONTEXT_FILE` via `_agent_context_pkg`;
  `intel.providers`/`intel.engine` read `OpenAI`/`Llama`/`resolve_intel_provider` via
  `_intel_pkg`; `shutil` is re-exposed for the tmux `shutil.which` patch. The
  egress-invariant test has a committed companion asserting a package-level `OpenAI`
  patch reaches the engine.
- **`ruff --select F821`** after each split caught every dropped import / undefined
  name (`_IMPORT_ERROR`, `socket`, the `MeetingIntel` forward-ref) — the single most
  valuable check for a verbatim move.

## State at close

- **Suite:** green — `uv run pytest -q --ignore=tests/e2e/test_metal.py` →
  **1,966 passed, 15 skipped** (incl. 15 new phase guard tests across 4 files).
- **All four packages ruff + F821 clean.** Route tables byte-identical to the
  pre-phase baselines.
- **Branch:** `phase-34/hs-34-01-dictation-routes-split` (open of the phase + 5
  story commits). No hardware needed; no API/behavior change.

## Decisions of record

- 2026-06-03 — **Scope = the 4 user-named targets** + closeout; `meetings.py` /
  `system.py` left as-is (below the pain threshold) — user.
- 2026-06-03 — **Package + full re-export** (not a façade module / not a state
  class) for `agent_context`/`intel`, mirroring Phase 31.
- 2026-06-03 — **Honor monkeypatch targets without changing tests** via package-
  routed reads (`_pkg.<name>`), rather than repointing the patches.

## Follow-ups beyond this phase

- `web/routes/meetings.py` (1,013L) / `system.py` (921L) could be sub-split if they
  later impede navigation — **not required** now.
- The decomposition lineage (26 → 31 → 32 → 34) is now complete for every
  god-object the reviews flagged; future structural work should be driven by a fresh
  pain signal, not preemptive.
