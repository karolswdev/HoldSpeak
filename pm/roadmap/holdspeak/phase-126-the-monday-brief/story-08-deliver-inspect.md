# HS-126-08 — Deliver and inspect

- **Project:** holdspeak
- **Phase:** 126
- **Status:** backlog
- **Depends on:** HS-126-07
- **Unblocks:** HS-126-09
- **Owner:** unassigned

## The thesis (the bar)

A brief earns attention only when it is available where the owner works and
can be acted on without losing its provenance. Deliver one persisted brief to
the desk, browser speech, FastAPI, and MCP; every surface reads the same
receipt.

### What changes

1. Add a Monday Brief pullout to the desk with fixed sections and source links.
2. Speak the headline through the browser Speech API and record its spoken state.
3. Add acknowledge, defer, and open-source actions, persisting disposition.
4. Add `monday_brief.get` and `holdspeak://briefs/latest`.
5. Add a FastAPI endpoint for reading the latest brief and applying supported
   delivery actions.

## Acceptance criteria

1. The pullout renders the latest persisted brief and opens each source item.
2. Headline speech uses the browser API only after an eligible user interaction
   and does not re-speak an already spoken brief unintentionally.
3. Acknowledge and defer persist and remain visible after reload.
4. The MCP tool, MCP resource, and FastAPI endpoint return the same brief.
5. Missing briefs return an explicit, non-fabricated empty/not-found result.

## Test plan

- Unit: read and action endpoints update only the intended persisted brief.
- Unit: MCP tool and resource serialize the latest brief consistently.
- Browser: assert pullout actions and guarded speech behavior with mocked speech.
- Integration: compare desk API and MCP representations of one generated brief.
