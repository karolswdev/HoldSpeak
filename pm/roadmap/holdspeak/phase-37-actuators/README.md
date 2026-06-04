# Phase 37 — Actuators

**Status:** not-started (teed up; renumbered from Phase 36 when the meeting-artifact
UX phase took the 36 slot, 2026-06-04).

The plugin system's third kind. Today the host's `actuator` kind is **blocked**
(`plugin_sdk.validate_manifest` rejects it as deferred). Phase 35 built the
groundwork — the public authoring guide, the pack manifest + discovery loader, and the
capability model. This phase turns actuators on: a plugin that, instead of producing a
read-only artifact, proposes an **external side effect** (file a ticket, post a
message, open a PR, …) behind a **preview → human approval → execute** flow.

This is the RFC's open question #5 and it **intersects the Phase-25 egress posture**
(no silent cloud egress; approval + audit before any outbound action), so it is its own
phase rather than a tail of Phase 35.

## When opening this phase

- Ground it in `docs/internal/PLAN_ARCHITECT_PLUGIN_SYSTEM.md` (the parent RFC) and the
  Phase-25 trust/egress decisions.
- Reuse the Phase-35 pack/manifest/capability contract; the `actuator` kind gate in
  `holdspeak/plugin_sdk.py` is the seam to unblock.
- Scaffold `current-phase-status.md` + stories per `pm/roadmap/roadmap-builder.md`.
