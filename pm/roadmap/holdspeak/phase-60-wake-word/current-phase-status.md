# Phase 60 — The Wake Word

**Status:** in-progress (3/6). Opened 2026-06-11 on standing user direction
("K, then O" → "Word"), right after Phase 59 closed (PR #48). From the
[project backlog](../BACKLOG.md): candidate **O**, with the four recorded
safety conditions fixed: **arms, not types** (preview is the default
action; direct typing is an explicit opt-in), **an unmissable armed
indicator** (presence + Qlippy + cockpit), **a local engine with a
MEASURED false-accept story** (openWakeWord, Apache-2.0; Porcupine ruled
out on licensing), **off by default**.

**Last updated:** 2026-06-11 (**HS-60-03 done: the armed UX + settings.**
The armed state is first-class on the ambient surfaces (presence
STATE_META, the Qlippy dock, every socket page); the sticky wake preview
card carries the safety copy ("Nothing has been typed… Type it, or
dismiss and nothing happens"); the one-shot Type-it route burns its
server-minted token and **structurally ignores client text** (asserted
with an injection payload); the settings section ships the honest copy
(the egress note, the false-detection warning on the type option, the
presence recommendation) + first-enable self-healing model download. The
cockpit-banner idea replaced by the recorded broadcast-everywhere +
presence-recommended design. 8 tests; three screenshots; suite **2723
passed, 17 skipped** (+8). **HS-60-02 (prior): arm, capture, and the
pipeline.** `ArmedCapture` (frame-count time: speech onset in the window,
silence-stop, runaway cap, silent disarm); the runtime glue with a
self-healing floor-respecting frame source (any audio-floor owner pauses
the listener); `_on_wake_detect` acquires the floor as `wake` (held floor
→ silent skip), arms visibly (the NEW `armed` activity state +
`wake_armed`), captures under a hard iteration cap, releases;
`_transcribe_wake` runs the NORMAL pipeline (journal source `wake`) and
forks: preview (default) stores a one-shot burned-on-use token +
broadcasts `wake_preview` and NEVER touches the typing seam; type is the
explicit opt-in. Lifecycle: boot, live settings sync, shutdown finally.
10 tests (preview-never-types locked); full suite **2715 passed, 17
skipped** (+10). **HS-60-01 (prior): the engine seam +
config.** `WakeWordListener` is fully injectable and carries the safety
behaviors in its bones: the refractory cooldown blocks the double-arm,
pause drains frames without scoring, resume resets the detector AND
re-arms the cooldown so stale audio can never fire, an exploding observer
never kills the loop. The real engine hides behind lazy imports
(top-level-import-locked); `download_wake_models()` is THE one network
moment, named as such. `WakeWordConfig` (off, preview, 0.5, 8 s) with
tolerant file-edit normalization + strict settings-route 400s; the
`[wakeword]` extra ships. 22 tests, none needing the engine; full suite
**2705 passed, 17 skipped** (+22). Earlier: scaffolded — the feasibility spike is
already real: openwakeword 0.6.0 + onnxruntime 1.26.0 install on this
py3.13 arm64 venv, and `hey_jarvis` on TTS speech scores **0.861** for the
wake phrase vs. **≤0.063** for distractors incl. adversarial near-misses
("hey there how is the migration going": 0.002; "jarvis is a name from
the movies": 0.063) — a 0.5 threshold has wide margin both ways. The
egress moment is identified: models download from GitHub releases on
first setup (~7 MB), to be stated in settings, docs, and the SECURITY
egress table.)

## The thesis — why this phase

Hands-free entry is the one input mode HoldSpeak lacks, and it is the
strongest possible proof of the local-first pitch: an always-listening
assistant whose audio provably never leaves the machine is something the
cloud competitors structurally cannot offer. It was parked for
false-positive risk; the conditions that de-risk it now exist (the
presence surface for the unmissable indicator, the voice-commands consent
model for the type opt-in, the dictation pipeline seam for normal-path
processing) and the spike shows the margins are wide.

## Goal

Say the wake phrase; HoldSpeak arms visibly for a bounded window; your
next sentence runs the normal dictation pipeline; by default the result
is previewed (journal + card with Type it), never typed; `action="type"`
is the explicit opt-in. Off by default, byte-identical when off, and the
false-accept posture measured, not asserted.

## Scope

- **In:** the injectable engine seam + config + the `[wakeword]` extra
  (HS-60-01); arm + energy-VAD capture + the normal-pipeline wiring with
  preview/type actions (HS-60-02); the armed UX (presence/Qlippy/cockpit)
  + the one-shot Type-it route + settings (HS-60-03); the measured
  false-accept dogfood (HS-60-04); docs (HS-60-05); the real-metal
  closeout (HS-60-06).
- **Out:** custom wake-word training; multiple simultaneous wake words;
  wake-word-initiated voice commands (a future composition); changing
  hold-to-talk in any way; speaker verification.

## Exit criteria (evidence required)

- The engine seam is fully testable without openwakeword (fakes drive
  every unit test; CI green with no extra); detection/refractory/
  pause-resume tested; config validates at the settings boundary.
  (HS-60-01)
- Wake → armed broadcast → VAD capture → the normal pipeline; preview
  default journals + broadcasts and NEVER types; type action behaves
  like a hotkey run; the listener pauses around hold-to-talk and
  meetings. (HS-60-02)
- The armed state is unmissable (presence + Qlippy dock + cockpit); the
  preview card's Type it types only the server-stored preview via a
  one-shot token; settings ship with the egress-honest download
  affordance; screenshots. (HS-60-03)
- The false-accept posture is measured and committed: ≥40
  distractor utterances (≥2 voices, adversarial included) → zero
  detections at the default threshold; the wake phrase detects across
  voices. (HS-60-04)
- Docs canon-clean; SECURITY egress row; POSITIONING rows. (HS-60-05)
- Real metal: the full loop live; type proven opt-in; defaults
  byte-identical; full suite green; `final-summary.md`; BACKLOG **O**
  flipped; PR merged on green. (HS-60-06)

## Invariants

- **A false accept never edits the user's focused app** (preview default;
  bounded visible window; measured margins).
- **Off by default; byte-identical when off** (no listener thread, no
  stream, no broadcast).
- **The audio never leaves the machine** (detection and transcription are
  local; the only network moment is the explicit model download).
- **One pipeline**: wake-initiated speech runs the exact dictation path.

## Stories

| Story | Title | Status | Depends on |
|---|---|---|---|
| HS-60-01 | The engine seam + config | done | none |
| HS-60-02 | Arm, capture, and the pipeline | done | HS-60-01 |
| HS-60-03 | The armed UX + settings | done | HS-60-02 |
| HS-60-04 | The false-accept measurement | backlog | HS-60-01 |
| HS-60-05 | Docs: the wake word | backlog | HS-60-03, HS-60-04 |
| HS-60-06 | Closeout: real-metal loop + final-summary + PR | backlog | HS-60-01..05 |

## Where we are

**HS-60-01 → HS-60-03 shipped 2026-06-11.** The loop is visible and the
preview is one decisive glance. Next is **HS-60-04 — the false-accept
measurement**: the committed harness, the numbers in evidence.
