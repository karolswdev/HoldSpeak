# HS-42-05 — Trust & Privacy — ambient chip + panel

- **Project:** holdspeak
- **Phase:** 42
- **Status:** done (2026-06-06)
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

- [x] A persistent shell chip shows posture on every route (TopNav default) and
      opens the panel; its state maps correctly from `trust{}` (local · configured
      endpoint · writes-need-approval · needs-attention) — a Node harness (5 cases)
      + a live two-config Playwright check.
- [x] The panel answers the listed questions in plain language (web bind/auth,
      egress + endpoint, actuators, webhook hosts, presence) with a Settings link.
- [x] Status mapping tested for local / cloud / actuator / off-loopback
      permutations (harness + the HS-42-01 `trust{}` data tests).
- [x] Bundle rebuilt; only `web/src` committed; screenshots of default local-only
      and a configured-endpoint state.
- [x] Default suite green; the local-only posture is the honest server-rendered
      default.

## Test plan

- Unit: `tests/unit/test_trust_posture_view_model.py` (status → chip/panel mapping).
- Frontend: `cd web && npm run build && npm run shots`; Playwright for the chip +
  panel in two postures.
- Full: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.

## Notes / open questions

- Reuse `intel_egress_posture()` + the config trust fields surfaced by HS-42-01;
  this story is presentation over that contract.
