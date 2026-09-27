# PHILO-9-05 - The atlas: assembly, rerun and equivalence

- **Project:** holdspeak-philo
- **Phase:** 9
- **Status:** backlog
- **Depends on:** PHILO-9-01, PHILO-9-02, PHILO-9-03, PHILO-9-04, PHILO-9-07 (each ships its own fences and atlas cases)
- **Unblocks:** PHILO-9-06
- **Owner:** Astra (Luna); Muad'Dib checks
- **Closure finding:** Phase 7 exit 4 and Phase 8 exit 5 (the method); Codex Astra r1 F7, F8 (`checks/charter-astra-r1.md`)
- **Canvas:** none

## Problem

Stories 01–04 each ship the executable fences and atlas cases for their own repairs, with their red-first record. Nothing yet runs them together with the Phase 7 and Phase 8 cases, or checks that the api, `op` and browser paths agree on the same outcomes. Authoring the cases a second time here would duplicate work (Tenet 1).

## Scope

- **In:** assemble the Phase 9 cases the stories shipped into the phase atlas file (fixed by story 01's first case against `docs/internal/philo/graph/atlas.schema.json`); apply the general atlas fences to it (Phase 8 law: they read `atlas.json` only); rerun every Phase 7, Phase 8 and Phase 9 case at 1440 and 393 on the phase head; run the api/`op`/browser equivalence for each durable outcome, including each admitted write's kernel receipt read with its actor; report the atlas counts over the named files.
- **Out:** authoring a new face case (a gap goes back to the story that owns the seam); any product change.

## Acceptance criteria

- [ ] Every Phase 9 case passes at the widths the charter's red-first matrix names, on the phase head; each case's red (or preservation green) record is the one its story kept — this story claims no new red.
- [ ] The Phase 7 and Phase 8 atlas cases still pass; the counts are reported.
- [ ] The api/`op`/browser equivalence holds for each durable outcome and refusal; real and replayed runs are retained apart.

## Effort (not a promise)

PROVISIONAL: 0.5–1 engineering day.

## Test plan

- **Integration:** `scripts/graph_walk.py run --atlas <file> --case <id> --viewport 1440|393 --engine none` for each case, `--out` under this phase's assets; the Phase 7 and Phase 8 atlas re-run.

## Notes

- 2026-09-27 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
- 2026-09-27 — round two (Codex Astra r1 F7 paid): assembly, rerun and equivalence only; the file keeps its name for the story link.
