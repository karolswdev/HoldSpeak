# HS-18-03 — Web Cockpit for Intelligent Typing and Project Context

- **Project:** holdspeak
- **Phase:** 18
- **Status:** done
- **Depends on:** HS-18-01, HS-18-02
- **Unblocks:** —
- **Owner:** unassigned

## Problem

Intelligent typing cannot be configured only through hidden dotfiles and CLI flags. Users need to see which target profile is active, which project context is loaded, how hooks are configured, and what rewrite behavior will happen before text is injected.

## Scope

### In

- Dictation page status for target profile, active project, hook freshness, and rewriter runtime.
- Project context viewer/editor for supported `.hs` files, respecting the write policy from HS-18-02.
- Setup panel for agent hooks with copy-ready snippets and detected status.
- Clear affordances for disabling context injection or rewrite behavior.

### Out

- Full IDE-style project browser.
- Editing arbitrary repo files.
- Multi-user admin settings.

## Acceptance Criteria

- [x] Web UI exposes hook status and captured target/project context.
- [x] Web UI can view supported project-context files and edit only files permitted by policy.
- [x] UI makes rewrite/context-injection mode visible before dictation is started.
- [x] API tests cover project-context read/write/skip behavior.
- [x] Web build and regression tests pass.

## Test Plan

- API tests for context file read/write endpoints.
- Web build.
- Manual runtime pass on the Dictation page with a throwaway repo.

## Notes

- The UI should explain status in product language: "Using context from this repo" is better than "profile detector confidence: 0.83".
- 2026-05-10 closeout: Readiness now shows target profile and hook freshness, Project Context respects HS-18-02 flat/canonical write policy, Runtime exposes the rewrite stage toggle, and evidence is recorded in [evidence-story-03.md](./evidence-story-03.md).
