# Evidence — HS-41-07 — Closeout

- **Shipped:** 2026-06-05
- **Commit:** this commit on branch `phase-41-runtime-presence`
- **Owner:** unassigned

## What shipped

Phase 41 closeout — verification + record only (no new surfaces).

### 1. Dogfood — state tracks, focus not stolen (live, this closeout)

Re-ran the macOS focus-safety smoke harness on this host:

```
uv run python scripts/presence_macos_smoke.py \
  pm/.../phase-41-runtime-presence/evidence/closeout_macos
→ frontmost before: Terminal | after: Terminal | focus_stolen: False
→ panel: .../closeout_macos/macos_presence_hud.png (40327 B)
→ glyph: .../closeout_macos/macos_presence_glyph.png (72192 B)
→ SMOKE PASSED (focus not stolen + HUD captured)
```

A real HoldSpeak server is started, the native `NSPanel` + `WKWebView` HUD and
the `NSStatusItem` glyph come up, a state is driven (`transcribing`), and the
frontmost app is unchanged before/after the HUD shows — so injected dictation
keystrokes keep landing in the target app. The HUD renders the Signal
"Transcribing — Turning your speech into text…" card with the `Hotkey` source
([`evidence/closeout_macos/macos_presence_hud.png`](./evidence/closeout_macos/macos_presence_hud.png)).

Linux Tier-1 (notification + tray) and Tier-2 (GTK-WebKit overlay) were
live-verified on `.43` (Ubuntu 24.04/GNOME, X11) in HS-41-05 and HS-41-08
respectively — captures carried in
[`evidence/linux_presence_notification.png`](./evidence/linux_presence_notification.png)
and [`evidence/linux_presence_overlay.png`](./evidence/linux_presence_overlay.png).

### 2. Flag-off byte-identity re-asserted

With `HOLDSPEAK_DESKTOP_PRESENCE` unset, `build_desktop_presence_host()` returns
`None` and nothing renders — the runtime is byte-identical and pulls in no GUI
dependency. Presence + runtime-activity units:

```
uv run pytest -q tests/unit/test_desktop_presence.py \
  tests/unit/test_runtime_activity.py tests/unit/test_runtime_counters.py
→ 37 passed
```

### 3. Full suite green

```
uv run pytest -q --ignore=tests/e2e/test_metal.py
→ 2261 passed, 16 skipped in 50.15s
```

(`test_metal.py` excluded — it hangs without a mic device, per the project's
documented regression-sweep exclusion. The 16 skips are hardware/endpoint-gated
integration + e2e tests with no backend on this host.)

### 4. No build artifacts tracked

```
git ls-files holdspeak/static/_built/ | wc -l  →  0
```

### 5. Record reconciled

- `final-summary.md` written.
- README phase row → **done**, "Current phase" pointer advanced.
- `HANDOVER.md` TL;DR refreshed to Phase 41 CLOSED.
- Story `current-phase-status.md` → CLOSED (8/8); story-07 row → done.
- **codex PR #17** closed as superseded (its bones salvaged; its Tk renderer
  rejected — see `final-summary.md` "Notes").

## Acceptance criteria

- [x] Real dogfood captured (state tracks; **focus not stolen**) — macOS smoke
      `SMOKE PASSED` live this closeout; Linux Tier-1/2 live on `.43`.
- [x] Full suite green (2261/16); flag-off byte-identity re-asserted (37 passed,
      host returns `None`); no `_built/` tracked (0).
- [x] `final-summary.md` exists; status frozen; README → done; HANDOVER updated;
      PR opened/merged; codex PR #17 closed.
