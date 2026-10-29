# The Line: the recipe

The slices that make `LINE-DESIGN-2026-10-29.md` real. The owner chose the
native line on 2026-10-29 ("I'm choosing the second"). Each slice is one PR
in the fast cycle (`CLAUDE.md`). Short paths: `desk/` is `web/src/desk/`,
`hs/` is `holdspeak/`. Tests follow the test diet: T1 a hub test, T2 vitest
(one file per app), T3 the desk sweep, T4 a real browser only for keys,
drag or touch.

**The rig for every slice.** `tests/fixtures/fake_baresip.py` is a real
separate process that speaks baresip 4.12.0's `ctrl_tcp` (the events are
recorded from the real baresip: `scripts/line/record_baresip_events.py`) and
plays and hears tones on the two `aupipe` sockets. `tests/fixtures/line_rig.py`
runs a real `LineNode` on it, linked in process to a `LineHub`.
`scripts/record_line_fixtures.py` records the hub's own routes into
`desk/calls/__fixtures__/line.*.json`. Every rig hub sets `HOLDSPEAK_LINE=off`
unless the test drives the Line.

State: **Shipped** means merged to main. **Left** means a later slice.

---

## LINE-1. The spike and the design (Shipped, #1606)

- **Goal**: choose the stack, measure it on the Mac and on `karol`, and
  write the design.
- **Proof**: `LINE-DESIGN-2026-10-29.md` §3 (the measured table), §2 (the
  licences read from the kegs and the wheels).

## LINE-2. The node (Shipped, #1608)

- **Goal**: a call to the Line reaches the Calls runner with no change to
  the runner.
- **Files**: `hs/line/` (supervisor, control, audio, speech, turns, guards,
  hub, adapter, node, secrets, `aupipe/aupipe.c` BSD-3), the three wire
  routes and the two face routes in `hs/web/routes/calls.py`, `calls.line`
  and `calls.daily_limit` (`hs/config/calls.py`), the `line` extra.
- **Proof**: seven unit files, `tests/integration/test_line_call.py`, the
  slow real-baresip test. What it changed from the design: "Built, 2026-10-29"
  in the design.

## LINE-3. The Line on the home box (Left)

- **Goal**: the Line runs on `karol` and the hub drives it over the tailnet.
- **Changes**: the node credential in place of the hub token
  (`holdspeak node token create karol --capability calls.line`, `holdspeak node
  pair`; `HubClient` is the one class that changes), the systemd user unit
  `holdspeak-line.service` and the launchd agent `com.holdspeak.line.plist`,
  `scripts/line/build-baresip.sh` (baresip 4.12 into `~/holdspeak-line/opt`,
  no sudo), a `holdspeak line install` that does the Mac's own-venv steps of
  `docs/calls.md` (Python 3.13: onnxruntime has no cp314 wheel), and
  "Install the Line on karol" in Settings ▸ Calls ▸ Line ▸ Where it runs
  (the canvas's pending verb). The hub lists its linked Line nodes, so Where
  it runs can offer them before one is picked (today it offers This Mac and
  the place in `calls.line.where`).
- **Proof**: a real call from the Mac to `karol` through the runner (a
  recorded turn); `systemctl --user status holdspeak-line` after a reboot.

## LINE-3b. The Telnyx line (Left; needs his account)

- **Goal**: a real number on the Line.
- **Changes**: verify the account line of design §8 at sign-up (NAT:
  latching, or `medianat=stun`; TLS and SRTP); the number itself has no
  settings key yet (`calls.line.account` holds `user`, `domain`, `outbound`),
  so the Number row of the canvas waits for it; the provisioning that reads
  `calls.line.telnyx_api_key`.
- **Proof**: one inbound and one outbound Telnyx call. The password custody
  in the hub's keystore needs his word (CONFIG, design §14).

## LINE-4. The faces and the docs (Shipped: the canvas #1607; the faces and docs in the LINE-4b PR)

- **Goal**: Settings ▸ Calls ▸ Line, the Calls window's Line words, the docs.
- **Files**: `desk/calls/LineSettings.tsx` (mounted from
  `CallsSettings.tsx`), `desk/calls/CallsWindow.tsx` (the status-bar words,
  the empty state with "Set up the Line ›"), `desk/calls/api.ts`,
  `desk/calls/types.ts`, `desk/calls/calls.css`,
  `scripts/record_line_fixtures.py`, `desk/__tests__/calls.app.test.tsx`;
  `docs/calls.md` "The Line", `NOTICE`.
- **Left from the canvas**: the Engines window's two speech rows (LINE-6);
  Cancel on a ringing Test call (the hub has no cancel for it); "Answered ·
  m:ss" (the test answer has no length); the Number row (LINE-3b); the
  primary empty-state verb (the kit's `SurfaceState` draws it secondary on
  every window); ai-phone stays an optional adapter until the Line has done
  his real calls for a week, then it is parked (never deleted).

## LINE-5. Barge-in, measured (Left)

- **Goal**: the time from his first word over our voice to our voice
  stopping, measured on a real line (design §13 estimates about 125 ms from
  the socket lead), and the first model token time that places the 1.5 s
  filler.
- **Proof**: the numbers in the design's "Built" section, from a real call.

## LINE-6. The concierge rows (Left)

- **Goal**: the two speech models come through the Engines window's
  download path, each with its CC-BY-4.0 line: "Phone speech in · Parakeet"
  (0.6 GB) and "Phone voice · Pocket TTS" (0.2 GB).
- **Why left**: the Engines catalog is the signed preset envelope of
  `hs/inference_setup_catalog.py` (LLM presets, formats `gguf` and
  `mlx_safetensors` only). A speech row needs a new preset kind, its
  validator and a new signature: that is the catalog's core, not a row.
  Until then `holdspeak line models` fetches the models from Hugging Face.

## LICENCE. The hub's own GPL pulls (Left; needs his ruling)

- **Goal**: no GPL code in a HoldSpeak process.
- **Findings** (design §2): the `tts` extra (Kokoro) imports `phonemizer` and
  loads `libespeak-ng` (GPL-3.0-or-later) in the hub; `faster-whisper` imports
  PyAV, whose Linux wheel bundles `libx264` and `libx265` (GPL-2.0-or-later).
- **Changes**: his ruling first (design §14); then swap Kokoro for Pocket TTS
  in the hub's speech, and keep PyAV out of the Linux STT path.
