# Phase 119 — The Revision

**Status:** in-progress (2/4).

**Last updated:** 2026-08-05.

## The orchestrator

Opus 4.6 implements. Terra verifies against spec. Sol reviews product
feel. The orchestrator makes the done call. This follows the standing
Opus->Terra->Orchestrator pipeline.

## What we're building

Phase 118 shipped the Hopper — nine stories of new capability: the
inlet, @-references, voice drawer resolution, output minting, artifact
triage, sprite states, browser mic pipeline. It shipped forward without
looking sideways. The presence window freezes on "RECONNECTING", the
browser mic is hold-to-talk on a tiny button (hostile UX), the seed
dumps 15+ demo objects onto the desk, and no integration regression was
run against the combined codebase.

This phase stops, looks back, and makes everything work together.

Three pillars:

1. **Click-to-toggle mic with streaming transcription.** The MicButton
   changes from hold-to-talk to click-to-toggle. Click once to start
   listening; real-time streaming transcription fills the field with
   Whisper's progressive corrections; click again (or Enter/Escape)
   to stop. The hold-to-talk hotkey path (system-level) stays
   unchanged. This is the difference between "the browser mic works"
   and "the browser mic is pleasant to use."

2. **Integration regression sweep.** Exercise every existing system
   path against the Phase 118 codebase. WebSocket auth, presence
   detection, meeting recorder, dictation hotkey, workbench conductor,
   kernel codecs, seed, DB migration. Find what broke, fix it,
   prove the fixes.

3. **Seed revision.** Replace the current noisy seed (15+ demo
   objects, seeded flattery) with a curated toolkit baseline: honest
   at zero, ready to configure. Inference target profiles, a starter
   workbench, one or two zones. Not a demo — a toolkit.

Plus the Phase 118 walk (story 10) that couldn't complete because
integrations were broken. This phase's walk covers both 118 and 119.

## Why this phase exists

1. **The mic UX gap.** The browser mic shipped as hold-to-talk: press
   and hold a small button, speak, release. This works for short
   commands but fails for anything longer than a few words. The user's
   hand cramps, their attention splits between holding and speaking,
   and there is no visual feedback that the system is hearing them.
   Click-to-toggle with streaming transcription is the minimum bar
   for a voice-first surface.

2. **The integration gap.** Phase 118 shipped nine stories of new
   capability without running a regression sweep across existing
   systems. The presence window freezes. Unknown breakages may lurk
   in the WebSocket handshake, meeting recorder, dictation hotkey,
   conductor scheduling, or kernel codec paths. Shipping forward
   without looking sideways is debt with compound interest.

3. **The seed gap.** The current seed dumps 15+ demo objects — sample
   meetings, fake notes, placeholder zones — onto the desk. This
   violates Article VI (honest by construction — no demo state, no
   seeded flattery). A new user's desk should be honest at zero:
   empty except for the tools they need to start configuring their
   own workspace.

4. **The walk gap.** Phase 118's walk (story 10) couldn't complete
   because integrations were broken. The proof was deferred. This
   phase completes it.

## Method

- Fix first, features second. The regression sweep (story 02) runs
  before the mic upgrade (story 01) ships, so fixes land on a stable
  baseline. (Article IX — proof over claim.)
- The MicButton toggle is a state machine, not a mode. Idle ->
  listening -> idle. The hold-to-talk hotkey path is unmodified.
  (Article IV — voice as input; one mic authority at a time.)
- The seed is a toolkit, not a demo. Honest at zero, ready to
  configure. No seeded flattery, no placeholder content.
  (Article VI — honest by construction.)
- Streaming transcription uses progressive Whisper partials so the
  user sees their words as they speak — corrections arrive in-place.
  (Article VIII — native-grade craft; Article IV — voice as input.)
- The walk proves on the real hub with real mic, real model, real
  viewport. Screenshots for static state, video for streaming
  transcription. (Article IX — honest proof.)
- Every surface that uses MicButton inherits the toggle automatically.
  No surface is special-cased.
  (Article II — everything is a primitive.)

## Dependency graph

```
02 regression sweep ──→ 01 click-to-toggle mic
                    ──→ 03 seed revision

01, 02, 03 ──→ 04 the walk
```

## Stories

### The fix

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 01 | Click-to-toggle mic | Why should the browser mic require holding a button? | backlog |
| 02 | Integration regression sweep | What broke when Phase 118 landed? | backlog |

### The baseline

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 03 | Seed revision | Why does the desk start noisy instead of ready? | backlog |

### The proof

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 04 | The walk | Does everything work together? | backlog |

## Story status

| ID | Story | Status | Story file | Evidence |
|----|-------|--------|------------|----------|
| HS-119-01 | Click-to-toggle mic | backlog | [story-01](story-01-click-to-toggle-mic.md) | -- |
| HS-119-02 | Integration regression sweep | done | [story-02](story-02-integration-regression-sweep.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-119-03 | Seed revision | done | [story-03](story-03-seed-revision.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-119-04 | The walk | backlog | [story-04](story-04-the-walk.md) | -- |

## Where we are

Stories 02 and 03 are done. The regression sweep found and fixed 5
regressions (HS-119-02). The seed revision replaced the noisy 15+
object demo with a toolkit baseline: 5 inference profiles (3 local
tiers + 2 cloud placeholders), 1 starter workbench wired to the
local resolver, 2 empty zones. No demo content, no seeded flattery
(Article VI). Story 01 (click-to-toggle mic) is next.
