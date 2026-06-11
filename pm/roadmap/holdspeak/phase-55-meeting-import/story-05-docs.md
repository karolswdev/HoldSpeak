# HS-55-05 — Docs: import + facets

- **Project:** holdspeak
- **Phase:** 55
- **Status:** backlog
- **Depends on:** HS-55-03, HS-55-04
- **Unblocks:** HS-55-06
- **Owner:** unassigned

## Problem
A feature that isn't documented honestly doesn't exist for a new user — and
import has three truths (formats need ffmpeg, one speaker label, audio not
kept) that must be stated, not discovered.

## Scope
- **In:**
  - Product-tense documentation of the import flow (web + CLI) and the
    history facets: extend `docs/MEETING_MODE_GUIDE.md` where it fits the
    journey, or a focused guide linked from `docs/README.md` — implementer's
    call, justified in evidence.
  - The honest notes, plainly: WAV works out of the box; mp3/m4a/ogg/flac
    need `ffmpeg` on PATH (with the one-line install hint); imported
    meetings carry a single speaker label; the audio file is not retained;
    everything runs locally; intel applies exactly as for live meetings.
  - `holdspeak import` in whatever CLI reference exists; README touched only
    if a one-liner earns its place (it likely does: "import your existing
    recordings").
- **Out:** internal/architecture docs (the engine is self-documenting +
  evidence); roadmap vocabulary anywhere user-facing.

## Acceptance criteria
- [ ] Docs ship product-tense; the Phase-51 roadmap-vocab guard passes; no
      em/en dashes per `DOCS_STYLE.md`; `humanizer` run and pattern findings
      addressed.
- [ ] The three honest truths are present verbatim-checkably (guarded by the
      doc tests if a cheap assertion fits).
- [ ] Linked from the docs index under the meeting journey.

## Test plan
- `uv run pytest -q tests/unit -k "doc or drift"` + the full suite.

## Notes / open questions
- Keep it short — the Phase-46 voice: honest, journey-grouped, no hype.
