# Phase 60 — Agent Brief (read this first)

You are picking up **Phase 60 — The Wake Word** for HoldSpeak. Backlog
candidate **O**, opened on standing user direction ("K, then O" → "Word").
Self-contained: mission, the recorded safety conditions, verified ground
truth (including a live detection spike), rules, per-story success.

---

## 0. Mission

Hands-free entry into dictation, without betraying the product's trust
posture: say the wake phrase, HoldSpeak **arms** (visibly, briefly), your
next sentence goes through the normal dictation pipeline, and by default
the result is **previewed, not typed**. The strongest possible proof of
the local-first pitch: an always-listening assistant whose audio provably
never leaves the machine.

## 0.1 The recorded safety conditions (fixed; from the user conversation)

1. **Arms, not types.** The wake word never types directly. It opens a
   visible, bounded armed window; speech in that window runs the normal
   pipeline; the DEFAULT action is a preview the user confirms. Direct
   typing is an explicit opt-in on top (`action: "type"`), the
   voice-commands consent model: configuring is consent.
2. **An unmissable armed indicator.** The presence surface (and Qlippy's
   dock when on) shows listening/armed; the web cockpit shows a banner.
3. **A local engine with a real false-accept story.** openWakeWord
   (Apache-2.0, ONNX) — Porcupine is ruled out on licensing. The
   false-accept posture is MEASURED, not asserted (HS-60-04).
4. **Off by default; defaults byte-identical.**

## 0.2 The feasibility spike (already run, 2026-06-11, this machine)

openwakeword 0.6.0 + onnxruntime 1.26.0 install cleanly on the py3.13
arm64 venv. `hey_jarvis` (ONNX) on 16 kHz/1280-sample frames:

- "hey jarvis" via `say -v Samantha`: **max score 0.861**
- "let's review the quarterly numbers tomorrow": 0.000
- "hey there how is the migration going": 0.002
- "jarvis is a name from the movies": 0.063

