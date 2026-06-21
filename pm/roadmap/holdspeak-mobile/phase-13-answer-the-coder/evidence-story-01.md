# Evidence — HSM-13-01 (Remote-dictation inject path)

**Date:** 2026-06-20 · **Status:** done

The desktop's first remote-dictation inject path ships, and the Companion seam that
carries it is proven on real metal (a physical iPad Air M4 reaching this Mac's
desktop runtime over the LAN).

## What shipped

- **Desktop (Python):** `POST /api/dictation/remote`
  (`holdspeak/web/routes/dictation/pipeline.py`) accepts a client-dictated payload,
  runs it through the **same rich pipeline** the browser dry-run uses
  (`_run_dictation_dry_run_text` — corrections/blocks/plugins), and delivers the
  *processed* text via the new `WebContext.on_remote_dictation` host hook. No hook →
  process-and-return (`delivered: false`); a hook that raises → `502`, never an
  autonomous retry. Deliver-on-command only.
- **Client (Swift):** `IDesktopClient.sendRemoteDictation(text:)` +
  `RemoteDictationResult` (`apple/Sources/Providers`). The token is joined at call
  time and never echoed.
- **Enabling infra:** `HOLDSPEAK_WEB_HOST` (`holdspeak/web_runtime.py`) lets the
  desktop bind off-loopback so a companion can reach it; default `127.0.0.1`
  unchanged. A non-loopback bind is already token-guarded
  (`web_auth.nonloopback_bind_blocked`).
- **Real-metal harness (seeds the HSM-12-03 shell):** `App/CompanionProbeApp.swift`
  with `scripts/gen-companion-probe.rb` + `scripts/companion-probe-device.sh` +
  `App/Companion-Info.plist` (ATS local-networking). A pure-networking device app
  that points the iPad at the desktop and drives the **real** `HTTPDesktopClient` +
  `CompanionLink` (no mock).

## Tests (ran)

- Python: `uv run pytest tests/unit/test_web_routes_remote_dictation.py
  tests/unit/test_dictation_routes_split.py` → **7 passed**. Asserts: processed (not
  raw) text delivered; no-hook process-only; empty/non-object-target rejected (400);
  delivery failure → 502; the route is registered (route-table count 36 → 37).
- Swift: `swift test` → **107 passed / 6 skipped / 0 failed**. Adds
  `testSendRemoteDictationPostsAndDecodes` + `...HTTPErrorThrows`; the IDesktopClient
  fakes in `CompanionLinkTests` / `CompanionMeetingsTests` conform to the new method.

## Real-metal proof (physical iPad Air M4 → desktop over the LAN)

Desktop: `HOLDSPEAK_WEB_HOST=0.0.0.0 HOLDSPEAK_WEB_PORT=8000 holdspeak web --no-open`
on `192.168.1.28`. Token-enforced off-loopback:

```
GET  /health             (no token)  -> 200    # unauthenticated reachability probe
GET  /api/runtime/status (no token)  -> 401    # auth enforced off-loopback
GET  /api/runtime/status (token)     -> 200
WARNING | holdspeak.web_server | Binding non-loopback host '0.0.0.0': the web runtime
        is reachable beyond this machine and requires the auth token on every request.
```

HSM-13-01 route over the LAN (token):

```
POST /api/dictation/remote {"text":"..."} ->
  {"success":true,"final_text":"...","delivered":false}   # pipeline ran; no host hook wired
```

CompanionProbe built + signed + installed + launched on the iPad (`devicectl`,
device `AjPed` / `6B2F424D-707F-51F7-A33E-259427861CB1`). On launch the device
established a live connection to the desktop runtime, captured server-side:

```
lsof -iTCP:8000 -sTCP:ESTABLISHED ->
  192.168.1.28:8000 -> 192.168.1.67:50008    # desktop  <-  iPad
```

The iPad (`192.168.1.67`, iOS Private Wi-Fi MAC) was the only LAN client to connect
to `:8000` within ~1s of the app launching — the HSM-12-01 seam, on real metal.

## Deferred (by design)

- On-device **voice-note capture** → HSM-13-02.
- The **Companion board** (AI PI state on the iPad) → HSM-13-03.
- The **host `on_remote_dictation` delivery wiring** into a live coder session and
  the end-to-end answer-the-coder walkthrough → HSM-13-04 (the Track N gate). The
  route + hook seam is ready for it; this story stops at the proven inject path.
