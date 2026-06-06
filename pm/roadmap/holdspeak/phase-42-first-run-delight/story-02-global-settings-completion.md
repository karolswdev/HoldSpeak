# HS-42-02 — Global settings completion

- **Project:** holdspeak
- **Phase:** 42
- **Status:** done (2026-06-06)
- **Depends on:** none (sequenced early so later surfaces land on a clean shell)
- **Unblocks:** HS-42-03, HS-42-05
- **Owner:** unassigned

## Problem

`web/src/layouts/AppLayout.astro` still ships an **interim** Settings drawer:
*"Global settings are consolidating here… The full move from History → Settings
lands in HS-30-08. Until then, manage settings there: Open History → Settings."*
There is no real `/settings` route. This was IA debt in Phase 30; with the
settings + trust surfaces added since, it's now live **product debt** that makes
the shell feel unfinished — and the first-run surfaces would otherwise land on top
of it.

## Scope

- In:
  - A real global settings surface — a `/settings` route (and/or a finished shell
    drawer) opened from the gear — hosting the genuinely-global settings
    (appearance, core runtime, cloud-intel config) that the interim copy promised.
  - **Delete** the interim "consolidating / History → Settings / HS-30-08" copy and
    the back-link to History.
  - Keep page-local settings where they are truly page-local (e.g. the `/dictation`
    Copilot-depth cockpit stays on `/dictation`).
  - Preserve the `#settings` deep link (keep it working or replace with a stable
    route) so existing links don't dangle.
- Out:
  - New settings fields / new config knobs (presentation/IA only).
  - The trust chip (HS-42-05) — though this story lands the shell header slot it
    will occupy.

## Acceptance criteria

- [x] A real global-settings surface (`/settings`) exists and is reachable from
      every route via the shell gear; page-local settings unchanged.
- [x] **No live product copy** has the interim-drawer markers (`consolidating` /
      `settings-interim` / `data-settings-open`) — guarded by a test.
- [x] The `#settings` deep link still resolves (redirects to `/settings`).
- [x] Bundle rebuilt; only `web/src` committed (no `_built/`); a **Playwright
      round-trip** confirms set→save→reload→disk; screenshot captured.
- [x] Default suite green; existing settings round-trips unchanged (same
      `/api/settings` contract).

## Test plan

- Page-surface / integration: the settings route or drawer entry resolves and
  renders the global settings.
- Guard: the `rg` interim-copy check (could become a small doc/markup test).
- Frontend: `cd web && npm run build && npm run shots`.
- Full: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.

## Notes / open questions

- Decide route vs drawer: a dedicated `/settings` page is cleaner for deep links and
  for the trust chip's "open settings" target; a drawer keeps context. Default to a
  `/settings` route with the gear opening it, preserving `#settings`.
