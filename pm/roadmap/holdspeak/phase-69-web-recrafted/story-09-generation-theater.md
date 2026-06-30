# HS-69-09 — Generation theater (orb + constellation)

- **Status:** done
- **Priority:** MED (high wow, lower frequency)
- **Depends on:** HS-69-02; a web `theaterorb` asset
- **Catalog pattern(s):** §4 theater, §9 (orb asset)
- **Evidence:** [evidence-story-09.md](./evidence-story-09.md)

## Goal

The "model thinking" set-piece: a plasma orb breathing inside concentric rings,
with an artifact-type constellation lighting up as meeting intelligence is
produced — driven by live intel WS frames.

## Scope

- Reuse the iPad's `theaterorb.png` on the web (true convergence, no regen).
- A theater overlay driven by the intel frames that already flow (no backend
  change): `intel_status` reveals/hides, `intel_token` pulses the orb,
  `intel_complete` lights the constellation for the produced types.
- Mounted in AppLayout; non-blocking; auto-hides when intelligence is ready.

## Proof required

The orb breathing/rotating + the constellation lighting per artifact, driven by
live intel; proven on **real metal** (a real intel run), not a no-LLM stub.

## Done

Shipped and proven. UI: simulated frames drive the full lifecycle — the
streaming "THINKING…" state (bright orb) and the "INTELLIGENCE READY" state with
all four constellation nodes lit (`theater-streaming.png`, `theater-card.png`).
Real metal: the actual `MeetingIntel` pipeline run against `.43` produced a real,
accurate snapshot (a correct summary + 2 action items + 4 topics → three
constellation nodes light) — the exact `intel_complete` content the theater
consumes. The owner's clean `.13` endpoint was down; `.43` returned the result
buffered (0 `intel_token` chunks), so the orb's token-pulse wasn't exercised
there — the theater reveals on `intel_status` regardless, and the ready
`theater_realmetal_proof.py` re-runs against `.13` when it is up. Build + route
pre-flight green (7 passed).
