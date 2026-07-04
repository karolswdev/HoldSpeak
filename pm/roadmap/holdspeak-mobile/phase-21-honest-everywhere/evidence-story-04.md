# Evidence — HSM-21-04 — The ambient trust chip on the iPad + the web-chip audit

**Status:** done (2026-07-03), on `holdspeak-mobile/hsm-21-04-trust-chip`.

## 1. The client + the shared posture mapping

- `SetupStatus` / `SetupTrust` in Contracts (robust decode of the chip's slice of
  `GET /api/setup/status`), plus **`SetupStatus.posture`** — the same four-state
  precedence as the web chip (`trust-view.js trustPosture`): attention (off-loopback,
  no token) → writes (actuators on) → endpoint (a transcript can leave) → local.
  `TrustPosture` carries the chip's exact words.
- `HTTPDesktopClient+SetupStatus.swift` — one pure read, own extension file (the
  conflict rule).
- `SetupStatusClientTests` (4 tests): decode of the real route shape + Bearer, the
  non-2xx throw, **the full precedence table** (attention outranks everything, writes
  outrank endpoint, a missing trust block is the calm default), and the label words.

## 2. The chip (`CompanionShellApp.swift`)

In the shell's top bar beside the connection chip: one posture line, four words, tinted
by severity (local green / endpoint + writes amber / attention red). `nil` status
(unreachable, older hub) renders nothing — the connection chip owns the unreachable
story. Loaded with the other connected reads.

## 3. The live proof — TWO surfaces, TWO postures, ONE hub

Scratch hub, config flipped mid-run (`allow_actuators` false → true):

```
1. trust (A defaults) -> egress='none', actuators=False, bind='127.0.0.1'
4. trust (B actuators) -> actuators=True
```

- iPad, posture A: [`hsm-21-04-shell-chip-local.png`](./screenshots/hsm-21-04-shell-chip-local.png)
  — **Local only** (green) beside `Desktop · 127.0.0.1`.
- iPad, posture B (same hub, relaunched after the flip):
  [`hsm-21-04-shell-chip-writes.png`](./screenshots/hsm-21-04-shell-chip-writes.png)
  — **Writes need approval** (amber).
- **The web-chip audit**, same hub both times, the real `TrustChip.astro` rendered by
  Playwright: [`hsm-21-04-web-chip-local.png`](./screenshots/hsm-21-04-web-chip-local.png)
  ("Local only") and
  [`hsm-21-04-web-chip-writes.png`](./screenshots/hsm-21-04-web-chip-writes.png)
  ("Writes need approval") — the chip is driven by the live posture, not a hardcoded
  default, and **both surfaces state the same truth in the same words**.

## Honest boundaries

- The attention posture (off-loopback bind without a token) was proven at the mapping
  level (test-locked precedence), not rendered live — binding the scratch hub
  off-loopback for a screenshot adds surface for no additional truth; the walk rider's
  H3 can flip any posture the owner likes.
- The desk app keeps its per-primitive badges as its trust surface (21-01); the ambient
  chip is the companion shell's.

## Suites

`swift test` **432 passed / 8 skipped / 0 failures** (+4 `SetupStatusClientTests`) ·
companion-shell sim build **BUILD SUCCEEDED** — after the change.
