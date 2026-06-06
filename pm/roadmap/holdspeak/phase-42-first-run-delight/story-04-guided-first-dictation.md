# HS-42-04 — Guided first dictation test (real app)

- **Project:** holdspeak
- **Phase:** 42
- **Status:** done (2026-06-06)
- **Depends on:** HS-42-01, HS-42-03
- **Unblocks:** none
- **Owner:** unassigned

## Problem

The most important user moment is "I held the key, spoke, released, and useful text
appeared in **the app I meant to use**." Today nothing guides or verifies that path,
and a naive in-browser textarea test would prove the *wrong* surface (text into our
own tab, not another app).

## Scope

- In:
  - A guided flow with two honest legs:
    - **(a) Deterministic leg (CI-provable):** mic → transcription → processing
      over the committed `tests/fixtures/core_path_smoke_16k.wav`, shown in-UI
      (transcript → processed output → insertion method).
    - **(b) Real-app leg (the magic moment):** "Focus your editor and hold the key"
      → record → insert → a **detectable confirmation** that text landed in the
      external app.
  - An honest fallback ladder: hotkey blocked (e.g. Wayland) → focused fallback;
    synthetic typing blocked → clipboard/manual paste (framed as a supported mode);
    backend unavailable → route to model setup (HS-42-06); mic permission missing →
    OS-specific instructions.
  - On a verified success, **set the `first_run` milestone** (HS-42-01 seam) so the
    user is never sent back to setup-mode.
- Out:
  - New transcription/insertion engines (reuse the existing core path + fallbacks).
  - Hardware-gated mic automation in CI (the real-app leg is a dogfood).

## Acceptance criteria

- [x] The guided flow shows the steps + a readiness mini-row + live status; on a
      real dictation it shows transcript + confirmation. *(Deterministic
      transcription proof = the existing `core_path_smoke` CI test; the fixture WAV
      lives in `tests/`, not the installed package, so the production flow uses the
      user's real speech.)*
- [x] Leg (b) proves insertion into an **external** app via the live
      `dictation_typed` WS → the success banner + transcript (Playwright); the
      real-mic frame is the HS-42-08 dogfood.
- [x] Every failure mode routes to remediation; the clipboard/focused fallback
      reads as intentional (the fallback ladder).
- [x] A verified success **sets the durable first-success milestone** (so `/`
      stops showing setup-mode); proven by 3 tests.
- [x] Bundle rebuilt; only `web/src` committed; screenshots of the guide + the
      done state + the live success.
- [x] Default suite green; the milestone test adds no real network/LLM call.

## Test plan

- Integration/unit: the deterministic leg over `core_path_smoke_16k.wav`; the
  milestone-set-on-success path.
- Manual/dogfood: a real first-dictation run into an external editor (the TTFD
  stopwatch starts here for HS-42-08).
- Frontend: `cd web && npm run build && npm run shots`.
- Full: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.

## Notes / open questions

- Real-app confirmation mechanism (deferred decision from the status doc): a
  clipboard round-trip vs an in-app echo target — pick the most reliable
  platform-portable signal during the story.
