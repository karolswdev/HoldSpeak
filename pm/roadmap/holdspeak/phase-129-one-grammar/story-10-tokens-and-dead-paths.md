# HS-129-10 — Tokens green and the dead paths

- **Project:** holdspeak
- **Phase:** 129
- **Status:** backlog
- **Depends on:** HS-129-05
- **Unblocks:** HS-129-11
- **Owner:** unassigned

## The thesis (the bar)

The gates the product already owns must pass, and dead interaction paths
must be alive or gone. `npm --prefix web run tokens:gate` exits 1 today with
27 raw-value violations; the z-ladder has six unallowlisted raws plus an
undocumented `--z-sticky` band and a phantom 200 fallback; and audit B found
desk-object double-click opening nothing in the scripted walk, plus Delivery
reporting `DW exited 2`.

### What changes

1. **Tokens (mechanical batches, audit D order):** replace the raw
   danger/ok/warn fallback literals (13× `#f87171`, 9× `#34d399`,
   6× `#fbbf24` — delivery.css, speak.css, RepoWindow.css,
   speak-to-fill.css) and the footer alpha washes with semantic tokens;
   fix the six raw z-indexes (intelligence.css:52, workbench-config.css:66,
   inline-editor.css:78,90 — dies with HS-129-08, mission-control.css:287,
   attention.css:212); remove the `var(--desk-z-popover, 200)` fallback
   (inlet-autocomplete.css:7); reconcile `--z-sticky` with the desk ladder
   (it dies with the sticky grammar in HS-129-05); refresh the stale
   token-allowlist entries; document (or remove) the 6/16/18px radius
   exceptions and the sheet-corner exception; collapse the letter-spacing
   recipes onto a small label scale. Gate green at story exit.
2. **Desk-object open path:** manually verify double-click on zones,
   meeting objects, and artifact objects in the live app. If the path is
   dead, fix it; if it was a walk-script artifact, land a Playwright
   helper that opens objects reliably and prove it — either way the walk
   harness gains a working object-open primitive for HS-129-11.
3. **Delivery `DW exited 2`:** diagnose. If environmental (dw CLI absent
   for the server process), the state must render as an honest named
   unavailable state with the reason; if a product bug, fix it.
4. Document the constitutional exemption note for OS-chrome overlays
   (ShortcutSheet, attention/system surfaces) flagged by audit C.

## Acceptance criteria

1. `npm --prefix web run tokens:gate` exits 0; the allowlist contains only
   current, per-file, commented exceptions.
2. Double-clicking a zone, a meeting, and an artifact on the desk opens the
   right window/pullout — proven live, in the walk harness.
3. Delivery either works or names its unavailability honestly with the
   failing precondition.
4. `grep -rn "z-index" web/src --include="*.css"` shows only `--desk-z-*`
   tokens and documented resets.

## Test plan

- Web: tokens:gate in CI posture (part of `npm run check`); the object-open
  Playwright helper's own test; typecheck + build.
- Walk: live object-open proof shots; Delivery state shot.
