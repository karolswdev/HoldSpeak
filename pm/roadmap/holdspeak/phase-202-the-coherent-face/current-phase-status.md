# Phase 202 - The Coherent Face

**Last updated:** 2026-09-21.

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
| HS-202-03 | Shared controls on the first-use path become library species | done | [story-03-shared-controls-on-the-first-use-path-become-library-species](./story-03-shared-controls-on-the-first-use-path-become-library-species.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-202-04 | Names and repeats on the touched flows | backlog | [story-04-names-and-repeats-on-the-touched-flows](./story-04-names-and-repeats-on-the-touched-flows.md) | - |
| HS-202-05 | The type-scale ruling, then the tokens | backlog | [story-05-the-type-scale-ruling-then-the-tokens](./story-05-the-type-scale-ruling-then-the-tokens.md) | - |
| HS-202-06 | The sitting selects the next scope | backlog | [story-06-the-sitting-selects-the-next-scope](./story-06-the-sitting-selects-the-next-scope.md) | - |

## Where we are

Chartered from the surface inventory after Astra's check (two rounds). Order: 01 → 02 → 03 and 04 together → 05 → 06. Lanes assigned at build time.

02 and 03 are built. 03 took the raw-button ratchet from **174 to 106**: the
shared species themselves — every menu item, every wing tab, the dock, the
editor's rail — and every raw control on the five jobs' screens now draw
through the library `Button`, most of them through its new `chrome` variant
(the species without the plate, so each strip keeps its own material; no
stylesheet defines `btn--chrome`, and a vitest fences that). 68 sites, 31
files. Story 01's fence is green at both widths on this tree. 04 is in a
sibling lane (labels and repeats) and does not overlap 03's files by design:
03 touched species, never a label string. Counsel #598 returned
RATIFY-WITH-CONDITIONS on 03 and all four conditions are closed in the same
worktree: the rig's overclaims corrected (it proves the keys it presses, not
complete keyboard or pixel identity), the reduced-motion ring loss settled as
INHERITED by a paired reproduction against 73758ef3, Escape's missing
`returnFocus` ledgered with file:line, and all six Philo inventories
regenerated and re-checked. Two ledger rows below carry owners inside this
phase rather than riding on story 05. 03 then paid the touch targets story
05's measurement found on its two strips: ten rows under 44 px at 393 (the
four wing tabs and the gear door at 23-24 px, the overview/reset keys at
22 px, the Record orb at 40 px, the two Room verbs at 36 px) are now 44 px in
each strip's own phone-width CSS, fenced in the species rig, with the 1440
face proven unchanged by a paired bundle swap (19 rows, 0 changed).

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Scope is underspecified | medium | Add concrete stories before implementation | A story cannot name testable acceptance criteria |

## Decisions made (this phase)

- 2026-09-20 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.

## Ledger

- 2026-09-20: `tests/unit/test_hs175_calendar_sources.py::test_matched_this_week` and `test_hs175_calendar_wire.py::test_week_strip_with_events` fail at a week boundary (Sunday evening local, Monday UTC) on pristine main 93f9524f; a clock time bomb like the one HS-201-08 paid for HS-171; not this phase's change. Owner: the next green lane.
- 2026-09-20: the first-run card (FirstWords) mixes four button species and three type stacks on one 620 px card marooned on a black screen, hiding the Workbench instead of introducing it (shot story-02-shots/first-run-mic-refused-1440.png). A design beat for the canvas (the desk visible behind one real window; one scale, one species; the mic as the field's own affordance), after story 05 settles the scale. Not a patch.
- 2026-09-21 (found by HS-202-03, **INHERITED at 73758ef3**) — **Escape from a menu-bar menu drops focus to the body.** `WorkMenu` accepts `returnFocus` (`web/src/desk/components/DeskMenu.tsx:455`, consumed at `:559`/`:562`); `DeskMenuBar` renders it without the prop (`web/src/desk/components/DeskMenuBar.tsx:134-144`; at the base, `73758ef3:…/DeskMenuBar.tsx:133-143`, `grep -c returnFocus` = 0). One prop plus a rig assertion. **Owner: the next face lane in this phase** (04 if it reopens the menus, otherwise 06's follow-up charter) — not story 05, which is tokens.
- 2026-09-21 (found by HS-202-03, **INHERITED at 73758ef3 by paired measurement**) — **under `prefers-reduced-motion: reduce` 18 of 26 keyboard stops on the cold desk compute a zero focus outline**: the desk-chrome controls (`.desk-mark`, `.desk-verbbar-title`, `.desk-bell`, the egress badge, every dock chip, `.surface-ledger-line`, the mic) while the plated `.btn` verbs keep 2px on the same page. Paired reproduction in `phase-202-the-coherent-face/assets/story-03-shots/reduced-motion-paired-baseline.json`: same hub, same page, same controls, same emulation, three rounds, only the built bundle swapped between `73758ef3` and the branch — **base 18/26 ringless, branch 17-18/26, and ZERO controls ringless only on the branch**. Mechanism **UNKNOWN**; ruled out are a reduced-motion outline reset (none in the built CSS) and the token (`--focus-outline-width` computes to `2px` on the ringless elements). The ringless elements compute `outline-color: currentColor`, the initial value, so the one global `:focus-visible` outline rule did not apply to them at all — a **cascade** question, not a token question. The 2026-09-20 census measured its 69 tab stops WITHOUT reduced motion, which is why it reported zero ringless stops; its "focus rings on every tab stop" pass therefore does not cover this state. **Owner: a chartered fix lane in this phase before story 06's sitting** — explicitly NOT story 05, whose tokens do not reach a cascade defect.
- 2026-09-20: `FIRST_VALUE_FAILURES` (holdspeak/db/onboarding.py) refuses three names the face can send (`mic_interval_closed`, `provider_failure`, `audio_floor_held`); pinned as a named gap by tests/unit/test_hs202_first_value_failure_vocabulary.py; one line, next lane.

## Decisions deferred

- Detailed story breakdown - trigger before implementation begins - default is no code changes without stories.
