# Evidence — HS-69-09: Generation theater (orb + constellation)

**Date:** 2026-06-30
**Verdict:** done. The cockpit gains the iPad's "model thinking" set-piece —
the plasma orb + concentric rings + the artifact-type constellation — driven by
the live meeting-intelligence WS frames. Proven in the UI and on real metal.

## What shipped

- **`web/public/theater/theaterorb.png`** — the SAME PixelLab orb the iPad uses
  (`apple/App/theaterorb.png`), reused verbatim (true convergence, no regen).
- **`web/src/components/GenerationTheater.astro`** — a centred, non-blocking
  theater: the orb (spin + breathe) over a vibrant accent backlight + three
  expanding rings, a status label, and the constellation (Summary / Decisions /
  Actions / Topics). Mounted in AppLayout; `is:global` (JS-toggled). Auto-hides.
- **`web/src/scripts/theater.js`** — subscribes on the shared runtime-bus to the
  intel frames that ALREADY flow (no backend change):
  - `intel_status {state}` — reveal while generating (queued / live /
    initializing / running), hold + label "ready", hide on ready/error/disabled.
  - `intel_token` (string chunks) — the streaming heartbeat: `.is-streaming`
    pulses the orb + rings faster.
  - `intel_complete` (the snapshot) — lights the constellation nodes for the
    artifact types actually produced (`summary` / `action_items` / `topics` /
    `decisions`), staggered.
  The frame shapes were read from the real backend
  (`meeting_session/session.py`, `intel_analysis.py`, `intel/models.py`), not
  guessed.

## Proof — the UI (simulated frames)

`scripts/screenshot_phase69_theater.py` drives `window.__hsTheater` through the
lifecycle on a real server:
- **`screenshots/theater-streaming.png`** — revealed, "THINKING…", the orb
  glowing brighter (streaming), the constellation still dim.
- **`screenshots/theater-card.png`** / **`theater-complete.png`** — "INTELLIGENCE
  READY", the orb settled in its accent halo, **all four constellation nodes
  lit** (`lit nodes: 4`).

## Proof — real metal

`scripts/theater_realmetal_proof.py` drives the **actual** `MeetingIntel`
pipeline against a real LAN endpoint and captures the real output the theater
visualizes (`theater-realmetal-transcript.txt`). The owner's clean `.13`
llama-server was down this session, so it ran on `.43` (Qwythos-9B):

```
summary: 'The team agreed on a token bucket per API key rate limiter design with a
          feature flag for gradual rollout. Bob will wire the flag by Friday. They
          also settled on Postgres as the primary store ...'
action_items: 2
topics: ['Rate limiter design', 'Feature flag', 'Service name', 'Database']
constellation nodes that would light: ['summary', 'actions', 'topics']
```

So the **real** intel snapshot (an accurate summary + 2 actions + 4 topics)
lights three constellation nodes — the theater's `intel_complete` path is proven
on real metal with real LLM content. Honest gap: `.43` returned the result
**buffered** (0 `intel_token` chunks), so the orb's token-pulse (`.is-streaming`)
was not exercised on real metal there; the theater reveals on `intel_status`
regardless (graceful), and the proof script re-runs against the streaming `.13`
endpoint when it is up.

## Tests

Build green (orb in the bundle); frontend density guard + route pre-flight
(every page loads with zero errors, so the theater's shell mount + script parse)
= 7 passed.
