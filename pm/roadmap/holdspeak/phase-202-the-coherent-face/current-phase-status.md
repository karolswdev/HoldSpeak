# Phase 202 - The Coherent Face

**Last updated:** 2026-09-20.

## Goal

Every face on the owner's first-use path has a door at every width, tells the truth, and is built from the library; a small fence keeps it so; the sitting selects the next scope.

## Scope

- **In:** the six stories below, sized to the owner's first-use path (docs/internal/SURFACE-INVENTORY-2026-09-20.md §6).
- **Out:** the inventory's ledger; the broad census numbers as gates.

## Exit criteria (evidence required)

- [ ] The first-use smoke (story 01) is green at 1440 and 393 on main.
- [ ] The owner sits on the merged phase and his line closes it (story 06); the sober eye re-runs; the census re-runs as a diagnostic beside the 2026-09-20 numbers.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-202-01 | The first-use fence | backlog | [story-01-the-first-use-fence](./story-01-the-first-use-fence.md) | - |
| HS-202-02 | First-use doors and truthful state | done | [story-02-first-use-doors-and-truthful-state](./story-02-first-use-doors-and-truthful-state.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-202-03 | Shared controls on the first-use path become library species | backlog | [story-03-shared-controls-on-the-first-use-path-become-library-species](./story-03-shared-controls-on-the-first-use-path-become-library-species.md) | - |
| HS-202-04 | Names and repeats on the touched flows | backlog | [story-04-names-and-repeats-on-the-touched-flows](./story-04-names-and-repeats-on-the-touched-flows.md) | - |
| HS-202-05 | The type-scale ruling, then the tokens | done | [story-05-the-type-scale-ruling-then-the-tokens](./story-05-the-type-scale-ruling-then-the-tokens.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-202-06 | The sitting selects the next scope | backlog | [story-06-the-sitting-selects-the-next-scope](./story-06-the-sitting-selects-the-next-scope.md) | - |

## Where we are

Chartered from the surface inventory after Astra's check (two rounds). Order: 01 → 02 → 03 and 04 together → 05 → 06. Lanes assigned at build time.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Scope is underspecified | medium | Add concrete stories before implementation | A story cannot name testable acceptance criteria |

## Decisions made (this phase)

- 2026-09-20 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.

## Ledger

- 2026-09-20: `tests/unit/test_hs175_calendar_sources.py::test_matched_this_week` and `test_hs175_calendar_wire.py::test_week_strip_with_events` fail at a week boundary (Sunday evening local, Monday UTC) on pristine main 93f9524f; a clock time bomb like the one HS-201-08 paid for HS-171; not this phase's change. Owner: the next green lane.
- 2026-09-20: the first-run card (FirstWords) mixes four button species and three type stacks on one 620 px card marooned on a black screen, hiding the Workbench instead of introducing it (shot story-02-shots/first-run-mic-refused-1440.png). A design beat for the canvas (the desk visible behind one real window; one scale, one species; the mic as the field's own affordance), after story 05 settles the scale. Not a patch.
- 2026-09-20: `FIRST_VALUE_FAILURES` (holdspeak/db/onboarding.py) refuses three names the face can send (`mic_interval_closed`, `provider_failure`, `audio_floor_held`); pinned as a named gap by tests/unit/test_hs202_first_value_failure_vocabulary.py; one line, next lane.

- 2026-09-21 - The 44 px hit halo lives in a viewport media query and global.css joins the container-query law allowlist: most Buttons at 393 (dock, menu bar, Chair shell, first-run) sit outside every named surface container; chair.css:566 is the precedent - tenet 1 - Muad'Dib, on the worker's disclosure.
- 2026-09-21 - The 126 ember contrast pairs (59 of them the filled primary Button) stay: no light foreground reaches 4.5:1 on the ember accent, only a near-black one, which repaints every filled primary. A look change the owner sees before it is made: decided at the sitting (story 06), recorded in story 05's Notes with the arithmetic.

## Decisions deferred

- Detailed story breakdown - trigger before implementation begins - default is no code changes without stories.
