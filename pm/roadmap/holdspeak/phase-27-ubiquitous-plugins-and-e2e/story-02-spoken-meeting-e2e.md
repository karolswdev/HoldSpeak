# HS-27-02 — Spoken-meeting end-to-end harness (`say` → pipeline → screenshots)

- **Project:** holdspeak
- **Phase:** 27
- **Status:** backlog
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
Chrome-for-Testing (puppeteer) was installed in HS-16-04 for screenshots.

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
     SVG + the action-item report). Save under
     `pm/roadmap/holdspeak/phase-27-ubiquitous-plugins-and-e2e/evidence/`.
- Reliability + opt-in:
  - Own pytest marker (e.g. `@pytest.mark.spoken_e2e`), **excluded from the
    default sweep** (like `test_metal.py`). Document the run command.
  - **Skip cleanly** when prerequisites are absent: `say` missing, `.43`
    unreachable, Chrome not installed, or Whisper model unavailable.
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

- [ ] The harness runs end to end on real endpoints and produces ≥1 web
      screenshot of a rendered artifact (committed under the phase `evidence/`).
- [ ] It asserts *structure*: diagram artifact with valid mermaid block + an
      action-item artifact with ≥1 ownership-gap flag.
- [ ] It is excluded from `uv run pytest -q --ignore=tests/e2e/test_metal.py`
      and **skips cleanly** (not fails) when `say` / `.43` / Chrome / Whisper are
      unavailable.
- [ ] Run command + prerequisites documented (in the test docstring + evidence).

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
- Puppeteer / Chrome-for-Testing lives at `~/.cache/puppeteer`; it was installed
  `--no-save` in HS-16-04. Decide whether the harness installs it on demand or
  documents it as a prerequisite (prefer: skip-if-absent + a one-line install
  hint, no churn to `package.json`).
- Sandbox note: hitting `.43` (LAN) needs `dangerouslyDisableSandbox` for any
  agent-run invocation (see memory `reference-lan-llm-endpoint`).
- Keep the scripted meeting in-repo (a short `.txt` / Python constant) so the
  demo is reproducible and reviewable.
