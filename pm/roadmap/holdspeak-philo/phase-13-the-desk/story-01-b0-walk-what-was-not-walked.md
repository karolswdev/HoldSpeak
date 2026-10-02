# PHILO-13-01 - B0 Walk what was not walked

- **Project:** holdspeak-philo
- **Phase:** 13
- **Status:** in-progress
- **Depends on:** the owner's ratification of this charter
- **Unblocks:** PHILO-13-07 (B2's merge record must cite this story's merged commit and `evidence-story-01.md`); every story's atlas cases (H-B0a, H-B0b); every consolidation move that reaches an unwalked path
- **Owner:** Astra (Luna, xhigh); Muad'Dib checks
- **Lane:** Data + truth (`../wt-philo-13-astra`, `feat/philo-13-astra`)
- **Proposal:** B0 (PROPOSAL §3, Wave B)
- **Closure finding:** `grounding/checks/proposal-astra.md` MISSED 2; `grounding/checks/faces-astra.md` finding 5
- **Canvas:** none

`grounding/` = `docs/internal/philo/phase-13/grounding/`.

## Goal

Every Desk path the grounding did not walk has an actual atlas case at both widths before B2 changes the shared window lifecycle, so the change cannot break a path nobody has seen.

## Problem

Nine paths are unwalked (`grounding/faces-surfaces.md:59`, `:219`; `grounding/faces.md:33`). The faces lane used `graph_walk.py serve`, not `run`: its observations are direct Playwright, not atlas cases (`grounding/faces-surfaces.md:15`). Astra's four atlas runs cover J5 only (`grounding/structure.md:34-46`). B2 changes how every object window opens, closes and returns (`web/src/desk/store/compositorSlice.ts:126`, `web/src/desk/store/windowFactory.ts:30`); these paths ride that lifecycle.

| Unwalked path | Where it mounts (S0) |
|---|---|
| Calendar snapshot | `web/src/desk/applications.ts:416-429`; doors `web/src/desk/components/GlassDropLayer.tsx:65-69`, `web/src/pages/cores/SettingsCore.tsx:2115` (`grounding/inventory.md:80`) |
| Roadmap window | `web/src/desk/DeskApp.tsx:269-275`; `web/src/desk/components/RoadmapWindow.tsx:72-119` (`grounding/inventory.md:117`) |
| Repository window | `web/src/desk/DeskApp.tsx:276-282`; `web/src/desk/components/RepoWindow.tsx:176-271` (`grounding/inventory.md:118`) |
| Delivery dossier | `web/src/desk/DeskApp.tsx:267`; `web/src/desk/components/DeliveryDossierWindow.tsx:58-96` (`grounding/inventory.md:115`) |
| Delivery terminal | `web/src/desk/DeskApp.tsx:268`; `web/src/desk/components/DeliveryTerminalWindow.tsx:160-236` (`grounding/inventory.md:116`) |
| Chain pullout | `web/src/desk/pullouts/registry.ts:33` (`grounding/inventory.md:174`) |
| Coder pullout | `web/src/desk/pullouts/registry.ts:35` (`grounding/inventory.md:176`) |
| Directory pullout / Zone window | `web/src/desk/pullouts/registry.ts:36`; `web/src/desk/gl/WorldStage.tsx:272-274`; Object Open intercept `web/src/desk/verbRegistry.ts:399-411` (`grounding/inventory.md:148`, `:177`) |
| Info window | `web/src/desk/gl/WorldStage.tsx:275-277`; `web/src/desk/components/InfoWindow.tsx:85-140` (`grounding/inventory.md:149`) |

## Scope

