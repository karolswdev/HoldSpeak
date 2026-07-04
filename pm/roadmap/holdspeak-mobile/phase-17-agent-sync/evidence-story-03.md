# Evidence — HSM-17-03: the agent on the desk (live coder sessions as primitives)

**Date:** 2026-07-04. **Proof style:** simulator, twice over — the seeded visual
states AND a live-hub run where the desk rendered the machine's REAL coder
sessions (including the very session that built this story). The cabled-iPad
walk remains HSM-17-06 as planned.

## What shipped

- **The typed transport (the HSM-17-01 call, decided + implemented):**
  coder presence is ephemeral, so it rides a typed polled endpoint — never the
  durable ChangeSet. `LiveCoderSession` (Providers, beside `CompanionTarget` —
  the codebase's home for live companion types) + `IDesktopClient.coderSessions()`
  (protocol requirement with an honest `notImplemented` default, the
  `runAgent` posture) + `HTTPDesktopClient.coderSessions()` decoding
  `GET /api/coders/sessions` via the loose snake_case DTO convention.
- **The mapping:** `CoderSession.init(from: LiveCoderSession)` builds an honest
  minimal feed from what the hub captured (last prompt, last tool via
  `CoderTool(hookName:)`, the pending question as the approval event, `ended`)
  — nothing invented; the rich per-event stream stays the 17-01 follow-on.
- **The live producer (the story's gap):** `startCoderPolling()` in the diorama
  stage — a 4s cadence task (the PresenceStore pattern; DeskSync stays
  event-driven and untouched) that reads the paired hub from `hostLink`,
  maps the live set into `coders`, and fires the glaring NEW-arrival treatment
  exactly once per rising edge into `waiting` (auto-clearing after 6s).
  The seeded `HS_DESK_CODER` demo suppresses the poll, so the offline demo
  stays deterministic. Rendering, tap-to-open, the pull-out, Answer — all
  pre-existing desk-parity work, now fed by real data.

## The proofs (screenshots/)

- **`hsm-17-03-seeded-desk.png`** — the seeded states: the waiting Claude
  GLARING (accent ring + NEW badge, "Claude · holdspeak"), the working Codex
  calm in cobalt.
- **`hsm-17-03-live-hub-desk.png` / `hsm-17-03-live-hub-glare.png`** — THE LIVE
  RUN: the sim paired to a real `holdspeak web` on the Mac (peer plist written
  directly; `simctl spawn defaults write` lands in the wrong domain — see
  gotchas). The desk rendered the registry's real sessions: **"Claude ·
  holdspeak" (working — the session building this story)**, **"Claude ·
  delivery-workbench" (waiting, accent — the owner's real blocked session)**,
  **"Codex · proof-repo" (idle — the morning's proof session, decayed)** — and
  the morning's `ended` claude correctly absent (tombstones leave the desk).
  Every state came from real hook data; nothing was seeded.
- **`hsm-17-03-session-feed.png`** — the open running-coder window: the rich
  replay (reads/searches/edits with `+118 −6`, `$ uv run pytest` exit 0), the
  NEEDS-YOU card with the full question, Approve/Answer entry points (the
  composer is 17-04).

## Acceptance vs. delivered

- Live sessions appear with correct identity + state — **live-proven** (three
  real sessions, three states, correct labels/colors).
- Waiting → glaring arrival; pull-out shows the question — **seeded-proven**
  (the glare ring + NEW badge) and live-proven for the accent state; the
  question renders in the NEEDS-YOU section/feed.
- State propagates without manual refresh; ended removed — the 4s poll; the
  live run showed the decayed `idle` and the absent `ended` session.
- Egress + vocabulary — `AgentSessionPrimitive.egress = .mixed("your desktop")`
  (unchanged); a coder is never a persona.
- Real metal on the cabled iPad — **deferred to HSM-17-06 by design.**

## Honest notes

- The sync chip read "Sync error · couldn't reach your desktop" during the live
  run: the durable DeskSync pass is event-driven (fires at desk load, possibly
  before pairing prefs are readable) and keeps its last outcome; the hub's
  `/api/sync/pull` answered 200 when probed. Pre-existing behavior, out of
  17-03's scope; the coder poll — this story — was unaffected.
- Gotcha for future sim pairing: `xcrun simctl spawn defaults write` writes a
  simulator-global domain the app does not read; write the app container's
  `Library/Preferences/dev.holdspeak.mobile.plist` directly (plistlib, binary
  fmt) with the app terminated, then reboot the sim to flush cfprefsd.

## Tests + builds

- `Tests/ProvidersTests/DesktopClientTests.swift` +4: the REAL proof-run wire
  payload decodes (fields + extras tolerated), malformed items are skipped
  (never invented), HTTP 500 throws, a bare conformer reports unsupported.
- Full SPM suite **449 passed / 8 skipped / 0 failures**; simulator app build
  **SUCCEEDED** (gen-meeting-capture.rb re-run; one target compiles all layers).
