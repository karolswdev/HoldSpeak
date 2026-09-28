# PHILO-9-05 - The atlas: assembly, rerun and equivalence

- **Project:** holdspeak-philo
- **Phase:** 9
- **Status:** done
- **Depends on:** PHILO-9-01, PHILO-9-02, PHILO-9-03, PHILO-9-04, PHILO-9-07 (each ships its own fences and atlas cases)
- **Unblocks:** PHILO-9-06
- **Owner:** Astra (Luna); Muad'Dib checks
- **Closure finding:** Phase 7 exit 4 and Phase 8 exit 5 (the method); Codex Astra r1 F7, F8 (`checks/charter-astra-r1.md`)
- **Canvas:** none

## Problem

Stories 01–04 each ship the executable fences and atlas cases for their own repairs, with their red-first record. Nothing yet runs them together with the Phase 7 and Phase 8 cases, or checks that the api, `op` and browser paths agree on the same outcomes. Authoring the cases a second time here would duplicate work (Tenet 1).

## Scope

- **In:** assemble the Phase 9 cases stories 01–04 and 07 shipped (story 07's grant cases included, R4-4) into the phase atlas file (fixed by story 01's first case against `docs/internal/philo/graph/atlas.schema.json`); apply the general atlas fences to it (Phase 8 law: they read `atlas.json` only); rerun every Phase 7, Phase 8 and Phase 9 case at 1440 and 393 on the phase head; run the api/`op`/browser equivalence for each durable outcome, including each admitted write's kernel receipt read with its actor; report the atlas counts over the named files.
- **Out:** authoring a new face case (a gap goes back to the story that owns the seam); any product change.

## Acceptance criteria

- [x] Every Phase 9 case passes at the widths the charter's red-first matrix names, on the phase head; each case's red (or preservation green) record is the one its story kept — this story claims no new red.
- [x] The Phase 7 and Phase 8 atlas cases still pass; the counts are reported.
- [x] The api/`op`/browser equivalence holds for each durable outcome and refusal; real and replayed runs are retained apart.

## Effort (not a promise)

PROVISIONAL: 0.5–1 engineering day.

## Test plan

- **Integration:** `scripts/graph_walk.py run --atlas <file> --case <id> --viewport 1440|393 --engine none` for each case, `--out` under this phase's assets; the Phase 7 and Phase 8 atlas re-run.

## Notes

- 2026-09-27 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
- 2026-09-27 — round two (Codex Astra r1 F7 paid): assembly, rerun and equivalence only; the file keeps its name for the story link.
- 2026-09-28 — built by the Fedaykin lane (Opus 5.5) for Muad'Dib on main `79fdee3c` (stories 01, 02, 03, 04, 07 merged). The census, the five authored gaps, the reruns and the equivalence are in `evidence-story-05.md`. Muad'Dib's brief allowed authoring "only the gaps the census proves"; the Scope's "Out: authoring a new face case" is overridden by that brief for the three face cases below, and each is named as such. The steward file (`atlas-phase9-steward.json`) is not folded into `atlas-phase9.json`: story 02's retained observations under `docs/internal/philo/graph/observations/muaddib/` name its path and sha256, and the owner rules "never delete, park instead". The phase atlas is the two files; `tests/unit/test_philo9_atlas.py` applies the general fences to both.
