# HS-27-02 — Spoken-meeting end-to-end harness (`say` → pipeline → screenshots)

- **Project:** holdspeak
- **Phase:** 27
- **Status:** done
- **Depends on:** HS-16-04 (web SVG render), HS-27-01 (a second real plugin to show)
- **Unblocks:** HS-27-05
- **Owner:** unassigned

## Problem

Every layer of the plugin stack has unit/integration coverage, but nothing
exercises the **whole thing on real endpoints**: spoken audio → transcript →
routing → real LLM plugins → persisted artifacts → rendered web UI. We want a
true end-to-end that (a) catches integration breaks the unit tests can't, and
(b) doubles as a **living demo** — you watch a spoken meeting become a rendered
architecture diagram + an action-item report, and capture screenshots.

The pieces already exist: `say` (`/usr/bin/say`) synthesizes audio;
`tests/e2e/test_meeting_transcription.py` already loads a wav into `Transcriber`;
`synthesize_and_persist` writes artifacts; `MeetingWebServer` serves `/history`;
browser screenshots are already proven feasible (HS-16-04 captured the rendered
mermaid SVG in a headless browser).

## Scope

### In

- A harness that, end to end on **real** endpoints:
  1. **Synthesize** a scripted mock meeting to audio with `say` — multiple voices
     (`say -v Alex` / `-v Samantha`) for 2+ speakers — covering architecture talk
     (so `mermaid_architecture` fires) and action items with/without owners (so
     `action_owner_enforcer` fires). Concatenate → wav.
  2. **Transcribe** via `Transcriber` (local Whisper), as the existing e2e does.
  3. **Route + run** the real plugin chain through `PluginHost` (with the `"llm"`
     capability enabled against the `.43` Q6 endpoint) — including the deferred
     queue drain (`process_next_deferred_run`).
  4. **Persist** via `synthesize_and_persist` into a temp SQLite DB.
  5. **Render + screenshot**: serve `MeetingWebServer` over that DB, drive
     `/history` → open the meeting → screenshot the artifacts (rendered mermaid
     SVG + the action-item report) with **Playwright (Python)**. Save under
     `pm/roadmap/holdspeak/phase-27-ubiquitous-plugins-and-e2e/evidence/`.
- Browser automation = **Playwright (Python)**, not Puppeteer: the e2e is a
  pytest test, so a Python-native driver keeps the whole harness in one language
  (no Node subprocess glue), and Playwright's auto-waiting handles "wait for
  Alpine to load artifacts + mermaid to finish rendering the SVG" without
  `sleep`-and-hope — directly mitigating the flakiness risk below. Dev-only dep
  (`playwright` + `playwright install chromium`); import-gated so it skips when
  absent. (Puppeteer in HS-16-04 was a throwaway dev screenshot, `--no-save`,
  never a committed dependency.)
- Reliability + opt-in:
  - Own pytest marker (e.g. `@pytest.mark.spoken_e2e`), **excluded from the
    default sweep** (like `test_metal.py`). Document the run command.
  - **Skip cleanly** when prerequisites are absent: `say` missing, `.43`
    unreachable, Playwright/Chromium not installed, or Whisper model unavailable.
  - **Structural assertions, not exact text** (real LLM is non-deterministic):
    a `diagram` artifact exists with a parseable mermaid block; an `action_items`
    artifact exists; ≥1 flagged ownership gap. Exact wording is never asserted.

### Out

- Putting this in the default CI sweep (it's slow + non-deterministic + needs
  endpoints).
- Live-meeting capture (mic). File-based / synthesized audio only.
- Asserting transcription accuracy numerically (WER) — that's the existing
  `test_meeting_transcription.py`'s job.
- Multi-speaker diarization correctness — just enough voices for realism.

## Acceptance criteria

- [x] The harness runs end to end on real endpoints and produces a web
      screenshot (`evidence/spoken_meeting_artifacts.png`) showing the transcript,
      the rendered mermaid SVG, and the action-item checklist.
- [x] It asserts *structure*: a `diagram` artifact whose mermaid renders to an
      `<svg>`, an `action_items` artifact rendering ≥1 checklist row, and a
      populated transcript. Exact wording never asserted.
- [x] Opt-in via `HOLDSPEAK_SPOKEN_E2E=1` (module-skips otherwise, so the default
      sweep never runs it), and **skips cleanly** when `say` / `.43` /
      Playwright+Chromium / Whisper are unavailable.
- [x] Run command + prerequisites documented (test docstring + evidence). Also
      drove a UX fix: action-items now render as a structured checklist (not raw
      markdown) with friendly gap labels — see `evidence-story-02.md`.

## Test plan

- The harness *is* the test: `uv run pytest -q -m spoken_e2e -s` (opt-in).
- Provide a `say`-based fixture generator that also (bonus) writes
  `tests/fixtures/mock_meeting.wav`, reviving the currently-skipped
  `tests/e2e/test_meeting_transcription.py`.
- Manual: eyeball the committed screenshots after a run.

## Notes / open questions

- **Transcript fallback for the assertion path:** if `say`+Whisper transcription
  is too lossy to reliably trigger intents, feed a hand-authored transcript
  straight into the routing step for the *assertion* path, and keep the
  `say`→Whisper leg for the *demo screenshot*. Documented fallback, not a failure.
- Playwright (Python) install: `uv pip install playwright && playwright install
  chromium` (or add to a dev/e2e extra in `pyproject.toml`). Prefer skip-if-absent
  + a one-line install hint in the skip reason over forcing the dep on everyone.
- Sandbox note: hitting `.43` (LAN) needs `dangerouslyDisableSandbox` for any
  agent-run invocation (see memory `reference-lan-llm-endpoint`).
- Keep the scripted meeting in-repo (a short `.txt` / Python constant) so the
  demo is reproducible and reviewable.
