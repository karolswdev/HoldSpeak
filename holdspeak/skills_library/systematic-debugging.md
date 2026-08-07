---
name: systematic-debugging
description: "4-phase root cause debugging: reproduce, isolate, diagnose, verify fix."
version: 1.0.0
source: "Adapted from Hermes Agent systematic-debugging skill (MIT)"
tags: [debugging, troubleshooting, root-cause]
---

# Systematic Debugging

## Core principle

ALWAYS find root cause before attempting fixes. A fix without root cause is a gamble.

## Phase 1: Reproduce

- Establish the exact steps to trigger the bug.
- Document: expected behavior vs actual behavior.
- If you can't reproduce it, say so — don't guess.

## Phase 2: Isolate

- Narrow down: which component, which input, which state.
- Binary search: remove half the system, does the bug survive?
- Find the smallest reproduction case.

## Phase 3: Diagnose

- Read the code path the reproduction case exercises.
- Form a hypothesis for WHY the bug occurs, not just WHERE.
- Verify the hypothesis explains ALL observed symptoms.

## Phase 4: Verify fix

- Fix the root cause, not a symptom.
- Confirm the original reproduction case passes.
- Check for regressions — did the fix break anything adjacent?
- If the fix is complex, explain WHY this fix is correct.

## Rules

- Never skip straight to Phase 4. A fix without phases 1-3 is untested.
- If Phase 2 takes too long, report what you've eliminated and ask for guidance.
- Log your reasoning at each phase — future debuggers will thank you.

## Attribution

Adapted from the Hermes Agent project (NousResearch, MIT License).
