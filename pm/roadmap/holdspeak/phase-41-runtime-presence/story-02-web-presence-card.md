# HS-41-02 — Web presence card (zero-dep surface)

- **Project:** holdspeak
- **Phase:** 41
- **Status:** done (2026-06-05)
- **Depends on:** HS-41-01
- **Unblocks:** HS-41-03
- **Owner:** unassigned
- **Evidence:** [evidence-story-02.md](./evidence-story-02.md)

## Problem

The first visible win, with **no new dependencies**: surface the runtime activity
in the web dashboard so a user with the dashboard open sees live state. Also the
data source the desktop HUD webview will reuse.

## Scope

- In:
  - Wire `RuntimeActivityTracker` into `web_runtime`: map the dictation + meeting
    lifecycle events to activity states; broadcast `runtime_activity` over the
    existing websocket; include the snapshot in the runtime status payload.
  - A Signal-styled **presence card** on the dashboard (`web/src/pages/index.astro`
    + `dashboard-app.js`) — salvage the codex card (tokens-only; pulsing ring,
    state tone, label/detail, `aria-live`). Empty/idle state handled.
  - Tests for the mapping + the broadcast + the card markup.
- Out:
  - The desktop renderers + the `/presence` route (HS-41-03+).

## Acceptance criteria

- [x] Dictation/meeting lifecycle drives `runtime_activity` broadcasts; the
      dashboard card reflects state live.
- [x] Rich Signal (not flat); off-by-default behavior unchanged when no activity.
- [x] Bundle rebuilt; no `_built/` staged; screenshot captured.

## Outcome

`web_runtime` maps the full dictation + meeting lifecycle into the
`runtime_activity` contract, snapshots it on `/api/state`, and broadcasts
`runtime_activity` over the websocket; the dashboard renders a live Signal
presence card (pulsing ring keyed to tone, label/detail, aria-live,
reduced-motion guard). Zero new deps (desktop fan-out deferred to HS-41-03).
Fixed an off-token drift (`--line-height-snug` → `--line-height-normal`). Suite
2228/16. See [evidence-story-02.md](./evidence-story-02.md).

## Notes

- Port the codex `index.astro`/`dashboard-app.js` additions onto current `main`
  (they branched pre-Phase-40; apply the *additions*, don't take the files
  wholesale). Re-verify `web_runtime` wiring against the post-Phase-40 file.
