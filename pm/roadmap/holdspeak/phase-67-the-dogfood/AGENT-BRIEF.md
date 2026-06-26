# Phase 67 — Agent Brief (read this first)

**Phase 67 — The Dogfood** for HoldSpeak. Opened 2026-06-14 on owner direction:
"create a dogfooding phase in the form of a thorough, easy-to-fill test protocol
for the end user, on believable data — mock repos with completed stages and
`.hs/` files, meetings rendered through `say` with different voices, fed to the
program, then verification."

## 0. Mission

Give the owner a repeatable way to exercise **all** of HoldSpeak the way a user
does, on real metal, against believable data, and to record what works in a
fillable artifact that survives across releases. This is a confidence instrument,
not a feature: the deliverable is a harness + a protocol, plus a thin automated
guard so the harness can't silently rot.

## 1. The one thing you must not get wrong

**The dogfood must be isolated.** Running it must never touch the owner's real
`~/.config/holdspeak` or `~/.local/share/holdspeak`. Everything runs under a
sandbox `HOME` (`dogfood/_home`) via `dogfood/hs`. The last cross-cutting check
(X-05) exists to prove this held.

## 2. Rules (the standing set)

- PMO gate: every shipping commit needs a fresh `.tmp/CONTRACT.md`; flip the
  story header + this phase's `current-phase-status.md` row + "Where we are" +
  the roadmap README "Last updated" in the same commit.
- Tests ran means ran: `uv run pytest -q` (exclude `tests/e2e/test_metal.py`).
  The dogfood plumbing pytest is opt-in: `HOLDSPEAK_DOGFOOD=1 uv run pytest -q
  tests/e2e/test_dogfood_plumbing_e2e.py`.
- Dedicated docs story before closeout (HS-67-05).
- Merge each phase to `main` via PR on green CI.

## 3. Ground truth (verified at scaffold)

- Config dir is `~/.config/holdspeak`, DB is `~/.local/share/holdspeak` — both
  key off `Path.home()`, so a sandbox `HOME` fully isolates a run. No env
  override for those paths exists; `HOME` is the lever.
- The intel/dictation LLM points at `.43` via `meeting.intel_provider="cloud"` +
  `intel_cloud_base_url` and `dictation.runtime.backend="openai_compatible"`.
- `say -v <voice> --data-format=LEI16@16000 -o out.wav "text"` yields Whisper's
  native 16 kHz mono PCM. Concatenating those WAVs (same params) makes one
  meeting clip.
- Project anchors are `.hs/` + `.holdspeak/` (and `pyproject.toml`), not `.git`.
  The mock repos are intentionally not git repos.
- VTT speakers come from `<v Name>` voice spans; SRT/TXT from a `Name:` prefix
  (≤3 words, blocklist of structural labels). The committed fixtures honor this.
- The doc/voice guards scan `docs/*.md` + root README only — `dogfood/**` and
  `pm/roadmap/**` are out of scope, so HS-IDs and prose dashes are fine here.

## 4. Stories

- **HS-67-01 — The isolated harness scaffold.** `dogfood/` skeleton:
  `setup.sh` (sandbox HOME + tier-1/tier-2 config, cache symlinks), `hs` runner,
  `env.sh`, `.gitignore`, `README.md`. Isolation is the contract.
- **HS-67-02 — The mock repo fleet.** `dogfood/repos/{ledgerline,questline,
  pylon-infra}` — each with `.hs/` context, a `.holdspeak/project.yaml` KB, a
  real-ish source tree, and completed-stage evidence (`STAGES.md`, ADRs,
  postmortems) seeding the meeting scenarios.
- **HS-67-03 — The scenario library + fixture generator.** `scenarios/*.yaml`
  (6 meetings across all 5 MIR profiles + balanced; 6 dictation sets incl.
  German, spoken-symbols, macros), `make_fixtures.py` (say → 16 kHz audio +
  ground-truth scripts), committed `transcripts/*.{vtt,srt,txt}`.
- **HS-67-04 — The master protocol.** `dogfood/PROTOCOL.md` (two tiers, ~58
  fillable checks covering every surface) + `RESULTS-TEMPLATE.md`.
- **HS-67-05 — Docs wiring.** Wire the harness into the contributor docs
  (CONTRIBUTING / docs index) and the roadmap; keep voice-guard clean.
- **HS-67-06 — Closeout: a recorded run.** Drive the protocol once on real
  metal, file the findings, drop a filled `dogfood/results/<date>.md`, write
  `final-summary.md`. The phase is not done until a run is on record.

## 5. Gotchas

- Don't commit `_audio/` or `_home/` — both are gitignored; regenerate.
- `say` voices vary per Mac; `make_fixtures.py` falls back if a named voice is
  missing, but German (`Anna`) is needed for the language check — confirm it's
  installed.
- Intel is non-deterministic. Protocol checks judge **substance** (did it find
  the decision/owners/risk?), not exact wording. Don't write brittle assertions
  into the automated tier — keep the LLM-shaped judgments manual.
- The tier-2 config enables macros incl. a `shell` macro. That's deliberate for
  the sandbox, but it means `make_fixtures` / setup wires real actions — note it
  in any demo.
- Re-running `setup.sh` won't overwrite an existing config without `--force`.
