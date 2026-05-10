# Evidence — HS-18-02 Project Context Conventions + Safe Maintenance Contract

**Story:** [story-02-project-context-conventions.md](./story-02-project-context-conventions.md)  
**Status:** done  
**Date:** 2026-05-10

## What Shipped

- Project context conventions
  - Canonical editable layout: `.hs/` directory with `instructions.md`, `context.md`, `memory.md`, `workflows.md`, `issues.md`, `terms.md`, `targets.md`, and `ignore`.
  - Flat read-only compatibility files: `.hs_context`, `.hs_issues`, `.hs_memory`, `.hs_instructions`, `.hs_workflows`, `.hs_terms`, `.hs_targets`, and `.hs_ignore`.
  - Precedence: `.hs/<name>.md` wins over matching flat `.hs_*` file.
- Discovery behavior
  - Repo/project root detection recognizes `.hs/`, `.hs_context`, `.git`, and legacy `.holdspeak`.
  - Nested cwd detection works through `detect_repo_root`.
- Safety behavior
  - Per-file prompt budget remains in place.
  - Very large files are skipped.
  - Binary files are skipped.
  - Obvious secret-looking content is skipped.
  - Skips are returned in `skipped` and `warnings` for visibility.
- Write policy
  - `.hs/` files are editable through the web UI after user action.
  - Flat `.hs_*` files are read-only inputs.
  - HoldSpeak never writes project context automatically during dictation.
- Documentation
  - `README.md` and `docs/USER_GUIDE.md` document the layout, flat compatibility files, precedence, write policy, and skip behavior.

## Commands Run

```bash
.venv/bin/pytest -q tests/unit/test_agent_context.py tests/integration/test_dictation_project_context.py tests/integration/test_web_project_kb_api.py
```

Result: `55 passed in 1.95s`.

```bash
python3 -m py_compile holdspeak/agent_context.py tests/unit/test_agent_context.py
```

Result: passed.

## Acceptance Mapping

- Project-context convention documented: `README.md`, `docs/USER_GUIDE.md`.
- Discovery helper finds context from repo root and nested cwd: `test_detect_repo_root_supports_flat_hs_context_marker`, existing repo-context tests.
- Oversized, binary, and obvious secret-looking files skipped with warnings: `test_hs_project_context_skips_binary_large_and_secret_files`.
- Write policy explicit: `docs/USER_GUIDE.md` and loader `write_policy` payload.
- Flat dotfiles and `.hs/` directory layouts covered: `test_load_hs_project_context_supports_flat_dotfiles`, `test_hs_directory_takes_precedence_over_flat_dotfiles`, existing `.hs/` tests.

## Residual Notes

- Secret detection is intentionally basic. It catches obvious patterns only and does not replace a real secret scanner.
- The web UI continues to write only canonical `.hs/` files.
