# Phase 60 — The Wake Word

**Status:** in-progress (1/6). Opened 2026-06-11 on standing user direction
("K, then O" → "Word"), right after Phase 59 closed (PR #48). From the
[project backlog](../BACKLOG.md): candidate **O**, with the four recorded
safety conditions fixed: **arms, not types** (preview is the default
action; direct typing is an explicit opt-in), **an unmissable armed
indicator** (presence + Qlippy + cockpit), **a local engine with a
MEASURED false-accept story** (openWakeWord, Apache-2.0; Porcupine ruled
out on licensing), **off by default**.

**Last updated:** 2026-06-11 (**HS-60-01 done: the engine seam +
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
| HS-60-02 | Arm, capture, and the pipeline | backlog | HS-60-01 |
| HS-60-03 | The armed UX + settings | backlog | HS-60-02 |
| HS-60-04 | The false-accept measurement | backlog | HS-60-01 |
| HS-60-05 | Docs: the wake word | backlog | HS-60-03, HS-60-04 |
| HS-60-06 | Closeout: real-metal loop + final-summary + PR | backlog | HS-60-01..05 |

## Where we are

**HS-60-01 shipped 2026-06-11.** The seam is real and CI-safe. Next is
**HS-60-02 — arm, capture, and the pipeline**: the runtime loop from
detection to the preview-by-default outcome.
