# HS-69-07 — The Queue HUD (shell + store)

- **Status:** done
- **Priority:** HIGH (glanceable always-on)
- **Depends on:** HS-69-02
- **Catalog pattern(s):** §3 Queue HUD
- **Evidence:** [evidence-story-07.md](./evidence-story-07.md)

## Goal

A Dynamic-Island-style collapsed pill under the nav that expands into a live
per-job ledger, present on every page — the web's missing RunQueueStore + the
floating shell, fed by the shared runtime-bus (no backend message-type change).

## Done

Shipped in the substrate wave: `runtime-bus.js` (the shared WS bus) +
`queue-hud.js` (the store + render) + `QueueHud.astro` (mounted in AppLayout).
Jobs are derived from the `intel_status` / `runtime_activity` frames that already
flow; the collapsed pill expands into a per-job ledger of signal-card rows. See
the evidence file. Honest gaps (in the module's own header): indeterminate
progress (no per-job %), two derivable concurrent jobs.
