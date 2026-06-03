# HS-32-04 — CI end-to-end smoke test (core path)

- **Status:** done (2026-06-02). Evidence: [evidence-story-04.md](./evidence-story-04.md).

## Goal

Close the biggest test-trust gap: the core promise — *audio in → transcript text
out → injected* — is today validated only behind `metal`/`spoken_e2e` markers
that never run in CI, so a regression in transcription or the injection seam
leaves CI green. Add one end-to-end smoke test that runs on every push and
asserts on the **actual produced text**.

## Scope

- A fixed, checked-in (or generated) short WAV of a known phrase → the real
  transcription path (smallest viable Whisper model) → the injection seam (typing
  captured, not sent to a real keyboard) → assert the produced text contains the
  expected phrase.
- Wire it into `.github/workflows/` as a non-gated job (not `metal`, not
  `spoken_e2e`); keep it fast and deterministic.
- Assert substring with tolerance, not exact equality, to stay robust to model
  quirks while still catching real breakage.

## Test plan

- The test itself is the deliverable; it must pass on CI hardware (Linux/macOS
  runner) without a microphone.
- Confirm it actually fails if the transcription or injection seam is broken
  (mutation check: stub the transcriber to return wrong text → test goes red).

## Done when

- [x] A CI job runs the core hotkey→text smoke test on every push, ungated.
- [x] It asserts on produced text and fails when the path is broken (shown).
- [x] Runs without a mic; fast and deterministic; documented in the workflow.

## Evidence

[evidence-story-04.md](./evidence-story-04.md). Checked-in 16 kHz WAV (generated
once via `say`, ~93 KB) → real `Transcriber("tiny")` → `TextProcessor` →
capturing typer → substring assert ("quick brown fox" / "lazy dog"). Runs ungated
on the macOS integration CI job (mlx-whisper core dep) every push; skips where no
backend. **2 passed in 1.24s** locally; mutation check (silence → empty
transcript → red) shown. Suite green **1948/14**.
