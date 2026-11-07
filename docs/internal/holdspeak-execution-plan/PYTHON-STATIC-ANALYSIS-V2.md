# Python static analysis v2 — roots, import contexts and candidate triage

**Publication note, 4 November 2026:** `${ANALYSIS_ARTIFACTS}` is a placeholder for the original external analysis directory. Its scripts and data are not bundled. The historical commands below are not runnable from this documentation checkout alone. Only path notation changed; the findings and execution claims remain historical.

**Status: source-only architectural evidence; owner review pending. No implementation or deletion decision.**

Snapshot: `80b641fa41c7352280cfa52e933acf6dbe8d3857`. This is a refinement of [v1](PYTHON-STATIC-ANALYSIS.md), not a replacement. All v1 analyzer/results remain unchanged.

## What became clearer

**28 of v1's 39 zero-recorded-explicit-inbound modules are explained by deliberately omitted graph semantics:** 21 named MCP registry members, six package initializers and one declared CLI entrypoint. The other 11 include a `python -m` entrypoint, public SDK, tests/guard tooling, compatibility and parked history. Only the small `db.models.mixins.Serializable` is a stronger orphan *candidate* from this bounded pass; no module is certified dead.

The graph also distinguishes actual import placement from runtime execution. Of 6,844 explicit local import-target records, **2,883 are top-level runtime-possible**, **3,925 are deferred runtime-possible**, and **36 are recognized type-guard-only**. “Top-level” includes class bodies and conditional/try imports, and is not a guarantee of execution. Deferred edges do not imply their containing function is called.

## Reproducibility and safety

```sh
python ${ANALYSIS_ARTIFACTS}/analyze_v2.py
python ${ANALYSIS_ARTIFACTS}/references_v2.py
```

These are our standard-library analysis programs, not repository scripts. Inputs are the retained pinned archive, manifest and 916 hub Python source files. All 916 parse; rechecked Git blob hashes have zero mismatches. No application module was imported; no application, setup, tests, build, dependency installation or repository mutation occurred.

Artifacts: `analyze_v2.py`, `report_v2.json`, `summary_v2.json`, `references_v2.py`, `references_v2.json` under `${ANALYSIS_ARTIFACTS}/`. The detailed JSON retains all edge contexts and all 39 candidate classifications' underlying graph facts. The Markdown ledger below adds source-reviewed interpretation.

Own synthetic analyzer checks passed for imported `TYPE_CHECKING` alias, `typing` alias, `else`, negation, Boolean AND/OR partial evaluation, deferred type-guarded imports, unrelated identifiers containing TYPE_CHECKING, and class-body imports. These test the analyzer, not HoldSpeak behavior.

## Graph layers — not runtime import-cycle findings

Declared roots are `holdspeak.cli_entry:main` and `holdspeak.mcp.server:main` from `[project.scripts]`. Conventional `holdspeak.mcp.__main__` is reported separately, not silently included as a console-script root. The MCP family's 28 literal registrations are source-resolved edges from the family loader, not 28 unconditional startup roots. Dynamic import failures remain possible.

| Layer | Unique directed module pairs | Largest SCC | Potential closure from two console roots |
|---|---:|---:|---:|
| Explicit, top-level, non-type-guard | 2,844 | 7 | 207/916 |
| Explicit, top-level + deferred, non-type-guard | 5,215 | 379 | 874/916 |
| Top-level + known registry + package init, non-type-guard | 4,388 | 50 | 291/916 |
| Top-level + deferred + known registry + package init, non-type-guard | 7,175 | 630 | 905/916 |
| Same enriched graph including type guards | 7,199 | 636 | 905/916 |

**An SCC is a structural dependency component, not a reproduced cycle failure.** Adding implicit initializer edges deliberately creates parent↔descendant dependencies; Python's import cache/order and partially initialized modules are not simulated. The large all-context SCC is a union of top-level, deferred and type-guarded dependencies. Even the top-level-only SCCs are not proof of import-time failure: declaration order, already-bound names and registration ordering matter. A 905-module potential closure is not evidence 905 modules execute at startup, nor that the remaining 11 are dead.

The largest explicit top-level SCC contains `operations` and six operation-descriptor siblings. For example, `channel_operations.py:20` imports descriptor types/constants from `operations`, while `operations.py:2267` aggregates channel descriptors after defining core contracts. This is an understandable registry/contract ownership loop, not evidence of a crash. A possible later seam is stable descriptor types below the aggregate; first establish whether that reduces actual change amplification.

## Measured ownership directions, then source checks

