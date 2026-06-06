# HS-43-04 — Presence as a UI toggle (kill the env var)

- **Project:** holdspeak
- **Phase:** 43
- **Status:** done (2026-06-06)
- **Depends on:** HS-43-01

## Problem
Desktop presence is gated **only** by `HOLDSPEAK_DESKTOP_PRESENCE=1` — no config
field, no UI toggle. Making a user set an env var + relaunch from a terminal to
enable a flagship feature is the single worst UX wart in the product.

## Scope
- In: a `config` field (e.g. `presence.enabled`) so presence is **config-backed**;
  `desktop_presence_enabled()` reads config OR the env override; a real **toggle**
  in the wizard's Presence step (+ Settings) that persists via `/api/settings`,
  with an honest "takes effect now / on relaunch" note and a live HUD preview. The
  env var stays as a power-user/headless override, not the only path.
- Out: turning presence on by default; new renderers.

## Acceptance criteria
- [x] Presence is enabled from the UI (config-backed via `/api/settings`); the env
      var is no longer the only path (retained as an override); default-off
      byte-identical; live start/stop; covered by 7 tests + a screenshot.
