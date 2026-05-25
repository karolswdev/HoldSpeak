# HS-19-01 — Local LLM Project Documentation Suggestions

- **Project:** holdspeak
- **Phase:** 19
- **Status:** done
- **Depends on:** HS-18-04, HS-18-05
- **Unblocks:** HS-19-02
- **Owner:** unassigned

## Problem

Project-aware dictation can improve a single prompt, but the bigger win is continuity. When a user and coding agent establish reusable context, HoldSpeak should help preserve that context as small Markdown documentation suggestions without silently mutating the repo.

## Scope

### In

- Local/OpenAI-compatible runtime prompt for one narrow project documentation suggestion.
- Safe target path validation under `.hs/memory`, `.hs/decisions`, `.hs/handoffs`, `.hs/workflows`, or `.hs/issues`.
- Secret-looking content rejection.
- ProjectRewriter integration for Codex/Claude target profiles.
- Fail-open behavior: invalid output or runtime failure yields no suggestion.

### Out

- Automatically writing files.
- Web apply/dismiss flow.
- Suggestions for generic browser/editor typing.
- Multi-file planning.

## Acceptance Criteria

- [x] Suggestion parser accepts safe narrow `.hs/.../*.md` paths and rejects broad/unsafe paths.
- [x] Suggestion generator uses a rewrite-capable local runtime and accepts `NO_SUGGESTION`.
- [x] Coding-agent rewrites can append a context-preservation suggestion.
- [x] Generic targets do not receive suggestions.
- [x] Tests cover safe suggestion, no suggestion, unsafe paths/content, and ProjectRewriter injection.

## Test Plan

- Unit tests for `holdspeak.project_doc_suggestions`.
- Unit tests for `ProjectRewriter` suggestion injection and target gating.

## Notes

- Product rule: HoldSpeak proposes; user/agent writes.
- 2026-05-10 closeout: safe suggestion parser/generator, Codex/Claude ProjectRewriter injection, generic-target gating, and tests are covered. See [evidence-story-01.md](./evidence-story-01.md).
