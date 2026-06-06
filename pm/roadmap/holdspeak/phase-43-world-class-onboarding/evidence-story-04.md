# Evidence — HS-43-04 — Presence as a config-backed UI toggle (kill the env var)

- **Shipped:** 2026-06-06
- **Commit:** this commit on branch `phase-43-world-class-onboarding`
- **Owner:** unassigned

## What shipped

The single worst UX wart is gone: desktop presence was **only** enableable by
setting `HOLDSPEAK_DESKTOP_PRESENCE=1` and relaunching from a terminal. It's now a
**config-backed one-click UI toggle** that takes effect live — the env var is
demoted to a power-user/headless override, not the path.

### Config — `holdspeak/config.py`

- A new `PresenceConfig(enabled: bool = False)` + `Config.presence`, wired into
  `Config.load` (`_coerce`) and the asdict save/`to_dict` round-trip.
- `desktop_presence.py::desktop_presence_enabled(env, *, config_enabled=False)` now
  returns **`config_enabled` OR the env override**; `build_desktop_presence_host`
  threads `config_enabled`.

### Live apply — `holdspeak/web_runtime.py`

- The host is built with `config_enabled=self.config.presence.enabled`.
- `_apply_updated_config` now calls **`_sync_desktop_presence()`** — when the
  config toggle flips it **starts or stops the presence host live** (no relaunch),
  fully defensive (a headless host stays None; an error never disrupts the runtime).

### Round-trip — `holdspeak/web/routes/system.py`

- `PUT /api/settings` reconstructs `presence=PresenceConfig(**presence_data)` (it
  previously dropped it), so `{ "presence": { "enabled": true } }` persists.
- `setup_status._presence_block` reads the config flag too, so `/api/setup/status`
  `presence.enabled` reflects the real state.

### The UI — the wizard Presence step (`welcome.astro` + `welcome-app.js`)

A real **switch** (`role="switch"`, animated knob, accent glow when on) that PUTs
`{presence:{enabled}}`, a **faithful inline HUD preview** that lights up (grayscale
→ full color) when on, the focus invariant, the install command when the native
extra is missing, and the line **"No environment variable, no relaunch from a
terminal — it's a real setting now."**

## Verification

- **Live (Playwright):** flipping the switch on persisted **`config.presence.enabled:
  True` to disk** and the note read "On — the HUD appears the next time you
  dictate." Screenshot: [`evidence/wizard_presence.png`](./evidence/wizard_presence.png).

## Tests run

```
uv run pytest -q tests/unit/test_presence_config.py            → 5 passed
uv run pytest -q tests/integration/test_web_settings_presence.py → 2 passed
```

- Config default-off + round-trip; `enabled` via config OR env, off when neither;
  build-host off-by-default → None.
- **Live start/stop:** toggling off closes a running host (+ sets None); toggling
  on builds one (injected fakes).
- `PUT /api/settings {presence:{enabled:true}}` persists to disk + `/api/settings`
  + `/api/setup/status` reflect it.
- The wizard step has a real `role="switch"` + "No environment variable" copy.

Full suite: see the HS-43-04 commit message.

## Acceptance criteria

- [x] Presence is enabled from the UI (config-backed via `/api/settings`); the env
      var is no longer the only path (retained as an override).
- [x] Default-off is byte-identical (`build_desktop_presence_host` → None; the
      default suite adds no GUI dep); the toggle **live-applies** (start/stop).
- [x] Covered by tests (config round-trip, gating, live start/stop, settings
      round-trip, the wizard switch) + a screenshot.
