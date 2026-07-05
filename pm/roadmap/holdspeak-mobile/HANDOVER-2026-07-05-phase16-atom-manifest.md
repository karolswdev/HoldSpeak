# Handover — 2026-07-05 — Phase 16 resumed: the atom + the manifest (3 PRs, 6/9)

One session, owner-steered three times ("deduce the next phase and plan" → "Lettuce
start building" → "Keep going?!"): **Phase 16 (The Desk, Everywhere) was deduced as
the delivery framework's next buildable phase, resumed survey-corrected, and built
from 0/9 recorded to 6/9** — PRs #254, #255, #256, all merged green. This is the
map: what shipped, the two truth-ups, what remains, the traps.

## Where main stands

- **Merged this session:** #254 (the resume survey: 16-01/02/03/05 recorded done
  pre-paid with evidence files; 16-04/08 re-scoped; 16-09 ratified as the lead),
  #255 (HSM-16-09, the Ask AI atom), #256 (HSM-16-08, the model manifest). Main is
  green at `e983fec`.
- **Suites at last runs:** `swift test` **467 / 9 skipped / 0 failures**;
  `uv run pytest tests/unit` **2474 passed**; doc drift guard 18/18;
  `contracts/validate.py` ALL CHECKS PASSED (now including two negatives: profile
  api_key + the new manifest-path smuggle); app simulator build green.
- Working tree clean; only the untracked `.holdspeak/` dir (app runtime data,
  never stage it).

## The two truth-ups (read these — the house discipline in action)

1. **The resume survey (#254) claimed "zero Ask-AI code exists (grep-verified)" —
   WRONG.** The atom's skeleton had already shipped under other names:
   `askBundle` → `DioRouteSheet` → the routing theater → `DioPrintedCard` in
   `DeskDioramaStage.swift`. A grep for "AskAI" misses all of it. The correction is
   recorded in story-09, evidence-story-09.md, the phase status, and the program
   README — as loudly as the claim. Lesson: survey by *reading the surface's code*,
   not by grepping the feature's roadmap name.
2. **SERIALIZATION-CONTRACT §11 still said `agents`** after the Phase-17 recipe
   rename; fixed in #256 while bringing the section to eleven kinds.

## Track 1 — HSM-16-09, the Ask AI atom (#255)

The story's real substance was what the existing skeleton faked:

| Slice | The one line |
|---|---|
| Full Ask lineage | `RunProvenance` grew `contextIds`/`contextTitles`/`prompt` (decode-tolerant custom init); a kept Ask persists as an `Artifact` naming every lasso'd card + the exact instruction; one canonical `sources` row per context; `viaKind: "ask"` on both the single-card route and the bundle |
| Golden-pin safety | The ask keys are emitted ONLY when present — recipe/chain provenance keeps the exact legacy structured shape (`testRecipeProvenanceKeepsLegacyWireShape`) |
| Two egress lies fixed | The printed card AND the routing theater read the app-wide `isLocal`, ignoring the per-run profile override — a cloud-profile ask printed a card claiming local. Both now resolve `resolveProfile(recipeProfileId:)`; a cloud run names its real `egressHost` |
| Off the scrim | The composer joined `DioAtelierPanel` (desk visible); `DioPrintedCard` lost the 0.7 scrim and PRINTS from the AI core (`birth` offset → spring); the lineage row learned the ask glyph |
| Proof | 3 new `HS_DESK_ASK` affordances (`selected`/`compose`/`printed`) drive the tap states headlessly; 3 committed screenshots |

## Track 2 — HSM-16-08, the model manifest (#256)

Survey-corrected scope: combine-to-run + cross-node runs were pre-paid (desk era +
P22); drop-model-sets-RUNS-ON superseded by P24 profiles; "resolved from the
manifest" ships as the manifest INFORMING the user's pick (silent egress
auto-routing would violate the approval+egress contract). The build:

- **The `model` MANIFEST is the sync wire's eleventh kind** —
  `{id "<node>:<file>", node, name, capabilities[]}`, availability only.
- iPad pushes installed language GGUFs (`DeskSyncDriver.localModels`); the hub
  stores every node's rows AND emits its own model as a live virtual row
  (`desktop:intel`, from `intel_provider` config, never stored); pulled
  `meshModels` cache to `hs.desk.meshModels`.
