# HS-34-03 — Decompose `agent_context.py` → `agent_context/` package

- **Status:** done (2026-06-03). Evidence: [evidence-story-03.md](./evidence-story-03.md).

## Goal

`agent_context.py` is 1,381 lines of **46 flat module-level functions** spanning
three unrelated concerns. Decompose it into an `agent_context/` package with a full
re-export `__init__`, mirroring the Phase-31 db split — so every
`from holdspeak.agent_context import X` caller is unchanged.

## Scope

- Create `holdspeak/agent_context/` (replacing the single module) with domain
  modules along the docstring/function clusters:
  - `models.py` — `AgentSession`, `RepoRoot` dataclasses + shared validation/keys.
  - `sessions.py` — the agent-session registry: `ingest_agent_hook_event`,
    `get_recent_*` / `select_*` / `clear_*` / `pin_*` / `list_*` /
    `set_agent_session_summary`, the awaiting-session helpers, the assistant-text
    extractors (`extract_last_assistant_text`, `looks_like_agent_question`, …), and
    the state IO (`_read_state`/`_write_state`/`_state_lock`/`_prune_sessions`).
  - `hs_context.py` — the `.hs` project-context loader: `detect_repo_root`,
    `load_hs_project_context`, `compact_hs_project_context`,
    `render_hs_context_for_prompt`, and their `_read_*`/`_parse_*`/`_normalize_*`
    helpers.
  - `hooks.py` — `claude_hook_template`, `codex_hook_template`,
    `_agent_hook_command`, and the tmux helpers (`detect_tmux_context`,
    `_read_tmux_display`).
  - `__init__.py` — re-export the **full public surface** (every name callers/tests
    use today), so the import path is stable. **Decision (deferred → resolve here):**
    a *package of domain modules*, not a single state class — the `.hs` loader and
    hook templates aren't session state, so one class would be a false grouping.
- Phase-31 lessons: a split module needs its own `import`s; relative imports gain a
  dot; run `ruff --select F821`. Watch **monkeypatch targets** — tests patching
  `holdspeak.agent_context.<symbol>` must still resolve (re-export from `__init__`,
  and keep state-path constants importable where tests patch them).

## Test plan

- `grep` tests for `agent_context` monkeypatch / patch targets; confirm each still
  resolves after the split.
- `ruff --select F821` on each new module.
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` — full suite green.
- `uv run ruff check holdspeak/agent_context/` — clean.

## Done when

- [x] `agent_context.py` → an `agent_context/` package (models / sessions /
      hs-context / hooks).
- [x] `__init__` re-exports the full public surface; no caller or test import
      changed; monkeypatch targets resolve.
- [x] Full suite green; package ruff-clean.
