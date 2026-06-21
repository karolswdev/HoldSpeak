# Evidence — HSM-12-03 (The unified Companion shell)

**Date:** 2026-06-20 · **Status:** done

One native app that presents **both** the iPad's own on-device runtime **and** the
desktop it is pointed at — web-app-consistent (Meetings / Dictate / Companion) in the
Signal language, with a calm "working on-device" state when the desktop is away. The
"not a dumb terminal" principle, made visible.

## What shipped

- **View-model (`CompanionShell`, RuntimeCore):** composes `CompanionLink` (HSM-12-01) +
  `CompanionMeetings` (HSM-12-02) with the iPad's own `LocalRuntimeSummary`, into one
  `CompanionShellState`. `load()` returns the on-device summary **always**, plus the
  server view when reachable; a reachable handshake whose meetings call then fails
  degrades to a calm `localOnly` mode (never a half-rendered server). All business logic
  lives here — the views only present.
- **The shell (`CompanionShellApp`):** a custom Signal **bottom tab bar** (Meetings /
  Dictate / Companion — not stock SwiftUI), a connection chip, a connect-to-desktop
  onboarding (HSM-12-01 pairing), the meetings remote-control surfaces (start/stop over
  HSM-12-02), and the Companion tab standing up the Phase-13 slot (the board summary).
  The **"THIS iPAD" card is a first-class peer** of the "DESKTOP" card — its capabilities
  (on-device capture / Whisper / local inference) are shown alive even while paired.
  `gen-companion-shell.rb` (no engine packages; SDKROOT unpinned so it builds for device
  AND the simulator) + `Shell-Info.plist` (ATS local networking).

## Tests (ran)

`swift test` → **133 passed / 6 skipped / 0 failed** (+4 `CompanionShellTests`):
connected shows both faces; **unreachable is `localOnly` but the device stands its
ground** (capabilities + local meetings still present); a reachable-but-meetings-fail
desktop degrades honestly to `localOnly`; egress mirrors the client. The shell **builds
+ signs for device** (`** BUILD SUCCEEDED **`) and was **installed + launched live on a
physical iPad Air M4** (connected to the desktop at `192.168.1.28:8000`).

## Screenshots (iPad Pro 13" simulator, `simctl`)

- `screenshots/shell-connected-meetings.png` — **portal-consistent nav in Signal** + the
  **on-device runtime present while paired**: the blue "THIS iPAD" peer (capability chips,
  "nothing leaves") above the green "DESKTOP" server card (Start/Stop), the custom 3-tab
  Signal bar. (Acceptance a + b.)
- `screenshots/shell-unreachable.png` — the **calm "working on-device" state**: an
  amber "Unreachable — working on-device" desktop card with "Nothing here is blocked —
  your iPad's own runtime above is fully live; it reconnects on its own", a Retry, and
  the on-device peer fully present above it. (Acceptance d.)

## Acceptance

- **Web-app-consistent in Signal, high bar:** the portal's Meetings / Dictate / Companion
  nav as a custom Signal tab bar (not stock), real depth (per-peer accented cards),
  flow-wrapping capability chips — not flat placeholders.
- **Connect onboarding + meetings remote control:** the onboarding points the iPad at a
  server (HSM-12-01); the meetings surfaces (HSM-12-02) are reachable from the shell.
- **On-device runtime presented alongside the server:** the "THIS iPAD" peer is
  first-class and obviously alive while paired (screenshot-verified) — the device is not
  reduced to a remote.
- **Calm unreachable, no business logic in views:** `localOnly` never blocks on-device
  use; all logic is in `CompanionShell` / `CompanionMeetings` / `CompanionBoard`.

## Deferred (by design)

The deep "Companion" content — answering the coder by voice + the full board interactions
— is Phase 13 (done, in `CompanionAnswerApp`); this story stands up the navigation slot
and the meetings/local surfaces. The full device walkthrough folds into HSM-12-04.
