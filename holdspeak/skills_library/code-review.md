---
name: code-review
description: "Security scan, quality gates, independent reviewer perspective."
version: 1.0.0
source: "Adapted from Hermes Agent requesting-code-review skill (MIT)"
tags: [code-review, security, quality]
---

# Code Review

## Method

Review code changes across these dimensions, in order:

1. **Security** — Injection vectors, auth bypasses, secret exposure, OWASP top 10.
2. **Correctness** — Does the code do what it claims? Edge cases, off-by-ones, null handling.
3. **Design** — Is this the right abstraction? Could it be simpler? Does it fit the codebase style?
4. **Performance** — N+1 queries, unbounded allocations, missing indexes, hot-path overhead.
5. **Tests** — Are the changes tested? Are the tests testing the right thing?

## Output format

For each finding:
- **File:line** — one-sentence finding
- **Severity**: critical / important / suggestion
- **Fix**: what to change (be specific)

## Rules

- Lead with blockers. Don't bury a security issue under style nits.
- Be specific: "line 42 has an SQL injection via unsanitized user input" not "watch out for injection."
- No agent verifies its own work. If you wrote the code, you cannot review it.
- Praise good patterns — reviews aren't just about finding faults.

## Attribution

Adapted from the Hermes Agent project (NousResearch, MIT License).
