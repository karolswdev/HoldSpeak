# Phase 167 - Project Rooms: The Room in Use

- **Project:** holdspeak
- **Status:** ACTIVE 3/8
- **Chartered:** 2026-09-03 off main `31c072f5` (166 The Jira Parity MERGED via PR #532 on the owner's word — the ELEVENTH Project Rooms phase merged; the SRS V0 slices P0..P7 are all on main)
- **Canon:** docs/internal/CONSTITUTION.md (Article III honest egress); docs/internal/POSITIONING.md (the voice rules); web/src/desk/surface/contract.md (the library contract, HS-156-03); docs/internal/project-rooms/SRS_DOMAIN_DRIVER.md §14 (the V0 slices this phase makes one thing); the owner's laws: face-design-before-build (2026-09-03), the beauty pass after every functional pass (2026-08-17), "will you use this on a Tuesday?" (Phase 139)

## The charter

The arc shipped eight faces in eight sittings, each judged by its own
gallery. Nobody has walked the whole product as ONE thing on the
owner's real desk — and recon found why that matters: **his real
desk holds ZERO projects and ZERO provider connections** (the
`projects` and `watch_provider_connections` tables exist, empty;
`~/.local/share/holdspeak/holdspeak.db`, schema v72). Every Rooms
face has only ever been seen on a rig. The owner picked this phase
over the model-era collapse, 155 The Crew and Gate B (2026-09-03).

The exit, verbatim: **the owner's first real project lives in a Room
on his real desk — created, connected, watched, stewarded and
written up in one attended walk on his real GitHub and his real
Jira site — and his word is that he will use it on a Tuesday.**

Two things stand between today and that exit:

1. **The faces drifted.** Only the Jira wizard (166) was designed on
   the library before it was built; it composes 17 species with
   near-zero hand-rolled markup and the owner said "HECK YES" to
   it. The seven older faces were built brief-first: the Room
   (ProjectRoomCore.tsx, 963 lines) hand-rolls its orientation
   band, focus block and right rail and still imports six private
   sub-paths instead of the barrel; the interview hand-rolls its
   question form and answer rows; the activation review renders a
   raw `<dl>` where a SurfaceLedger belongs; the GitHub wizard
   renders label:value test fields; Review, Update and Steward each
   hand-roll their row internals. None of the seven has a mockup.
   The scroll-hint species exists once, as a private Y-axis copy in
   steward/model.ts. The phase designs the WHOLE Room on the
   library first (mockups at both widths, the owner ratifies), then
   rebuilds every face to the mockups — the Jira wizard is the
   reference implementation, not the exception.
2. **The debts a user hits in a week.** The Jira population toggles
   live only in React state (useSetupController.ts:642/:862); the
   N+1 acli enrichment calls are counted (jira_provider.py:1421)
   but never receipted on the steward face; the acli lock is a
   per-process RLock (jira_provider.py:90) while the MCP sidecar is
   another process; the evaluation cadence is decoded read-only
   (steward/model.ts:210) with no write wire in savePolicy or the
   MCP rules tool; evaluate_due/run_due (workbench_conductor.py:598/
   :619) have no external trigger; four faces have no scroll
   affordance. These are paid BEFORE the beauty pass (functional
   pass first, beauty after — the standing directive).

The chain: 01 the audit + the settled design (mockups; OWNER
RATIFIES — zero code) -> 02 the debts a user hits (functional, no
face change) || 03 the library reform (the species the design
needs, promoted and expanded; the shared glass conftest; every rig
builds first) -> 04 the faces recomposed I (the Room, the interview,
the activation review, the GitHub wizard; shots) -> 05 the faces
recomposed II (Review, Update, Steward postures; shots; the beauty
pass) -> 06 the Tuesday walk (the owner's FIRST project on his real
desk, attended — OWNER VERDICT) || 07 the docs -> 08 the close.

OUT: new capabilities (Jira write effects, MCP-008 remote, Gate B
partner feedback); the model-era collapse (backend, parked); 155 The
Crew; a second Jira account (the owner holds one — the multi-site
proof stays a ledgered debt); the door-title first-match choice
(human either way; ledgered, not pinned).

## Stories

| ID | Story | Status | Story file | Evidence |
| --- | --- | --- | --- | --- |
| HS-167-01 | The audit + the settled design (the whole Room on the library; mockups at 1440 + 393; OWNER RATIFIES) | done | [story-01-the-settled-design](./story-01-the-settled-design.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-167-02 | The debts a user hits (toggles persisted; enrichment receipted; the acli file lock; the cadence write wire; the trigger route) | done | [story-02-the-debts](./story-02-the-debts.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-167-03 | The library reform (scroll-hint + egress species promoted; the design's new species; tokens fenced; the shared glass conftest) | done | [story-03-the-library-reform](./story-03-the-library-reform.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-167-04 | The faces recomposed I (the Room, the interview, the activation review, the GitHub wizard; shots) | backlog | [story-04-the-faces-i](./story-04-the-faces-i.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-167-05 | The faces recomposed II (Review, Update, Steward; shots; the beauty pass) | backlog | [story-05-the-faces-ii](./story-05-the-faces-ii.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-167-06 | The Tuesday walk (the owner's first project on his real desk, attended — OWNER VERDICT) | backlog | [story-06-the-tuesday-walk](./story-06-the-tuesday-walk.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-167-07 | The docs (the Rooms guide re-shot; the library contract; MCP_SIDECAR counts guarded; the dedicated docs story) | backlog | [story-07-the-docs](./story-07-the-docs.md) | [evidence-story-07](./evidence-story-07.md) |
| HS-167-08 | The close (gates, riders, debts, final summary) | backlog | [story-08-the-close](./story-08-the-close.md) | [evidence-story-08](./evidence-story-08.md) |

## Where we are

**CHARTERED 0/8.** Branch `feat/project-rooms-the-room-in-use` off
main `31c072f5`. The owner's pick, 2026-09-03: "167 The Room in
Use" over the model-era collapse, 155 The Crew and Gate B. The PR
#532 merge word, verbatim: "yes the PR is fine, I gave my word...,
you know?" Recon (read-only, anchors re-verified): eight faces,
7,000+ lines under web/src/features/project-room/; one design
canvas in the whole arc (166's, 85d15031-…); the owner's real desk
empty of projects. Story 01 IN PROGRESS: the drift audit
and the settled design written; counsel RATIFY-W-C (18 findings, all
paid — the wings law: nothing retires); the atlas extracted; sixteen
mockup artboards built and read at true size through three bounce
rounds; the canvas published for the owner's word
(https://claude.ai/code/artifact/1dd81936-2c1a-484f-a78e-f56e5a5cf22b).
**HIS WORD (2026-09-03): "PASS — build it."** Story 01 DONE. **03 DONE**
(the library reform: four species/props from D9 in the barrel, the
ONE glass infrastructure with an honest xdist-safe `_ensure_build`,
Jira px tokenized; 252 vitest, 46 glass green). **02 DONE** (the five
debts; three orchestrator catches paid: a submit inside a React state
updater, a trigger route lying about project scope, a swallowed
scheduler error; 72 python + 320 vitest). 04 and 05 build in parallel. 04/05 build to the ratified mockups.

## Active risks

- **Designing eight faces at once invites a mural, not a Room.**
  The settled design is ONE document with per-face sections that
  share a spine: one orientation band species, one ledger-row
  grammar, one chip vocabulary (StateChip / ProvenanceChip /
  EgressChip), one scroll-hint, one footer. A face that needs a
  species the others don't is a finding, not a feature. Counsel
  reads the design before the owner does.
- **A rebuild that changes behavior is a regression wearing a
  redesign.** 04 and 05 recompose markup; the controllers, models
  and wire decoders are untouched except where 02 changes them.
  Every glass rig (158..166) re-runs green on the recomposed faces;
  the old shots sit beside the new in the gallery.
- **The cold-start walk exercises paths no rig has walked:** zero
  projects on the desk, the first connection ever recorded, the
  first steward run against a repo with real history. Expect
  inherited defects (166 found four on the first live tick). The
  walk script is written BEFORE 04 so its first dry run on the
  current faces surfaces them early.
- **Cadence as a write** is a new effect on the steward policy; it
  must ride the existing savePolicy transaction and the MCP
  `project.watch.set_rules` twin, with the range fenced (a floor
  the conductor's tick can honor).
- **The cross-process acli lock** must be a file lock the sidecar
  and the web server share, with a timeout that is a typed error
  (never a hang): the 166 switch-and-verify law extended across
  processes.
- Debts carried in: 166's counsel N (diff_snapshots' else-branch
  assumes jira; the broad enrichment except; find_run_by_watermark's
  100-run scan; the transcript's counts_match; the ActivationReview
  jira label test); 165's remaining N; 164 N-1..N-5; 163 S-4/N-1/
  N-3; 160 N-5/N-1/N-2; 158 S-1/N-1/N-3; 159 seeding walls; 161 N-1.
