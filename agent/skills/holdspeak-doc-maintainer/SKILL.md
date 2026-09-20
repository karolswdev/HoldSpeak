---
name: holdspeak-doc-maintainer
description: Use when updating documentation, capability metadata, requirements or generated references. Applies to the HoldSpeak repository, not to user-installed runtime Workbench skills.
---

# holdspeak-doc-maintainer

Read `AGENTS.md`, `CLAUDE.md` and the current charter first. Owner instructions
in the active session override standing workflows. Work in the assigned clone
or worktree. Paths below are repository-relative; verify them before editing.

## Inspect first

- `docs/internal/philo/data/README.md`
- `docs/internal/DOCS_STYLE.md`
- `scripts/check_docs.py`
- `tests/unit/doc_claims/registry.py`

## Vocabulary and invariants

A source path is traceability, not proof that behavior works. A proposed requirement is not implementation.

## Change path

Edit the source-owned contract or metadata, regenerate derived output, inspect the diff and run drift checks. Keep historical inputs intact and date snapshots. Use ASD-STE100 for user guides.

Update `docs/README.md` and the corresponding Philo capability metadata when behavior
or evidence changes. Keep the source snapshot and test-execution status honest.

## Verification

Collect the relevant tests before running them:

```sh
HOME="$(mktemp -d)" uv run pytest --collect-only -q tests/unit/test_docs_navigation.py tests/unit/test_phase200_doc_claims.py
HOME="$(mktemp -d)" uv run pytest -q tests/unit/test_docs_navigation.py tests/unit/test_phase200_doc_claims.py
```

These are starting checks, not a substitute for tests of the changed branch.
Workers run only their brief's scoped tests. The orchestrator owns the quiet
full suite. Never run `tests/e2e/test_metal.py`. Frontend changes also need
focused interaction tests and 1440/393 evidence under the current UI charter.

## Traps

Do not erase an unresolved claim by weakening its test. Do not copy mutable secrets, transcripts or owner records into examples.

## Prove completion

Report changed paths, the source-to-assertion trace, exact collected test names,
run outcomes, documentation changes and remaining unknowns. Separate mocked
proof from observed behavior. Workers hold for SHIP; they do not stage or commit.