These counts are **distinct explicit non-type-guard module pairs**, including deferred imports; they exclude implicit-init and registry-added edges. Owners are literal second-level package names, with root modules kept individually. They are not quality scores or ideal dependency targets.

| Direction | Module pairs |
|---|---:|
| web → services | 200 |
| MCP → services | 123 |
| services → DB / DB → services | 116 / 11 |
| services → kernel / kernel → services | 107 / 10 |
| runtime → services / services → runtime | 41 / 39 |
| services → web | 1 |

The broad dominant direction is compatible with shared services below transports. Reverse edges deserve explanation, not blanket prohibition:

- **Small misplaced pure-helper dependency:** `ActivityMeetingCandidateService.create` (`services/activity_meeting_candidate_service.py:32`) imports `_parse_iso_datetime` from `web/runtime_support.py`. The service declares itself transport-neutral, while the helper module also imports FastAPI `JSONResponse`. A neutral timestamp parsing home is a plausible small boundary repair *after matching existing parser semantics*; no generic service rewrite is needed.
- **Constants owned by an orchestrator:** `db/pipeline_events_retention.py:55` imports `ROOM_WRITE_METHODS` from `services/project_service.py` to avoid pruning write receipts as read events. The safety rule is necessary; importing a large orchestrator just for method classification suggests the contract could have a lower, stable owner. Preserve that exclusion exactly.
- **Intentional compatibility lifecycle:** `db/core.py:243–245` invokes `DecisionRecordService(...).migrate_legacy_desk_decisions(None)` during DB construction, with explicit additive/idempotent compatibility intent. Do not remove or move this solely to make arrows pretty; any later composition change must preserve bare-DB consumers and canonical decision identity.

These are responsibility/change-amplification signals, not file-size judgments. Large cohesive schemas, registries and domain modules remain legitimate.

## All 39 original flags, classified

“Retained” means counterevidence defeats a dead-code inference; it does not freeze the current placement forever. All source links use the pinned snapshot.

