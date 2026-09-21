# Phase 202 - The Coherent Face

**Last updated:** 2026-09-21 UTC.

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
| HS-202-02 | First-use doors and truthful state | backlog | [story-02-first-use-doors-and-truthful-state](./story-02-first-use-doors-and-truthful-state.md) | - |
| HS-202-03 | Shared controls on the first-use path become library species | backlog | [story-03-shared-controls-on-the-first-use-path-become-library-species](./story-03-shared-controls-on-the-first-use-path-become-library-species.md) | - |
| HS-202-04 | Names and repeats on the touched flows | backlog | [story-04-names-and-repeats-on-the-touched-flows](./story-04-names-and-repeats-on-the-touched-flows.md) | - |
| HS-202-05 | The type-scale ruling, then the tokens | backlog | [story-05-the-type-scale-ruling-then-the-tokens](./story-05-the-type-scale-ruling-then-the-tokens.md) | - |
| HS-202-06 | The sitting selects the next scope | backlog | [story-06-the-sitting-selects-the-next-scope](./story-06-the-sitting-selects-the-next-scope.md) | - |

## Where we are

Chartered from the surface inventory after Astra's check (two rounds). Order: 01 → 02 → 03 and 04 together → 05 → 06. HS-202-01 has built and verified the fixture fence: normal RED names five desktop and nine narrow defects; strict verification and the unchanged ratchet pass six tests in 86.83s. It does not claim that the first-use path is repaired. Astra owns the delivery; Muad'Dib checked it twice with RATIFY-WITH-CONDITIONS, whose source and proof closure is recorded in [the check](checks/story-01-muaddib.md). The PR is to remain unmerged; inventory PR #594 goes first.

## Lanes

| Lane | Stories | Owner | Checker | Worktree | Branch |
|---|---|---|---|---|---|
| A — first-use fence | HS-202-01 | Astra | Muad'Dib | `/Users/karol/dev/tools/wt-202-01` | `feat/hs-202-01-fence` |
| B — first-use repairs | HS-202-02 | Muad'Dib | Astra | `/Users/karol/dev/tools/wt-202-02` | Assigned by lane B |

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Scope is underspecified | medium | Add concrete stories before implementation | A story cannot name testable acceptance criteria |
| HS-202-01 intentionally makes the default E2E job RED before repairs | certain | PR remains open, unmerged as ordered; HS-202-02 repairs the named failures before phase GREEN. Local verification uses the explicit strict mode; CI is not changed. | Do not treat strict-mode GREEN as product GREEN or merge this lane as a repaired first-use path. |

## Decisions made (this phase)

- 2026-09-20 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.

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

None on the settled harness. Both verdicts and Astra's bounded proof ruling
are preserved in [the built check](checks/story-01-muaddib.md).

## Decisions deferred

- Detailed story breakdown - trigger before implementation begins - default is no code changes without stories.
