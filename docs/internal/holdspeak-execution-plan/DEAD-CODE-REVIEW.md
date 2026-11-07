# HoldSpeak dead code evidence review

**Publication note, 4 November 2026:** `${ANALYSIS_ARTIFACTS}` is a placeholder for the original external analysis directory. Its scripts and data are not bundled. The historical commands below are not runnable from this documentation checkout alone. Only path notation changed; the findings and execution claims remain historical.

**Three original candidates plus a targeted Python follow-up; none is established as safely dead. No removal is authorized.** This is a bounded source-review ledger at `80b641fa41c7352280cfa52e933acf6dbe8d3857`, not an exhaustive reachability census. The initial candidate/entrypoint review did not execute an analyzer, build or product test. A later original hub-Python analyzer did run, as distinguished below; no product scripts or tests ran. Searches identify possible references; they cannot prove absence across dynamic entrypoints, plugins or supported external imports.

## 1 ProjectMemoryCore compatibility wrapper

**Path:** `web/src/pages/cores/ProjectMemoryCore.tsx`.

**Verified evidence:** The [wrapper](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/web/src/pages/cores/ProjectMemoryCore.tsx) re-exports ProjectRoomCore/model symbols. The nonparked [projectMemoryCore test](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/web/src/pages/cores/__tests__/projectMemoryCore.test.tsx#L27-L31) imports its values, and [the cores barrel](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/web/src/pages/cores/index.ts#L15) re-exports its `ProjectTimelineEntry` type. The current [Memory application loader](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/web/src/desk/applications.ts#L426-L441) instead loads `MemoryCore` directly.

Three nonparked test files are confirmed value consumers: [projectMemoryCore.test.tsx](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/web/src/pages/cores/__tests__/projectMemoryCore.test.tsx#L27-L31), [memory.app.test.tsx](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/web/src/desk/__tests__/memory.app.test.tsx#L51-L55), and [delivery06.test.tsx](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/web/src/desk/components/delivery06.test.tsx#L14) (the last imports `LifecycleChip`). The barrel's `export type` is a type-compatibility edge, not a runtime value-import path. These source imports do not claim the tests ran.

**Classification:** Compatibility/test/type surface, not the current Memory application's runtime implementation. The wrapper header's statement about the lazy application loader is stale as evidence of that current route.

**Limits:** A complete value/type import graph and the supported-import compatibility policy have not been established. Nonparked tests are source references, not a claim that they were executed. Retiring the wrapper cannot be justified by the changed loader alone.

## 2 Parked Workbenches home implementation

**Path:** `web/src/pages/cores/_parked/WorkbenchesHomeCore.tsx`.

**Verified evidence:** The [current nonparked implementation](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/web/src/pages/cores/WorkbenchesHomeCore.tsx#L1-L11) identifies its former card grid/Recent runs ledger as parked. The [application registry](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/web/src/desk/applications.ts#L380-L381) loads the nonparked implementation. [TypeScript configuration](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/web/tsconfig.json) excludes parked paths from its initial source set; [Vitest configuration](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/web/vite.config.ts#L199-L205) excludes parked tests. The reviewer's exact parked-path search found the explanatory comment, not a runtime import.

**Classification:** Retained historical implementation; production reachability remains unproven. It is a stronger retirement candidate than the other two items, not approved dead code.

**Limits:** Exclusion and an empty indexed search do not establish absence from the import/build graph. Imported excluded modules can still be reached. Complete imports/globs, both browser entrypoints, build inclusion and the repository's archive-retention policy need to be understood before any retirement decision.

## 3 MemoryIndexRepository dynamic registration

**Path/symbol:** `holdspeak/db/memory_index.py::MemoryIndexRepository`.

**Verified evidence:** The [class](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/db/memory_index.py#L26-L28) declares `table = "memory_index"`. [db/core.py](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/db/core.py#L20-L41) imports repository modules for registration; [BaseRepository.__init_subclass__](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/db/base.py#L24-L29) registers them; [Database.__init__](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/db/core.py#L232-L239) instantiates registry entries dynamically. [sweep](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/memory/retain.py#L517-L530) accesses the resulting `db.memory_index` repository.

**Classification:** Active through dynamic registration in the inspected source; retain. It is a useful counterexample to constructor-name grep, not a removal candidate.

**Limits:** The source demonstrates the dispatch/registration mechanism; no runtime or test execution is claimed here. Its class name need not appear at a direct constructor call to be required.

## Corrections to the inventory

The earlier **785** frontend count means **non-test/non-parked paths**, not proven runtime-active files. Path filtering can both include unreachable code and exclude code reached through a wrapper.

[The existing import-graph helper](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/scripts/vitest_related.py#L122-L137) deliberately includes parked production modules, because a nonparked file can re-export one: [SystemShade](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/web/src/desk/components/SystemShade.tsx) is such a wrapper. This does **not** establish that SystemShade itself is reachable from a production entrypoint. Parked tests are separately excluded from Vitest.

The helper is a useful source of graph semantics, not a dead-code oracle. Its test-selection purpose, type-edge handling, traversal limits and unresolved dynamic/external consumers prevent interpreting selected-test output as runtime reachability proof.

## Entry point reachability follow-up

### Desk root

The reviewer traced a positive source path from [index.html](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/web/index.html#L16) through `web/src/main.tsx`, `App.tsx`, `routes.tsx`, `desk/DeskApp.tsx` and [SurfaceWindows](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/web/src/desk/components/SurfaceWindows.tsx#L15-L19) to `SURFACE_APPLICATIONS`. SurfaceWindows [constructs lazy cores from application.surface.load](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/web/src/desk/components/SurfaceWindows.tsx#L61-L76); the registry loaders point to nonparked `WorkbenchesHomeCore` and current `MemoryCore`, not either candidate.

**Result:** No production value-import path to either candidate was found in these inspected Desk paths and indexed references. This is not a complete Desk dependency graph: other paths, dynamic imports/globs and external consumers remain unresolved. Search-result coverage is not a substitute for whole-checkout AST analysis.

### Briefing root

The separate [briefing.html](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/web/briefing.html#L14) entry loads `web/src/briefing/main.tsx` and [BriefingApp](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/web/src/briefing/BriefingApp.tsx#L21-L32). The reviewer manually inspected a conservative closure of **18 local TypeScript modules** through its Button/thin-surface and related control dependencies. Within that inspected closure, neither candidate, the application registry, a literal dynamic import nor a glob was found.

**Result:** The inspected Briefing closure gives stronger bounded negative evidence than the incomplete Desk walk. Eighteen is the reviewer's inspected local-module scope, not a generated repository graph or an application-wide runtime module count. It does not establish that either candidate is globally dead or safe to remove.

### Built chunks do not prove current source reachability

[The Vite build configuration](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/web/vite.config.ts#L179-L184) sets `emptyOutDir: false` so open Desk tabs can request chunks from earlier builds. An old candidate-related bundle filename or retained asset is therefore not evidence that the current source entrypoints still reach it. Conversely, source absence cannot be established from one observed asset list.

### Validation gap

A full checkout-wide TypeScript AST graph has **not** been produced. The earlier candidate/entrypoint pass was connector-only: the environment catalog showed no saved coding environment, and a visible connected desktop was not authorized for this task. That availability was not treated as execution authority.

A later [Python static pass](PYTHON-STATIC-ANALYSIS.md) safely materialized archive source in the cloud workspace and verified all 916 hub Python blobs before running an original standard-library AST analyzer. This changes the source-analysis evidence, not the frontend reachability conclusion or desktop permission. No HoldSpeak module import, product setup/build/test script or desktop command was used for that run.

The missing proof is a graph that preserves runtime versus type/test/historical edges from both Vite roots and records unresolved dynamic/registered/external consumers. Do not invent cycle, fan-in, active-module or reachability counts to fill that gap. No access request or implementation action is implied by documenting it.

## Separate measured Python finding

The [Python AST report](PYTHON-STATIC-ANALYSIS.md) confirms two unconditional, undecorated, AST-identical definitions of `_backfill_directory_name_normalized` in `holdspeak/db/primitives.py`: the later definition shadows the earlier binding. This is a confirmed redundant declaration, not a finding that the surviving helper is unused; tests reference that helper. No source removal is authorized.

Two other repeated-declaration candidates are legitimate property setters. The report's 39 zero-explicit-target-inbound modules are not a deletion list: 21 are dynamically loaded MCP families, and the graph omits implicit parent-package initialization and other runtime roots. Its import measurements are all-context syntactic edges, not runtime reachability proof. These measured findings must not be generalized into a safe-removal claim for the three candidates above.

The subsequent [v2 source-only refinement](PYTHON-STATIC-ANALYSIS-V2.md) classifies all 39 original flags and explains 28 through omitted registry/package/entrypoint semantics. The remaining classifications include supported non-startup surfaces and one stronger but uncertain mixin candidate. No module is certified dead; the three candidates in this ledger retain their existing qualified status. V1 and v2 are preserved as separate measured reports.

## Decision boundary

Keep these classifications as evidence. No module deletion, archive move, test removal or task expansion follows from this ledger. The remaining question is whether the incomplete Desk graph or unresolved dynamic/external paths reach either frontend candidate. The inspected paths did not; that is bounded evidence, not a removal verdict. Specific retirement and implementation choices remain pending under the current surgical-evolution direction in [Decisions](DECISIONS.md).

## Targeted follow-up: `Serializable` and retired model copies

**Status: stronger orphan candidate, not certified dead or approved for removal.** Snapshot remains `80b641fa41c7352280cfa52e933acf6dbe8d3857`. This pass reused the earlier reference and graph results rather than rerunning the whole census; it inspected the candidate, seven model files, packaging, and relevant registration/loading mechanisms as source.

### New evidence

- [`holdspeak/db/models/mixins.py:7–16`](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/db/models/mixins.py#L7-L16) defines only `Serializable.to_dict`, delegating to `dataclasses.asdict`. It has no registration hook, factory or entrypoint.
- [`parked/README.md:16–21`](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/parked/README.md#L16-L21) records six former split-model modules as stale copies moved out of the product package. The earlier reference scan found the actual `Serializable` subclass uses in those six parked files—not active models. This history explains the candidate better than an inbound count alone.
- A targeted AST comparison found **40 direct `Serializable` subclasses** across those six parked modules. All 40 names also exist in the canonical `holdspeak/db/models/__init__.py`; none of those canonical definitions inherits `Serializable`. Nineteen define their own `to_dict`. This establishes declaration/inheritance facts, **not serializer behavior equivalence**; restoring the old mixin or split copies would not be justified by these counts.
- The normal DB export and repository registration paths do not rescue this candidate: [`db/__init__.py:7`](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/db/__init__.py#L7) imports the canonical models, not every submodule; that models file does not import/export `Serializable`. [`BaseRepository.__init_subclass__:24–29`](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/db/base.py#L24-L29) registers its own subclasses declaring a table. `Serializable` is neither such a subclass nor a table declaration. It is not analogous to the dynamically active MemoryIndexRepository.

### Counterevidence and unresolved consumers

The file remains inside the package selected by [`pyproject.toml:230–231`](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/pyproject.toml#L230-L231). That makes `holdspeak.db.models.mixins.Serializable` an existing import path in the intended package, even though no in-repository active consumer was found. No wheel was built or installed to verify a distribution artifact, and a packaged path is not automatically a promised public API.

Known console entrypoints and the reviewed first-party MCP/recipe/DB registrations do not name it. **External extension compatibility remains genuinely unresolved:** [`plugin_pack_loader.py:265–279`](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/plugin_pack_loader.py#L265-L279) and [`connector_pack_loader.py:258–273`](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/connector_pack_loader.py#L258-L273) load user-supplied Python modules. Such modules could import shipped paths. Their existence is not evidence that any actually imports this mixin, but the repository-only analysis cannot rule it out. No installed user pack, external package or serialized external object was inspected or loaded.

Evidence that would defeat a removal proposal includes a supported external import/API promise, an installed extension importing/subclassing this class, a live generated registration naming it, or persisted external objects requiring its qualified path. None was verified in this pass. Conversely, the six parked subclass files establish historical use, not current product execution.

**Next question:** what import/extension compatibility surface is actually supported? If this internal model helper is outside that surface and no owned extension consumes it, the case for retirement is materially stronger. If supported consumers exist, a compatibility path or migration decision is needed. Do not retain it forever merely because reflection is imaginable, but do not declare absence of external consumers from repository grep.

Reproducible targeted artifacts: `${ANALYSIS_ARTIFACTS}/serializable_review.py` and `serializable_review.json`; run the former with Python to repeat the seven-file declaration comparison. Existing `references_v2.json` and `report_v2.json` supply the previously qualified full-scope reference/graph evidence. No application imports, repository tests/build scripts, dependency installation, file moves or deletion occurred.

### Compatibility-contract follow-up

**Bounded conclusion:** the inspected repository contracts are narrower than “every packaged Python path.” No inspected contract promises `holdspeak.db.models.mixins.Serializable` as an external extension API. This strengthens the orphan classification; it does **not** certify safe removal. All evidence below is from snapshot `80b641fa41c7352280cfa52e933acf6dbe8d3857`; referenced tests were read as source, not run.

- **An explicit DB promise exists, but at the barrel:** [`holdspeak/db/__init__.py:1–7`](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/db/__init__.py#L1-L7) says existing `from holdspeak.db import X` imports keep working. Its canonical models do not import/export `Serializable`. This promise cannot simply be generalized to every submodule beneath that package.
- **Historical counterevidence must remain visible:** [`story-10-the-schema-extraction.md:47–89`](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/pm/roadmap/holdspeak/phase-117-the-foundation/story-10-the-schema-extraction.md#L47-L89) explicitly proposed the mixin and preserved `holdspeak.db.models` imports; [lines 101–116](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/pm/roadmap/holdspeak/phase-117-the-foundation/story-10-the-schema-extraction.md#L101-L116) require unchanged serializer output and model-name imports. [`evidence-phase-117.md:66–71`](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/pm/roadmap/holdspeak/phase-117-the-foundation/evidence-phase-117.md#L66-L71) claims mixin adoption and compatible barrels. These are historical refactor intent/evidence, not a specific promise to external callers of the direct mixin path. Their implementation description does not match the current canonical models and later parked-copy record above.
- **Extension contracts name specific seams:** [`PLUGIN_AUTHORING.md:79–100`](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/docs/PLUGIN_AUTHORING.md#L79-L100) specifies dictionary input/output; [lines 209–257](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/docs/PLUGIN_AUTHORING.md#L209-L257) specify SDK validation, `MANIFEST`, `create_plugin()` and local loading. [`connector_sdk.py:8–20`](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/connector_sdk.py#L8-L20) identifies manifests and SDK protocols as its contract. Neither names the model mixin. The pack `version` format checks ([plugin SDK](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/plugin_sdk.py#L77-L79), [connector SDK](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/connector_sdk.py#L92-L94)) are not a repository-wide semantic-version compatibility guarantee.
- **Focused tests corroborate those seams, not arbitrary import compatibility:** [`test_plugin_pack_loader.py:263–303`](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/tests/unit/test_plugin_pack_loader.py#L263-L303) checks fixture discovery and dictionary-based host dispatch; [`test_connector_sdk.py:192–231`](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/tests/unit/test_connector_sdk.py#L192-L231) checks duck-typed SDK protocols. No mixin import was found in the scanned active tests or extension guides.

**Remaining boundary:** package inclusion establishes an intended importable path, not an affirmative public-API promise. The inspected documentation does not establish a comprehensive supported-import policy, and no installed or user-owned extension was inspected. A concrete supported consumer or owner compatibility decision remains more probative than hypothetical reflection. This pass only read archive/source text and appended this evidence; it imported no application module and ran no product test, build, setup or installation.