| Module | Classification | Evidence / remaining proof |
|---|---|---|
| `holdspeak.cadence` | Package initializer, retained | [holdspeak/cadence/__init__.py:1](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/cadence/__init__.py#L1) — Imported descendants cause package initialization; v1 omitted that dependency. |
| `holdspeak.cli_entry` | Declared console entrypoint, retained | [pyproject.toml:1](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/pyproject.toml#L1) — [project.scripts] holdspeak = holdspeak.cli_entry:main; inbound importer unnecessary. |
| `holdspeak.commands` | Package initializer, retained | [holdspeak/commands/__init__.py:1](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/commands/__init__.py#L1) — Imported descendants cause package initialization; v1 omitted that dependency. |
| `holdspeak.connector_fixtures` | Test harness, retained | [tests/unit/test_connector_fixture_harness.py:22](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/tests/unit/test_connector_fixture_harness.py#L22) — Explicit test import; runtime-hub reachability is the wrong criterion. |
| `holdspeak.db.models.mixins` | Uncertain; strongest orphan candidate | [holdspeak/db/models/mixins.py:7](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/db/models/mixins.py#L7) — Serializable has no hub importer. Selected archive search finds uses in parked model copies, not active hub models; external users/reflection and compatibility intent remain unproven. |
| `holdspeak.mcp.__main__` | Conventional entrypoint, retained | [holdspeak/mcp/__main__.py:1](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/mcp/__main__.py#L1) — python -m holdspeak.mcp delegates to server.main; not expected to have an importer. |
| `holdspeak.mcp.families.agent` | Known registry member, retained | [holdspeak/mcp/families/__init__.py:29](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/mcp/families/__init__.py#L29) — Named in literal family list; guarded dynamic load at line 67. Registration intent, not proof load succeeds. |
| `holdspeak.mcp.families.ask` | Known registry member, retained | [holdspeak/mcp/families/__init__.py:29](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/mcp/families/__init__.py#L29) — Named in literal family list; guarded dynamic load at line 67. Registration intent, not proof load succeeds. |
| `holdspeak.mcp.families.cadence` | Known registry member, retained | [holdspeak/mcp/families/__init__.py:29](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/mcp/families/__init__.py#L29) — Named in literal family list; guarded dynamic load at line 67. Registration intent, not proof load succeeds. |
| `holdspeak.mcp.families.calls` | Known registry member, retained | [holdspeak/mcp/families/__init__.py:29](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/mcp/families/__init__.py#L29) — Named in literal family list; guarded dynamic load at line 67. Registration intent, not proof load succeeds. |
| `holdspeak.mcp.families.coder` | Known registry member, retained | [holdspeak/mcp/families/__init__.py:29](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/mcp/families/__init__.py#L29) — Named in literal family list; guarded dynamic load at line 67. Registration intent, not proof load succeeds. |
| `holdspeak.mcp.families.concierge` | Known registry member, retained | [holdspeak/mcp/families/__init__.py:29](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/mcp/families/__init__.py#L29) — Named in literal family list; guarded dynamic load at line 67. Registration intent, not proof load succeeds. |
| `holdspeak.mcp.families.desk_windows` | Known registry member, retained | [holdspeak/mcp/families/__init__.py:29](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/mcp/families/__init__.py#L29) — Named in literal family list; guarded dynamic load at line 67. Registration intent, not proof load succeeds. |
| `holdspeak.mcp.families.inference` | Known registry member, retained | [holdspeak/mcp/families/__init__.py:29](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/mcp/families/__init__.py#L29) — Named in literal family list; guarded dynamic load at line 67. Registration intent, not proof load succeeds. |
| `holdspeak.mcp.families.interview` | Known registry member, retained | [holdspeak/mcp/families/__init__.py:29](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/mcp/families/__init__.py#L29) — Named in literal family list; guarded dynamic load at line 67. Registration intent, not proof load succeeds. |
| `holdspeak.mcp.families.memory` | Known registry member, retained | [holdspeak/mcp/families/__init__.py:29](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/mcp/families/__init__.py#L29) — Named in literal family list; guarded dynamic load at line 67. Registration intent, not proof load succeeds. |
| `holdspeak.mcp.families.model_library` | Known registry member, retained | [holdspeak/mcp/families/__init__.py:29](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/mcp/families/__init__.py#L29) — Named in literal family list; guarded dynamic load at line 67. Registration intent, not proof load succeeds. |
| `holdspeak.mcp.families.note` | Known registry member, retained | [holdspeak/mcp/families/__init__.py:29](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/mcp/families/__init__.py#L29) — Named in literal family list; guarded dynamic load at line 67. Registration intent, not proof load succeeds. |
| `holdspeak.mcp.families.phone` | Known registry member, retained | [holdspeak/mcp/families/__init__.py:29](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/mcp/families/__init__.py#L29) — Named in literal family list; guarded dynamic load at line 67. Registration intent, not proof load succeeds. |
| `holdspeak.mcp.families.plugin_job` | Known registry member, retained | [holdspeak/mcp/families/__init__.py:29](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/mcp/families/__init__.py#L29) — Named in literal family list; guarded dynamic load at line 67. Registration intent, not proof load succeeds. |
| `holdspeak.mcp.families.practice_recipe` | Known registry member, retained | [holdspeak/mcp/families/__init__.py:29](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/mcp/families/__init__.py#L29) — Named in literal family list; guarded dynamic load at line 67. Registration intent, not proof load succeeds. |
| `holdspeak.mcp.families.program` | Known registry member, retained | [holdspeak/mcp/families/__init__.py:29](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/mcp/families/__init__.py#L29) — Named in literal family list; guarded dynamic load at line 67. Registration intent, not proof load succeeds. |
| `holdspeak.mcp.families.reactions` | Known registry member, retained | [holdspeak/mcp/families/__init__.py:29](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/mcp/families/__init__.py#L29) — Named in literal family list; guarded dynamic load at line 67. Registration intent, not proof load succeeds. |
| `holdspeak.mcp.families.sequence` | Known registry member, retained | [holdspeak/mcp/families/__init__.py:29](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/mcp/families/__init__.py#L29) — Named in literal family list; guarded dynamic load at line 67. Registration intent, not proof load succeeds. |
| `holdspeak.mcp.families.settings` | Known registry member, retained | [holdspeak/mcp/families/__init__.py:29](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/mcp/families/__init__.py#L29) — Named in literal family list; guarded dynamic load at line 67. Registration intent, not proof load succeeds. |
| `holdspeak.mcp.families.setup` | Known registry member, retained | [holdspeak/mcp/families/__init__.py:29](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/mcp/families/__init__.py#L29) — Named in literal family list; guarded dynamic load at line 67. Registration intent, not proof load succeeds. |
| `holdspeak.mcp.families.thread` | Known registry member, retained | [holdspeak/mcp/families/__init__.py:29](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/mcp/families/__init__.py#L29) — Named in literal family list; guarded dynamic load at line 67. Registration intent, not proof load succeeds. |
| `holdspeak.meeting_session.deferred_admission` | Compatibility surface, retained | [tests/unit/test_meeting_service.py:35](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/tests/unit/test_meeting_service.py#L35) — Retired implementation namespace reexports current bound objects; active test imports queue_service_principal; another test imports BoundDeferredIntelJob at test_meeting_deferred_admission.py:1600. |
| `holdspeak.memory` | Package initializer, retained | [holdspeak/memory/__init__.py:1](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/memory/__init__.py#L1) — Imported descendants cause package initialization; v1 omitted that dependency. |
| `holdspeak.plugins` | Package initializer, retained | [holdspeak/plugins/__init__.py:1](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/plugins/__init__.py#L1) — Imported descendants cause package initialization; v1 omitted that dependency. |
| `holdspeak.plugins.builtin.followup_ticket_actuator` | Opt-in reference/test plugin, retained | [tests/unit/test_actuator_reference.py:24](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/tests/unit/test_actuator_reference.py#L24) — Direct test import. Source:150 explicitly registers only behind an opt-in actuator gate; default nonactivation is intentional. |
| `holdspeak.plugins.dictation.builtin` | Package initializer, retained | [holdspeak/plugins/dictation/builtin/__init__.py:1](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/plugins/dictation/builtin/__init__.py#L1) — Imported descendants cause package initialization; v1 omitted that dependency. |
| `holdspeak.privileged_effects` | Package initializer, retained | [holdspeak/privileged_effects/__init__.py:1](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/privileged_effects/__init__.py#L1) — Imported descendants cause package initialization; v1 omitted that dependency. |
| `holdspeak.product_copy` | Guard/tooling, retained | [scripts/phase93_copy_census.py:16](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/scripts/phase93_copy_census.py#L16) — Census script and tests/unit/test_product_copy.py:8 import it; not unused because absent from hub startup. |
| `holdspeak.realtime_frames` | Cross-stack contract/guard, retained | [tests/unit/test_realtime_frame_registry.py:12](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/tests/unit/test_realtime_frame_registry.py#L12) — Active test imports canon; tests/unit/test_desk_live.py:27 and web/src/runtime/frames.ts mirror establish consumers outside hub graph. |
| `holdspeak.sdk` | Public SDK package, retained | [holdspeak/sdk/__init__.py:1](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/sdk/__init__.py#L1) — External-client namespace; initialized when SDK descendant imported. Hub should not need to import its own client. |
| `holdspeak.sdk.programs` | Public SDK/test surface, retained | [tests/unit/test_sdk_programs.py:14](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/tests/unit/test_sdk_programs.py#L14) — Programs/ProgramsRefused imported in tests and documented in agent skill; external consumer reachability intentionally not modeled. |
| `holdspeak.web.routes.primitives._parked` | Parked history; no live path found | [holdspeak/web/routes/primitives/_parked/__init__.py:1](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/web/routes/primitives/_parked/__init__.py#L1) — Explicit history namespace; not a removal recommendation. |
| `holdspeak.web.routes.primitives._parked.decisions` | Parked history; no live path found | [holdspeak/web/routes/primitives/_parked/decisions.py:1](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/web/routes/primitives/_parked/decisions.py#L1) — Header declares canonical decision-record router owns route and legacy adapter intentionally unregistered. Only definition of build_parked_desk_decisions_router found in selected archive text scope. |

## Search scope and uncertainty

The supporting literal-reference pass inspected **12,298 UTF-8 source/document/config files** in the pinned archive, selected by suffix (`.py`, `.md`, `.toml`, `.json`, `.yaml`, `.yml`, `.sh`, `.ts`, `.tsx`, `.mjs`, `.txt`) and capped at 2 MB per file. Three selected files were skipped: `docs/internal/philo/graph/static-astra.json`, `pm/archive-manifest.txt`, and `pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/checks/story-04-built-muaddib.md`. Its exact terms/results are retained. Text matches are not binding resolution; historical prose and parked code are distinguished from active imports. Absence is not proof against reflection, aliases, generated code or external users.

Additional analyzer limits: `from package import name` may overapproximate a submodule; guard aliases are recognized syntactically without complete scope/rebinding analysis; only the reviewed MCP registry is expanded; literal dynamic calls and other custom loaders remain recorded but generally unresolved. No function call graph, production coverage or installed-plugin census was obtained. Full monorepo Python, frontend compilation/reachability and native-runtime graphs are outside the 916-file AST scope.

## Next bounded question

Review contract ownership on a handful of reverse dependency edges (pure timestamps, retention classification, descriptor types), and distinguish these from intentional lifecycle composition. For the orphan candidate, inspect packaging/public-API expectations and the parked-model migration decision before proposing removal. Do not turn the 905-node closure or SCC counts into a wholesale reorganization, dead-code census or arbitrary file-length rule.
