# HS-18-02 — Project Context Conventions + Safe Maintenance Contract

- **Project:** holdspeak
- **Phase:** 18
- **Status:** done
- **Depends on:** HS-18-01
- **Unblocks:** HS-18-03
- **Owner:** unassigned

## Problem

Project-aware dictation needs a predictable place to find local context. Without conventions, every repo becomes bespoke and the web UI cannot safely help users maintain memory, issues, or project-specific rewrite preferences.

## Scope

### In

- Define supported project files: `.hs_context`, `.hs_issues`, `.hs_memory`, and/or equivalent files under `.hs/`.
- Define precedence, maximum sizes, parsing rules, and write policy.
- Define what HoldSpeak may read automatically and what requires user confirmation before write.
- Add project-context discovery helpers and tests.
- Document examples for common repo types.

### Out

- Secret scanning beyond basic denylist / file-size protections.
- Hosted memory or synchronization.
- Complex schema migrations.

## Acceptance Criteria

- [ ] Project-context convention documented in product docs.
- [ ] Discovery helper finds context from repo root and nested cwd cases.
- [ ] Oversized files, binary files, and obvious secrets are skipped with visible warnings.
- [ ] Write policy is explicit: automatic, suggested, or manual-only per file type.
- [ ] Tests cover flat dotfiles and `.hs/` directory layouts.

## Test Plan

- Unit tests for discovery, precedence, size limits, and skip reasons.
- Manual test in a throwaway git repo with nested directories.

## Notes

- The first version should be boring and easy to inspect. If users cannot understand a file by opening it in an editor, it is the wrong format.
- 2026-05-10 closeout: canonical `.hs/` layout, read-only flat `.hs_*` compatibility files, precedence, skip warnings, write policy, tests, and docs are covered. See [evidence-story-02.md](./evidence-story-02.md).