- **In:**
  - **H-B0a:** create `docs/internal/philo/graph/atlas-phase13-astra.json`, valid against `atlas.schema.json`; this lane writes only that file. The faces lane creates and owns `atlas-phase13-muaddib.json` with its first case. `tests/unit/test_philo_graph_atlas.py:27` already globs `atlas*.json`, so neither file needs registering.
  - **H-B0b:** `tests/unit/test_philo_graph_atlas.py:492` (the hard-coded `.op` sibling count, 69) counts siblings outside `atlas-phase13-*` only; `tests/unit/test_philo13_astra_atlas.py` (this lane's) asserts the Astra file's count; the faces lane's `tests/unit/test_philo13_muaddib_atlas.py` asserts its own. After this story no lane edits `test_philo_graph_atlas.py`. **H-B0b filters the count only** (Astra charter r2 F4): every shared semantic check in `test_philo_graph_atlas.py` (durable reads, predicates, triggers, captured read arguments; e.g. `:469`, `:551`) keeps running over **both** `atlas-phase13-*` files through the `:27` glob; the acceptance shows one such check failing on a deliberately broken Phase 13 case before the fix.
  - One atlas case per path above (open, the first useful face, close, and return after reload where the path has a window), set through real production entry points (`api`, `ui`, `fixture`, `cli` steps), at 1440 and at 393 with touch. A repository-backed fixture for the Roadmap/Repository/Delivery paths, made in the run's own HOME. Each case's verdict and a one-line finding table in the story's evidence.
- **Out:** fixing what the walk finds (each defect is ledgered to the story whose face owns it, or to BACKLOG); any consolidation move; the Floor itself (Zone and Info are inventoried boundary surfaces only, `grounding/structure.md:257`).

## Acceptance criteria

- [ ] H-B0a and H-B0b merged first: `atlas-phase13-astra.json` and its count fence exist; the shared count excludes `atlas-phase13-*`; `test_philo_graph_atlas.py` passes.
- [ ] Each of the nine paths has an atlas case in `docs/internal/philo/graph/atlas-phase13-astra.json` that validates against `docs/internal/philo/graph/atlas.schema.json` (`HOME=$(mktemp -d) uv run --extra dev pytest -q tests/unit/test_philo_graph_atlas.py`).
- [ ] Each case ran through `scripts/graph_walk.py run`, one case per invocation, at 1440 and at 393, each in a fresh HOME; `provenance.db_path` is under that HOME.
- [ ] Each case passes on main, or, where it finds a defect, it is red on main with the defect named and a home (story or BACKLOG) recorded. Red-before-green where the defect is in this phase's scope.
- [ ] The 393 runs drive touch, not the mouse adapter (`grounding/structure.md:37` names the mouse adapter as not touch proof); if the rig has no touch adapter for a step, that is a named limit, not a pass.
- [ ] Cases exist and pass on main **before** PHILO-13-07 merges. The gate is review evidence: this story's evidence file names each run directory, and B2's merge record cites this story's merged commit and `evidence-story-01.md`.

## Test plan

- **Atlas file:** `docs/internal/philo/graph/atlas-phase13-astra.json` (this lane's only atlas file; `--atlas` per run, `scripts/graph_walk.py:6507`); its count fence in `tests/unit/test_philo13_astra_atlas.py`.
- **Atlas:** `HOME="$(mktemp -d)" PLAYWRIGHT_BROWSERS_PATH="$REAL_HOME/Library/Caches/ms-playwright" uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case <case id> --brain astra --viewport <1440|393> --engine none --out .tmp/graph-walk/philo-13-01/<label>` — one case per invocation (`agent/skills/holdspeak-capability-verifier/SKILL.md` "Walk a case").
- **Focused:** `tests/unit/test_philo_graph_atlas.py` and `tests/unit/test_philo13_astra_atlas.py` only.
- **Shots:** `before.png` / `after.png` per run, read by eye; 1440 and 393 (touch).

## Worker-brief scars

- **Doubles that lie:** a case seeds through real producers; never inject rows or finished responses and call them producer evidence.
- **Read the run:** `blocked` with its reason is a result; never edit an observation by hand; each run its own `--out`.
- **Never a blanket restore:** restore nothing; report what a run changed.

## Effort (not a promise)

Grounding size: not sized there; nine cases at two widths. PROVISIONAL.

## Notes

- 2026-10-01 — r2: Astra charter check r1 (DO-NOT-RATIFY) paid; see the status file, "Round two".
- 2026-10-01 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
