# HS-67-03 — Scenario library + fixture generator

- **Project:** holdspeak
- **Phase:** 67
- **Status:** built (awaiting commit)
- **Depends on:** HS-67-01, HS-67-02
- **Owner:** unassigned

## Problem

The protocol needs real audio to feed the program — meetings with multiple
speakers and dictation in different voices and languages — plus deterministic
transcript files for the import path. Hand-recording is not repeatable; the
fixtures must regenerate from source.

## Scope

- **In:** `dogfood/scenarios/*.yaml` (6 meetings covering architect, incident,
  product, delivery, balanced; 6 dictation sets: per-repo coding tasks, German,
  spoken-symbols, voice-macros), `dogfood/make_fixtures.py` (+ `.sh` wrapper)
  that renders each line via `say -v <voice> --data-format=LEI16@16000` into
  16 kHz mono WAV (one combined clip per meeting, one per dictation utterance)
  and writes a ground-truth `*.script.txt` + `MANIFEST.json`; committed
  `dogfood/transcripts/*.{vtt,srt,txt}`; the opt-in plumbing pytest
  `tests/e2e/test_dogfood_plumbing_e2e.py`.
- **Out:** committing the generated audio (gitignored); the manual protocol steps.

## Acceptance criteria

- [ ] `make_fixtures.py --list` / `--dry-run` enumerate all scenarios; a real
      render produces valid 16 kHz mono WAVs (verified with `wave`).
- [ ] Meeting scenarios cover all five MIR profiles plus balanced; dictation
      covers grounding (3 repos), a non-English language, spoken symbols, macros.
- [ ] The committed `.vtt` (voice spans), `.srt`, and `.txt` each parse via
      `parse_transcript` into cues with ≥2 distinct speakers.
- [ ] `HOLDSPEAK_DOGFOOD=1 uv run pytest -q tests/e2e/test_dogfood_plumbing_e2e.py`
      passes; the file skips cleanly without the flag.

      See `evidence-story-03.md`.

## Test plan

- Unit: the plumbing pytest (scenario shape, repo load, transcript parse,
  profile coverage).
- Manual: `make_fixtures.py --only meeting-questline-balanced-sync`; listen /
  inspect the WAV + script; `dogfood/hs import` the result.

## Notes / open questions

- VTT speakers require `<v Name>` spans (parser ignores `Name:` in VTT bodies) —
  the committed fixture honors this; caught at scaffold by the pytest.
- Audio is gitignored to keep the repo light; the generator is the source of truth.
