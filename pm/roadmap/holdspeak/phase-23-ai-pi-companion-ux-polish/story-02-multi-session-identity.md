# HS-23-02 — Multi-Session Identity Model

- **Status:** done
**Opened:** 2026-05-26.
**Closed:** 2026-05-26.
**Owner:** Codex.

## Problem

Phase 22 proved that AI PI can help answer a waiting local agent, and HS-23-01
made long questions readable. The next trust problem is identity: if two Codex
sessions and one Claude session are active, the user needs to know exactly which
session is waiting and where their spoken answer will land.

Without a stable identity model, even correct routing can feel unsafe.

## Outcome

HoldSpeak and the bridge expose a compact, deterministic identity for each
waiting agent session. AI PI can show a short label that distinguishes sessions,
and richer web/debug surfaces can use the same fields without inventing a
parallel naming scheme.

## Scope

### In

- Define the identity fields that matter for agent sessions:
  - agent name;
  - project/repo label;
  - cwd/repo root;
  - tmux session/window/pane when known;
  - session freshness;
  - answer transport/confidence.
- Add a compact display label suitable for the AI PI middle zone.
- Add a richer structured identity payload for `/api/companion/status` or the
  bridge adapter.
- Cover fallback behavior when tmux metadata is missing.
- Add tests for Codex/Claude, same-project multi-session, and missing metadata
  cases.

### Out

- Device browse controls. That belongs to HS-23-03.
- Web companion panel UI. This story may shape the data contract, but not build
  the full panel.
- Direct Claude/Codex API transport.
- Autonomous replies.

## Acceptance Criteria

- [x] Agent sessions have a stable compact identity label that can fit on AI PI.
- [x] Same-agent/same-project sessions remain distinguishable when tmux metadata
      exists.
- [x] Missing tmux metadata degrades visibly instead of pretending confidence is
      high.
- [x] Companion status or bridge adapter exposes structured target confidence.
- [x] Tests cover multi-session identity, missing metadata, and display-label
      formatting.
- [x] Evidence records the chosen identity rules before this story is marked
      done.

## Implementation Notes

Prefer deriving identity from existing hook metadata first. The model should not
require a new agent-side protocol if Codex/Claude hooks already provide enough
facts.

Initial compact label candidate:

```text
Codex | HoldSpeak | work:2.1
```

Fallback candidates:

```text
Codex | HoldSpeak | no tmux
Claude | /repo/path | low confidence
```

The key product distinction is between "display identity" and "answer target":
HS-23-02 defines the naming/confidence model; HS-23-03 can use it for browse
and selection controls.

## Closeout

Implemented 2026-05-26. See [evidence-story-02.md](./evidence-story-02.md).
