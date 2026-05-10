# HS-18-04 — OpenAI-Compatible Runtime Support for Rewriters

- **Project:** holdspeak
- **Phase:** 18
- **Status:** done
- **Depends on:** existing dictation plugin/runtime configuration
- **Unblocks:** HS-18-05
- **Owner:** unassigned

## Problem

Users should not have to run one blessed local llama.cpp package for intelligent dictation. Many local and LAN runtimes expose OpenAI-compatible APIs; HoldSpeak should support those endpoints for rewrite/context flows with clear fallback behavior.

## Scope

### In

- OpenAI-compatible endpoint configuration for dictation intelligence flows.
- Provider probe or dry-run that validates URL, model, auth header behavior, and response shape.
- Timeout and fallback rules: if rewrite fails or is too slow, inject the original transcript.
- Documentation for known-good endpoint families.

### Out

- Vendor-specific advanced tuning UI.
- Streaming rewrite responses.
- Cloud account management.

## Acceptance Criteria

- [x] Runtime config supports an OpenAI-compatible endpoint, model name, optional API key, and timeout.
- [x] Rewriter calls use the configured endpoint and fall back safely on failure.
- [x] Tests cover success, timeout, malformed response, and disabled-provider cases.
- [x] Docs explain how to point HoldSpeak at llama.cpp or another OpenAI-compatible service.

## Test Plan

- Unit tests with mocked HTTP responses.
- Integration-style test against a local fake OpenAI-compatible server.
- Manual smoke test with the user's available local endpoint if present.

## Notes

- Compatibility means "works with the common chat/completions shape," not "supports every OpenAI API feature."
- 2026-05-10 closeout: runtime config, fallback behavior, fake-server contract tests, docs, and web build are covered. See [evidence-story-04.md](./evidence-story-04.md).
