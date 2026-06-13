# Phase 66 — The Architecture Map: final summary

**Closed:** 2026-06-13 on owner direction (a dedicated phase for pipeline
architecture and Mermaid diagrams). 4/4 stories.

## What shipped

`docs/ARCHITECTURE.md`, the runtime map the repo never had, with six
Mermaid diagrams that render on GitHub and are kept rendering by a guard:

1. The top-level **component map** (how the subsystems connect).
2. The **dictation flow** (entries, transcribe, the voice-command branch,
   the opt-in stages, the wake preview-default fork, type, journal).
3. The **learning loop** (journal, one-tap correction, correction memory,
   replay).
4. The **device path** (the ESP32-S3 board over the device WebSocket, with
   the agent-reply branch).
5. The **meeting pipeline** (capture/import through artifacts and aftercare
   to the two approve-gated proposals).
6. The **trust boundary** (a "Your machine" box with all seven egress
   crossings labeled by their gate).

Every diagram was traced against the shipped, post-decomposition code (real
module names, opt-in paths marked), and the trust boundary was checked
one-to-one against SECURITY's egress table. The map is wired into the docs
index, the README, and CONTRIBUTING.

## The guard

`tests/e2e/test_mermaid_renders.py` renders every fenced ```mermaid block
in the docs via mmdc and fails on any that does not, with the file and
block index. CI-skippable (no browser), green locally, with a canary so it
cannot pass vacuously if the diagrams disappear. Proven both ways. The
principle: a diagram that does not render is worse than no diagram.

## Numbers

- Suite: **2779 passed, 17 skipped** (+2, the guard).
- 4 commits, one per story, plus the scaffold; PR merged on green.

## Honest notes

- GitHub is the canonical renderer (the owner chose GitHub-rendered over
  teaching the Astro docs site to render Mermaid; that remains an optional
  future follow-up).
- The map is a snapshot; it lives next to the code, and the render guard
  protects syntax, not accuracy. When a pipeline changes, the diagram is a
  doc to update like any other.
