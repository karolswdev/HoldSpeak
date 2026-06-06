# HS-42-05 — Trust & Privacy — ambient chip + panel

- **Project:** holdspeak
- **Phase:** 42
- **Status:** backlog
- **Depends on:** HS-42-01, HS-42-02
- **Unblocks:** none
- **Owner:** unassigned

## Problem

HoldSpeak's local-first posture is a core differentiator, but the truth (what can
leave the machine right now) lives across `doctor`, docs, and several tabs. A panel
you have to remember to visit is the weak version — posture should be **ambient**,
like the Phase-41 presence surface.

## Scope

- In:
  - A persistent **shell header chip** (in the finished HS-42-02 shell) showing the
    current posture: `Local only` / `Configured endpoint` / `Writes need approval` /
    `Needs attention`, color-keyed, reading the `trust{}` block from
    `/api/setup/status`.
  - A full **Trust & Privacy panel** (opened from the chip) answering, in plain
    language with layered disclosure: is the runtime loopback-only? is the auth token
    set? is meeting intel local/cloud/disabled? which OpenAI-compatible endpoint is
    configured? which connector packs are enabled? are actuators enabled, and which
    can write externally? what can leave the machine right now? where do
    DB/config/`.hs` files live?
- Out:
  - Changing any egress behavior or default (display only).
  - New connector/actuator config (read-only view of existing config).

## Acceptance criteria

- [ ] A persistent shell chip shows posture on every route and opens the panel;
      its state maps correctly from `trust{}` (local-only default vs configured
      endpoint vs writes-need-approval) — covered by view-model tests.
- [ ] The panel answers the listed questions in plain language with layered
      disclosure (summary first, details expandable).
- [ ] Status mapping is tested for local / cloud / actuator-enabled /
      connector-enabled permutations.
- [ ] Bundle rebuilt; only `web/src` committed; screenshots of default local-only
      and a configured-endpoint state.
- [ ] Default suite green; default (local-only) posture is byte-identical to today.

## Test plan

- Unit: `tests/unit/test_trust_posture_view_model.py` (status → chip/panel mapping).
- Frontend: `cd web && npm run build && npm run shots`; Playwright for the chip +
  panel in two postures.
- Full: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.

## Notes / open questions

- Reuse `intel_egress_posture()` + the config trust fields surfaced by HS-42-01;
  this story is presentation over that contract.
