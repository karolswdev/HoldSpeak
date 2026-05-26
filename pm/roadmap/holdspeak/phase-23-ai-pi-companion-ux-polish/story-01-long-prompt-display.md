# HS-23-01 — Long Prompt Display And Marquee/Window Contract

- **Status:** done
**Opened:** 2026-05-26.
**Closed:** 2026-05-26.
**Owner:** Codex.

## Problem

Phase 22 proved the local agent loop, but the LCD frequently truncates the most
important part of an agent question. A clipped `...` is not just ugly; it can
make the user unsure what they are answering. The device needs a display
contract for long prompts that preserves confidence without pretending the LCD
is a full transcript viewer.

## Outcome

AI PI can show long Claude/Codex questions in a way that is understandable on a
small display. The user can identify the agent/session, see enough of the
question to decide whether to answer, and avoid confusing stale or clipped text
for the active target.

## Scope

### In

- Define display modes for agent questions:
  - compact identity label;
  - short question preview;
  - long-question marquee or windowed/paged text;
  - stale marker.
- Decide what text is shown in each AI PI zone when an agent is waiting.
- Keep display behavior deterministic and bridge-testable.
- Add tests for long prompt formatting and state transitions.
- Record live-device observations if hardware is available during the story.

### Out

- Multi-session browsing beyond the display primitives. That belongs to
  HS-23-02 and HS-23-03.
- Direct Claude/Codex API transport.
- Autonomous answers.
- Cross-network transport.

## Acceptance Criteria

- [x] Long agent questions do not render as ambiguous clipped text ending in
      unexplained `...`.
- [x] The visible display state always includes a stable agent/project/session
      label when available.
- [x] The display contract distinguishes preview text from full-question
      scrolling/windowing.
- [x] Stale waiting-agent state is visibly marked or cleared according to a
      documented rule.
- [x] Bridge-side tests cover long, short, stale, and missing-question cases.
- [x] Phase 23 status docs and evidence are updated before this story is marked
      done.

## Implementation Notes

Start in the bridge companion formatting layer, not firmware. The firmware
should remain a simple renderer of status strings and gesture signals. If the
existing firmware marquee behavior is good enough, use it through bridge status
text before adding any new firmware surface.

The core design question is whether long questions are:

- marquee-scrolled continuously;
- shown as timed windows;
- paged by gesture;
- or summarized into a short preview with optional full display mode.

Prefer the smallest behavior that makes the live agent loop trustworthy.

## Evidence Plan

Use `evidence-story-01.md` when closing this story. Include:

- relevant bridge/unit test commands and output;
- at least one sample long Codex/Claude question payload;
- before/after display behavior;
- live-device notes if tested on AI PI.

## Closeout

Closed in [evidence-story-01.md](./evidence-story-01.md). Long questions now
render as deterministic `[N/M]` windows and advance on companion polls. The
device-facing middle text uses a stable identity line plus question window
instead of one clipped sentence with a trailing ellipsis.
