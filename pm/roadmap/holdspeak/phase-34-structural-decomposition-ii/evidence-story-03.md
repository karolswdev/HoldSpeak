# Evidence — HS-34-03 (Decompose `agent_context.py` → `agent_context/` package)

**Shipped:** 2026-06-03. The 1,381-line / 46-function `agent_context.py` is now an
`agent_context/` package with a **full re-export `__init__`** (63 names), mirroring
the Phase-31 db split. No caller or test import changed; the monkeypatch targets
still resolve.

## What changed

`holdspeak/agent_context.py` → `holdspeak/agent_context/` (acyclic layering
`_common` ← `models` ← `hs_context`/`hooks` ← `sessions`):

| Module | Lines | Holds |
|---|---|---|
| `_common.py` | 26 | `_optional_str`, `_format_timestamp`, `_parse_timestamp` (leaf utils) |
| `models.py` | 184 | all constants (incl. `AGENT_CONTEXT_FILE`) + the `AgentSession` dataclass |
| `hs_context.py` | 341 | `RepoRoot` + the `.hs` loader (`detect_repo_root`, `load/compact/render_hs_project_context`) + its parsers |
| `hooks.py` | 132 | Claude/Codex hook templates, `_agent_hook_command`, tmux detection |
| `sessions.py` | 791 | the agent-session registry, state IO, assistant-text extraction |
| `__init__.py` | 152 | re-exports the full surface (63 names) + `import shutil` |

Old: **1,381 lines, one module.** New: **1,626 lines across 6 files** (the +245 is
per-module imports/docstrings; the biggest file is now `sessions.py` at 791).

## Method — AST extraction (the Phase-31 technique)

Functions were **interleaved** by domain in the original (e.g. `detect_tmux_context`
sat between session functions) with shared utils, so a line-range cut was
impossible. I parsed the module, computed the cross-domain call graph to assign
each of the 46 defs to a module, and extracted each node's **exact source span**
(decorator-aware: `start = min(decorator linenos)` — `ast.get_source_segment`
silently drops decorators, which would have stripped `@dataclass(frozen=True)` off
`AgentSession`/`RepoRoot`; a committed test now guards that). Imports were trimmed
with `ruff --fix` and the residual undefined names resolved via `ruff --select
F821` until clean.

## Monkeypatch targets preserved (the real risk) — tests unchanged

- **`AGENT_CONTEXT_FILE`** — tests do `monkeypatch.setattr(agent_context, "AGENT_CONTEXT_FILE", tmp)`
  on the **package** (5 sites). Its readers all live in `sessions.py`; a bare
  module global there would not see a patch on the package. So `sessions.py` reads
  it through the package at call time via a one-line `_default_state_file()`
  (`return _agent_context_pkg.AGENT_CONTEXT_FILE`), and every `... or
  AGENT_CONTEXT_FILE` site now resolves the live, patchable value.
- **`shutil.which`** — tests patch `holdspeak.agent_context.shutil.which`. `__init__`
  re-exposes `import shutil`; `hooks.py` calls `shutil.which(...)` on the same
  module singleton, so the patch is seen.
- **Function patches** (e.g. `get_recent_awaiting_agent_session` in
  `test_web_runtime.py`) — auto-preserved by the full re-export: callers read the
  package attribute / lazy-import, exactly as before.

## Tests ran

- Monkeypatch-sensitive suites: `test_agent_context.py`, `test_web_project_kb_api.py`,
  `test_web_runtime.py`, `test_web_server.py` → **163 passed.**
- New `tests/unit/test_agent_context_package.py` (public-surface + frozen-dataclass
  + `shutil` re-expose guards) → **4 passed.**
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **1958 passed, 15 skipped**
  — identical to the post-HS-34-02 baseline.
- `uv run ruff check holdspeak/agent_context/` (+ `--select F821`) → **All checks passed!**

## Done-when

- [x] `agent_context.py` → an `agent_context/` package (models / sessions /
      hs-context / hooks + a `_common` leaf).
- [x] `__init__` re-exports the full public surface (63 names); no caller or test
      import changed; monkeypatch targets resolve.
- [x] Full suite green; package ruff-clean.

## Decisions / deviations

- **Package + full re-export** (the resolved deferred decision) — *not* a single
  state class: the `.hs` loader and hook templates aren't session state, so one
  class would be a false grouping.
- **A `_common.py` leaf** for the three cross-cutting utils — keeps the layering
  acyclic (`sessions` → `hooks`/`hs_context` → `models` → `_common`).
- **`_default_state_file()` indirection** chosen over editing the tests' patch
  target — honors the done-when's "no test changed; monkeypatch targets resolve."
