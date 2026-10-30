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

## LINE-6. The concierge rows (Shipped 2026-10-29, lane LINE-6)

- **Goal**: the two speech models come through the Engines window's
  download path, each with its licences: "Phone speech in · Parakeet (int8,
  onnx-asr)" (661 MB) and "Phone voice · Pocket TTS" (226 MB); weights
  CC-BY-4.0, code MIT.
- **Files**: `hs/inference_setup_catalog.py` (kind `speech_model_preset`,
  its validator, revision 6 signed with a new key `holdspeak_catalog_2026_10_29`;
  the old trust roots stay; no private key is kept), `hs/line/models.py`
  (new: the fetch, the state, the jobs), `hs/line/node.py`
  (`holdspeak line models` and the hello read it), `hs/line/speech.py` (the
  engines load from the Line's model folder when it is Ready),
  `hs/services/concierge_service.py`, `hs/web/routes/concierge.py`
  (`GET /api/concierge/speech`; `POST /api/concierge/download` with a speech
  preset starts the Line's fetch), `web/src/features/runson/PhoneSpeech.tsx`
  (new), `RunsOnCore.tsx`, `scripts/record_speech_fixture.py` (new).
- **Changes**: each model pins a Hugging Face revision and every file its
  engine loads (onnx-asr's int8 Parakeet: config, vocab, encoder, decoder;
  pocket-tts 4.0.1's English model, tokenizer and the `alba` voice), each
  with its size and SHA-256. The fetch streams each file into
  `<the Line's folder>/models/<id>/`, hashes it as it comes and keeps it only
  when it matches. Ready = every pinned file is there and matches;
  `.verified.json` keeps the digest by size and time, so a read does not hash
  650 MB again. The Engines window draws the two in their own fold, "Phone
  speech" (name, size, licence, state, Download with the host in its hover
  title); the row polls while it downloads. Speech models are not inference
  presets: `applicable_presets` leaves them out.
- **Tests**: T1 `tests/unit/test_line_models.py` (the signed envelope
  round-trips; a changed pin breaks the signature; the validator refuses a
  mutable revision, a path out of the folder, a wrong total; the fetch with
  a fake: the pinned URLs, progress, Ready, a wrong digest kept nowhere, a
  changed file hashed again; the job to Ready and to failed; `holdspeak line
  models` and the hello share the state; the routes); T2
  `features/runson/__tests__/engines.app.test.tsx` (Phone speech at 1440 and
  393: one Ready and one Not downloaded row; the press through to progress
  and Ready, on the recorded answers); T3 the sweep's Engines case.
- **Left**: the rows say this machine's folder. A Line node on another
  machine still runs `holdspeak line models` there (its hello reports its own
  state). The engines' load from the folder (onnx-asr `path=`, a pocket-tts
  config pointed at the local files) is not proven on real metal in this
  lane: onnx-asr and pocket-tts are not installed in the dev venv.

## LICENCE. The hub's own GPL pulls (Left; needs his ruling)

- **Goal**: no GPL code in a HoldSpeak process.
- **Findings** (design §2): the `tts` extra (Kokoro) imports `phonemizer` and
  loads `libespeak-ng` (GPL-3.0-or-later) in the hub; `faster-whisper` imports
  PyAV, whose Linux wheel bundles `libx264` and `libx265` (GPL-2.0-or-later).
- **Changes**: his ruling first (design §14); then swap Kokoro for Pocket TTS
  in the hub's speech, and keep PyAV out of the Linux STT path.
