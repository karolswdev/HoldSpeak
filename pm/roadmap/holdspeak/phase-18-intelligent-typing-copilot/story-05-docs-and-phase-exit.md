# HS-18-05 — Product Documentation + Phase Exit

- **Project:** holdspeak
- **Phase:** 18
- **Status:** done
- **Depends on:** HS-18-01, HS-18-02, HS-18-03, HS-18-04, HS-18-06
- **Unblocks:** daily-use dogfooding of intelligent typing
- **Owner:** unassigned

## Problem

The product story has changed: HoldSpeak is not only a meeting-intelligence system. It is also a local intelligent typing layer. The documentation, README, and PMO close-out need to make that clear.

## Scope

### In

- User guide sections for intelligent typing, target profiles, agent hooks, optional external-agent summarization, project context, and OpenAI-compatible runtimes.
- README update that positions intelligent typing as a primary surface.
- Final-summary with shipped behavior, remaining gaps, test posture, and recommended next phase.
- Evidence files for all completed HS-18 stories.

### Out

- Marketing site copy.
- Video walkthroughs.
- Documentation for HS-17 hardware work.

## Acceptance Criteria

- [x] User guide explains core workflows in order: install, start runtime, dictate, enable intelligence, configure project context, troubleshoot.
- [x] README points users to the guide and describes intelligent typing without assuming meeting mode.
- [x] Every completed HS-18 story has evidence.
- [x] `final-summary.md` follows roadmap-builder requirements.
- [x] Parent roadmap marks HS-18 done only after evidence and summary exist.

## Test Plan

- Markdown link/path sanity check.
- Fresh-reader review: follow the guide from a clean checkout as far as local environment allows.

## Notes

- Documentation should describe the product users have, not the architecture we wish they inferred from the code.
- 2026-05-10 closeout: user guide, README, final summary, phase status, parent roadmap, broad pytest baseline, web build, and markdown link sanity are covered. See [evidence-story-05.md](./evidence-story-05.md) and [final-summary.md](./final-summary.md).
