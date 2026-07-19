# HS-100-05 — B1: the vocabulary guard

- **Project:** holdspeak
- **Phase:** 100
- **Status:** done
- **Depends on:** HS-100-04
- **Unblocks:** HS-100-06

## Problem

The glass speaks banned words ("Personas", "Intel model not found")
and one refusal leaks an absolute filesystem path (UIUX_JUDGMENT §5.5).
Canon vocabulary must be mechanical, like the token gate.

## Scope

- In:
  - `tests/unit/test_web_vocabulary_guard.py`: scans web/src user-facing
    string literals for canon-banned words (intel, persona/Personas as
    user-facing nouns) and for absolute-path leakage in refusal copy;
  - a shrink-only allowlist seeded with today's offenders (the token-gate
    pattern) so the guard lands green and B3–B7 burn it down to zero;
  - the AskPanel refusal fixed NOW: names the fix ("pick a model in
    Settings"), never prints a filesystem path.
- Out: the surface renames (B5 shrinks the allowlist).

## Acceptance criteria

- [ ] Guard green with a seeded allowlist that only shrinks.
- [ ] The ask refusal names its fix and carries no path.

## Test plan

- `uv run pytest -q tests/unit -k vocabulary`; vitest on the refusal copy
  if a component test exists for AskPanel.

## Evidence required

- Guard output; the refusal's before/after.