A 0.5 default threshold has wide margin both ways. **The egress moment**:
models download from the openWakeWord GitHub releases on first setup
(~7 MB total incl. shared melspectrogram/embedding/VAD models, cached in
the package's resources dir) — this must be explicit in settings + docs +
the SECURITY egress table.

---

## 1. The one thing you must not get wrong

**A false accept must never put text into the user's focused app.** That
is the whole reason `action: "preview"` is the default and the armed
window is visible and bounded. Every design choice bends toward: a
misfire costs a glance, never an edit.

---

## 2. Rules of the road (non-negotiable)

- **PMO commit gate** (7 boxes; evidence with done-flips; final-summary at
  exit). No `Co-Authored-By`; no `--no-verify`.
- **Operating cadence** per shipping commit; one PR per phase, branch
  `phase-60-wake-word`, merged on green.
- **Tests**: `uv run pytest -q --ignore=tests/e2e/test_metal.py`. The
  wake engine must be FULLY testable without openwakeword installed
  (injectable detector + frame source; lazy imports; CI has no extra).
- **Web bundle gitignored**; `is:global` for JS-rendered DOM.
- **Docs obey the canon** (POSITIONING.md; the live voice guard). New
  canonical names this phase: "the wake word", "the armed window".
- **Real-metal closeout**: the full loop on this Mac (`say` the wake
  phrase → armed broadcast → a spoken sentence → the preview carrying the
  real pipeline result).

---

## 3. Ground truth (verified at scaffold)

- **Audio capture**: `holdspeak/audio.py` provides the recording
  primitives; `web_runtime` owns hold-to-talk (pynput) and constructs the
  Transcriber + TextProcessor + dictation pipeline (`dictation_runner`).
  The wake listener is a NEW continuous 16 kHz mono `sounddevice`
  InputStream consumer at 1280-sample hops — it must pause while
  hold-to-talk records and while a meeting captures (stream contention),
  and resume after.
- **openwakeword API**: `Model(wakeword_models=["hey_jarvis"],
  inference_framework="onnx")`; `model.predict(np.int16[1280])` →
  `{name: score}` per frame; detection = score ≥ threshold, then a
  refractory period to avoid double-fires; `openwakeword.utils.
  download_models(model_names=[...])` fetches from GitHub (the egress
  moment).
- **Broadcast transport**: `server.broadcast(type, data)` /
  `ctx.broadcast`; presence + Qlippy consume `runtime_activity` and
  `hs-broadcast` DOM events (Phase 56). An `armed` activity state needs a
  dock mapping + presence STATE_META entry.
- **The pipeline seam**: `dictation_runner.run_dictation_pipeline` (the
  Phase-52 carve) — wake capture feeds the SAME path; `action="preview"`
  stops before the typing step and broadcasts + journals instead.
- **The journal** records every run (source-tagged) — wake runs should
  carry a distinguishable source.
- **Config**: add `WakeWordConfig` to `Config` (the PresenceConfig
  precedent); settings route validation per the established pattern;
  `[wakeword]` extra in pyproject (openwakeword pulls onnxruntime).

---

## 4. Per-story definition of success

- **HS-60-01 — the engine seam.** `holdspeak/wake_word.py`:
  `WakeWordListener(detector, frames, on_detect, threshold,
  refractory_seconds)` fully injectable (a fake detector + a fake frame
  source drive every unit test); the real openwakeword detector behind a
  lazy import + `wake_word_available()`; pause/resume; a
  `download_wake_models()` helper. `WakeWordConfig(enabled=False,
  model="hey_jarvis", threshold=0.5, armed_window_seconds=8.0,
  action="preview")` on `Config` with settings-route validation
  (threshold 0..1, action in preview/type, window 2..30). `[wakeword]`
  extra. Tests: detection at/above threshold, refractory, pause/resume,
  config round-trip + refusals, the no-extra-installed import safety.
- **HS-60-02 — arm + capture + the pipeline.** web_runtime: listener
  lifecycle (config-gated start/stop, live via settings-applied); on
  detect → `runtime_activity` state `armed` broadcast + an
  `wake_armed` broadcast (window seconds) → energy-VAD capture (start on
  speech within the window, stop on ~1.2 s silence or 15 s cap; abandon
  silently if no speech) → the normal pipeline. `action="preview"`
  (default): the result is journaled (source `wake`) and broadcast as
  `wake_preview`, NEVER typed; `action="type"`: typed exactly like a
  hotkey run. The listener pauses during hold-to-talk recording and
  meetings. Tests with fakes end to end.
- **HS-60-03 — the armed UX + settings.** Presence: `armed` state in the
  activity map (web HUD + the Qlippy dock mapping); the wake preview as
  a Qlippy/web card with **Type it** (a one-shot confirm route that
  types ONLY the exact previewed text: the preview is stored server-side
  under a one-shot token; the route types-and-burns it) and Dismiss. The
  /dictation cockpit shows armed + preview surfaces. The settings
  section (enable, model, threshold, window, action with the honest
  copy, the download affordance with the egress note). Screenshots.
- **HS-60-04 — the false-accept measurement.** A committed, repeatable
  dogfood: a distractor corpus (≥20 sentences × ≥2 `say` voices,
  including adversarial near-misses) → ZERO detections at the default
  threshold; the wake phrase × voices → detection. The numbers land in
  evidence and the docs cite them as "measured on synthetic speech",
  honestly noting real-room audio differs.
- **HS-60-05 — docs.** USER_GUIDE section (what arming looks like, the
  preview default, the type opt-in as consent, the measured numbers
  caveat); SECURITY.md egress table gains the model-download row;
  POSITIONING canonical rows; canon-clean (live voice guard).
- **HS-60-06 — closeout.** Real metal: `say` the wake phrase → the armed
  broadcast observed → a spoken sentence → `wake_preview` carrying the
  real Whisper transcript through the real pipeline; the type action
  proven opt-in; defaults byte-identical (config diff + no listener
  thread when disabled). Full suite; `final-summary.md`; BACKLOG **O**
  flipped; PR merged on green.

---

## 5. Gotchas

- **CI has no openwakeword** — every test must run without it (lazy
  imports; `wake_word_available()`; fakes). Mark any real-model test
  opt-in like the spoken e2es.
- **Stream contention**: one process, multiple sounddevice consumers —
  pause the wake stream around hold-to-talk and meeting capture, and
  make pause idempotent (events can race).
- **The refractory period** matters: openwakeword scores stay high for
  several frames after a hit; without a cooldown you arm twice.
- **`predict()` wants int16** at 16 kHz, 1280-sample hops; the recorder
  yields float32 — convert at the boundary, once.
- **The one-shot type route is a write** — it must type the stored
  preview verbatim (server-side token, burned on use, expiring with the
  preview), never client-supplied text.
- **Settings-applied lifecycle**: enabling via the UI must start the
  listener live (the presence-host precedent) and disabling must stop it.
- **The voice guard is live**: docs prose dash-free, canonical names.

## 6. Where to start

HS-60-01: the injectable engine seam is the foundation and proves the
testing posture. Then 02 (the runtime loop), 03 (UX), 04 (measurement),
05 (docs), 06 (closeout).
