---
name: test-driven-approach
description: "Write the test first, watch it fail, write minimal code to pass."
version: 1.0.0
source: "Adapted from Hermes Agent test-driven-development skill (MIT)"
tags: [testing, tdd, verification]
---

# Test-Driven Approach

## Method

1. **Write the test** that describes the expected behavior.
2. **Run it** — confirm it fails for the right reason (not a syntax error).
3. **Write the minimal code** to make the test pass.
4. **Refactor** — clean up while keeping the test green.

## Rules

- The test comes BEFORE the implementation, not after.
- Each test should test ONE behavior, not a chain of behaviors.
- Tests should be deterministic — no flaky tests, no time-dependent assertions.
- Test names describe the behavior: `test_expired_token_returns_401`, not `test_auth`.
- Mock external dependencies, not internal logic.

## When to skip TDD

- Exploratory prototyping (but write tests before merging).
- Pure UI layout changes (visual verification > unit tests).
- Configuration changes with no logic.

## Attribution

Adapted from the Hermes Agent project (NousResearch, MIT License).
