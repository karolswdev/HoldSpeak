---
name: systematic-task-processing
description: "Break tasks into steps, execute in order, verify each before proceeding."
version: 1.0.0
source: "Adapted from Hermes Agent plan skill (MIT)"
tags: [planning, execution, verification]
---

# Systematic Task Processing

## Method

1. **Decompose** the task into concrete, verifiable steps.
2. **Order** steps by dependency — what must complete before the next can start.
3. **Execute** each step fully before moving to the next.
4. **Verify** each step's output against its acceptance criteria before proceeding.
5. **Report** what was done, what was verified, and what remains.

## Rules

- Never skip verification. A step is not done until its output is checked.
- If a step fails verification, stop and report — do not continue with bad state.
- Each step's output should be independently useful, not dependent on later steps succeeding.
- State dependencies explicitly: "Step 3 requires the output of Step 2."

## Attribution

Adapted from the Hermes Agent project (NousResearch, MIT License).
