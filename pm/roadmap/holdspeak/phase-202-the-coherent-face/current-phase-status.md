# Phase 202 - The Coherent Face

**Last updated:** 2026-09-21 UTC.
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
| HS-202-01 | The first-use fence | done | [story-01-the-first-use-fence](./story-01-the-first-use-fence.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-202-02 | First-use doors and truthful state | done | [story-02-first-use-doors-and-truthful-state](./story-02-first-use-doors-and-truthful-state.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-202-03 | Shared controls on the first-use path become library species | done | [story-03-shared-controls-on-the-first-use-path-become-library-species](./story-03-shared-controls-on-the-first-use-path-become-library-species.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-202-04 | Names and repeats on the touched flows | done | [story-04-names-and-repeats-on-the-touched-flows](./story-04-names-and-repeats-on-the-touched-flows.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-202-05 | The type-scale ruling, then the tokens | done | [story-05-the-type-scale-ruling-then-the-tokens](./story-05-the-type-scale-ruling-then-the-tokens.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-202-06 | The sitting selects the next scope | in-progress | [story-06-the-sitting-selects-the-next-scope](./story-06-the-sitting-selects-the-next-scope.md) | - |

## Where we are

Chartered from the surface inventory after Astra's check (two rounds). Order: 01 → 02 → 03 and 04 together → 05 → 06. HS-202-01 has built and verified the fixture fence: normal RED names five desktop and nine narrow defects; strict verification and the unchanged ratchet pass six tests in 86.83s. It does not claim that the first-use path is repaired. Astra owns the delivery; Muad'Dib checked it twice with RATIFY-WITH-CONDITIONS, whose source and proof closure is recorded in [the check](checks/story-01-muaddib.md). The PR is to remain unmerged; inventory PR #594 goes first.

Follow-up, 2026-09-21: the fence now follows editor autosave and Go's phone
menu fold. Pinned inventory still reports the exact five/nine defects;
strict mode plus the ratchet passes six tests in 92.95s. Story 02 at
3595fcb6 completes both widths but remains default RED: import refresh at
both widths and off-screen Object/Window entries in Go at 393. The receipt,
summary refresh and restart legs pass. The requested compatibility result
is partial, recorded in [the follow-up evidence](evidence-story-01.md#follow-up-result--partial-2026-09-21-utc).
The story remains done and PR #596 remains unmerged.

## Lanes

| Lane | Stories | Owner | Checker | Worktree | Branch |
|---|---|---|---|---|---|
| A — first-use fence | HS-202-01 | Astra | Muad'Dib | `/Users/karol/dev/tools/wt-202-01` | `feat/hs-202-01-fence` |
| B — first-use repairs | HS-202-02 | Muad'Dib | Astra | `/Users/karol/dev/tools/wt-202-02` | Assigned by lane B |

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
| HS-202-01 intentionally makes the default E2E job RED before repairs | certain | PR remains open, unmerged as ordered; HS-202-02 repairs the named failures before phase GREEN. Local verification uses the explicit strict mode; CI is not changed. | Do not treat strict-mode GREEN as product GREEN or merge this lane as a repaired first-use path. |

## Decisions made (this phase)

- 2026-09-20 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.

## Ledger

- 2026-09-21: `tests/unit/test_phase200_continuity.py::test_the_last_known_observation_survives_a_restart` fails on pristine main 13bbe8bc: the seeded 2026-09-07 observation aged past the last-known store's horizon; a clock time bomb like the calendar one below. Owner: the next green lane.
- 2026-09-20: `tests/unit/test_hs175_calendar_sources.py::test_matched_this_week` and `test_hs175_calendar_wire.py::test_week_strip_with_events` fail at a week boundary (Sunday evening local, Monday UTC) on pristine main 93f9524f; a clock time bomb like the one HS-201-08 paid for HS-171; not this phase's change. Owner: the next green lane.
- 2026-09-20: the first-run card (FirstWords) mixes four button species and three type stacks on one 620 px card marooned on a black screen, hiding the Workbench instead of introducing it (shot story-02-shots/first-run-mic-refused-1440.png). A design beat for the canvas (the desk visible behind one real window; one scale, one species; the mic as the field's own affordance), after story 05 settles the scale. Not a patch.
- 2026-09-21 (found by HS-202-03, **INHERITED at 73758ef3**) — **Escape from a menu-bar menu drops focus to the body.** `WorkMenu` accepts `returnFocus` (`web/src/desk/components/DeskMenu.tsx:455`, consumed at `:559`/`:562`); `DeskMenuBar` renders it without the prop (`web/src/desk/components/DeskMenuBar.tsx:134-144`; at the base, `73758ef3:…/DeskMenuBar.tsx:133-143`, `grep -c returnFocus` = 0). One prop plus a rig assertion. **Owner: the next face lane in this phase** (04 if it reopens the menus, otherwise 06's follow-up charter) — not story 05, which is tokens.
- 2026-09-21 (found by HS-202-03, **INHERITED at 73758ef3 by paired measurement**) — **under `prefers-reduced-motion: reduce` 18 of 26 keyboard stops on the cold desk compute a zero focus outline**: the desk-chrome controls (`.desk-mark`, `.desk-verbbar-title`, `.desk-bell`, the egress badge, every dock chip, `.surface-ledger-line`, the mic) while the plated `.btn` verbs keep 2px on the same page. Paired reproduction in `phase-202-the-coherent-face/assets/story-03-shots/reduced-motion-paired-baseline.json`: same hub, same page, same controls, same emulation, three rounds, only the built bundle swapped between `73758ef3` and the branch — **base 18/26 ringless, branch 17-18/26, and ZERO controls ringless only on the branch**. Mechanism **UNKNOWN**; ruled out are a reduced-motion outline reset (none in the built CSS) and the token (`--focus-outline-width` computes to `2px` on the ringless elements). The ringless elements compute `outline-color: currentColor`, the initial value, so the one global `:focus-visible` outline rule did not apply to them at all — a **cascade** question, not a token question. The 2026-09-20 census measured its 69 tab stops WITHOUT reduced motion, which is why it reported zero ringless stops; its "focus rings on every tab stop" pass therefore does not cover this state. **Owner: a chartered fix lane in this phase before story 06's sitting** — explicitly NOT story 05, whose tokens do not reach a cascade defect.
- 2026-09-20: `FIRST_VALUE_FAILURES` (holdspeak/db/onboarding.py) refuses three names the face can send (`mic_interval_closed`, `provider_failure`, `audio_floor_held`); pinned as a named gap by tests/unit/test_hs202_first_value_failure_vocabulary.py; one line, next lane.
- 2026-09-20 — HS-202-01 acceptance clarified from the owner's lane brief: ship the normal RED fence and strict expected-failure verification before product repairs. The generic face-repair checklist does not assert that this harness-only story repairs the face. The phase's green-on-main exit remains unchanged.

- 2026-09-20 — The built fixture walk adds an explicit `import-refresh` check: the imported transcript loads, but the stale selected row withholds Run summary. Home: HS-202-02. It also distinguishes Notes query ranking from Enter dispatch; exact-title note search works. These are visible amendments, which the owner may overrule at the sitting.

## Verification ledger

The full isolated suite returned 8 failed / 11,299 passed / 116 skipped /
4 xfailed. Both fence cases passed in strict mode. Two inherited metadata
failures are fixed; two runtime failures reproduce on pinned base 50ca0dd6;
four flakes passed twice serially on this lane. Web: 2,645 passed.
[The ledger](verification-ledger-story-01.md) names every failure, its
classification and follow-up. No full-suite GREEN or real-voice claim.

## Open dissents

The original delivery's verdicts and Astra's bounded proof ruling are
preserved in [the built check](checks/story-01-muaddib.md). The follow-up
records the wording interpretation below.

Follow-up wording distinction, 2026-09-21: the owner asked to “record the
editor-scoped receipt text before Save, click Save, and assert a NEW
receipt,” while requiring default GREEN on story 02 with no product repair.
At 3595fcb6, Save only closes the editor and its receipt. Astra and Muad'Dib
therefore interpret freshness across the edit: absent before typing,
visible Kept after the successful autosave, then Save closes and the exact
text persists. No new after-click receipt is claimed. This interpretation,
the pending clarification and the owner's right to overrule are explicit in
[the follow-up check](checks/story-01-followup-muaddib.md).

- 2026-09-21 - The 44 px hit halo lives in a viewport media query and global.css joins the container-query law allowlist: most Buttons at 393 (dock, menu bar, Chair shell, first-run) sit outside every named surface container; chair.css:566 is the precedent - tenet 1 - Muad'Dib, on the worker's disclosure.
- 2026-09-21 - The 126 ember contrast pairs (59 of them the filled primary Button) stay: no light foreground reaches 4.5:1 on the ember accent, only a near-black one, which repaints every filled primary. A look change the owner sees before it is made: decided at the sitting (story 06), recorded in story 05's Notes with the arithmetic.

## Decisions deferred

- Detailed story breakdown - trigger before implementation begins - default is no code changes without stories.

## The sitting — findings, 2026-09-21/22 (HS-202-06)

The owner wiped his desk to a fresh database (parked, not deleted, at
`~/.local/share/holdspeak-parked/2026-09-21-191251/`), logged in, and met two
basics in his first two clicks. Both fixed on 2026-09-22 before his demo; both
fences fail pre-fix.

1. **"Desk memory" → a sweep row → Open does nothing.** The row is a
   pipeline-event receipt (`holdspeak/db/projections.py::_pipeline_events`)
   whose door was `/`; the shade's `openSource` fell through to
   `openPrimitive(event_id)`, which resolves nothing, silently. Now: the sweep
   receipt's door is the Rhythm face (`/cadence`); a receipt with no face
   behind it carries no door and the shade, the Desk memory window and the
   ambient card draw no Open for it. Fences:
   `tests/unit/test_hs174_reach_wire.py::TestSittingReceiptDoors`,
   `web/src/desk/components/__tests__/shadeDoorless202.test.tsx`.
2. **"No brief yet" → Generate → the whole row disappears; a day later, still
   no brief.** Generate worked (a `monday_briefs` row at 19:37:43, headline
   "Nothing material changed.", zero items). The face had no branch for an
   empty brief after a reload (`brief` set, no untriaged rows, no receipt in
   state) so the section rendered `null`, and the Generate verb went with it.
   Now: the section keeps the brief's own headline, the receipt when this
   gesture made it, and "Generate again". Fence:
   `briefReceiptRendered202.test.tsx` ("shows an empty brief's own words…").

Still open from the same two clicks (ledgered, not fixed): the dock launcher
labelled "Desk memory" opens the shade titled "Missed" (already in the
ledger above); the assigned intel profile on a fresh desk points at a missing
`legacy-intel` (`meeting intel destination unavailable`, log 23:15/23:16) —
step 2 of the sitting is where he chooses an engine.