- **The felt payoff:** the "where should it run?" sheet's desktop row names the
  actual model ("Qwen3.5-9B-Instruct-Q6_K · 192.168.1.43"), not "big model".
- **The no-binary invariant is asserted on three layers**: schema
  (`additionalProperties:false` + a validate.py negative), Swift wire test (no
  `path`/`url` key encodes), hub route test (pulled value keys ⊆ the manifest set).

## Outstanding — the owner's hands

**THE COUCH SESSION** (unchanged queue + new beats): 17-06, the 18/19/21/22/23
walk riders, and now **16-06's device beats** — the Ask atom walked on the cabled
iPad (lasso → speak → print → keep, on-device air-gap honest) + the manifest
round-trip against a real hub + the org-sync live loop.

## Outstanding — buildable headless (ranked)

1. **HSM-16-04's remaining web slice** — web recipe/atelier authoring (the 17-08
   closeout filed it verbatim as "the next slice") + the Ask atom's web parity.
   The web desk lives in `web/src/desk/` (React island, the front door via
   `index.astro`); RecipeRail exists, authoring doesn't. Remember: edit `web/src`,
   `cd web && npm run build` to verify, never commit `holdspeak/static/_built/`.
2. **HSM-16-06 prep** — the walk rider doc (stage the three device beats above in
   one runbook, ~5 min, joining the couch queue).
3. **HSM-16-07 docs** — README/ARCHITECTURE catch-up for the atom + the manifest;
   feature docs must touch the ENTRY points (the Phase-64 lesson).

## Traps (this session's additions to the standing list)

- **The desk demo env var is `HS_DESK_RECIPES`** (not `HS_DESK_AGENT`) —
  `SIMCTL_CHILD_HS_DESK_RECIPES=runtarget` opens the run-target sheet;
  `runtarget` also seeds the mesh manifest so the hub row names its model. Don't
  combine with `HS_DESK_SUMMON=1` (its radial covers the sheet).
- **`patch-llm-macro.sh` takes args**: `<derived-data> <xcodeproj> <scheme>`; the
  scheme is **HoldSpeakMobile** (not HoldSpeakMeetingCapture). Then build with
  `-disableAutomaticPackageResolution -skipMacroValidation`.
- **The kind-add checklist that worked** (do ALL of it in one commit): Swift
  `SyncKind` + `ChangeSet` (init/CodingKeys/decode/isEmpty/count) → new
  `schemas/<kind>.schema.json` + changeset schema (props + kind enum + $defs
  bucket) → `validate.py` kind map → the golden fixture (row + changeset bucket
  incl. a tombstone) → hub `SYNC_KINDS`/`_BUCKET_KIND`/`_MERGEABLE` + table/repo →
  the drift guard's `KIND_BUCKETS` + its pull_body seeding → the db schema
  snapshot (regenerate with the test's own regex, `tests/unit/test_db.py`) → the
  `_fake_db` stub in `test_web_routes_sync.py` needs the new repo attr.
- **Demo affordance blocks in DioStage have no `w`/`h` in scope** — mirror
  `askBundle`'s tail manually (geometry is cosmetic there).
- **SourceKit diagnostics in App files are noise** (the gen script flattens
  Sources+App into one module); xcodebuild is the truth.
- The standing ones still bite: re-run `gen-meeting-capture.rb` after EVERY
  App/*.swift edit; gate merges on the conclusion JSON in three separate calls;
  screenshots need absolute paths.

## Where things live

- Phase 16: `pm/roadmap/holdspeak-mobile/phase-16-the-desk-everywhere/`
  (per-story evidence 01/02/03/05/08/09 + 4 screenshots).
- The contract growth: `apple/Sources/Contracts/{Primitives,Sync}.swift`,
  `holdspeak/db/{models,core,primitives}.py`, `holdspeak/web/routes/sync.py`,
  `pm/roadmap/holdspeak-mobile/contracts/` (schema + validator + fixture + both
  contract docs).
- Memory (Claude's): `project_phase16_resume_ask_ai` carries the running state +
  the kind-add checklist; `project_equilibrium_program` +
  `project_phase17_agent_sync` carry the couch queue.
