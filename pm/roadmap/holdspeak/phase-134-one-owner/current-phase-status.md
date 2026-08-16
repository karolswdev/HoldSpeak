# Phase 134 — One Owner

**Status:** in-progress (9/10).

**Last updated:** 2026-08-16.

## Owner mandate

Issue #450 Wave 1 ("make ownership obvious") — the owner-named next
product slice, greenlit 2026-08-16 to ship in parallel with the Comfy
Chair design studies ("studies now, Wave 1 ships meanwhile"). Scope is
the Wave 1 checklist: one target spec replacing the Profile +
InferenceTarget dual API; global/Agent/Workbench/invocation inheritance
with effective-target provenance; Settings as the only persistent
preference writer; Agent skill binding out of Workbench mutation;
Workbench sync repair; `mir_profile`/`plugin_profile` retirement.

## Goal

Every placement decision has one visible owner and one precedence
chain, and every API answer says who decided. The dual profile/target
vocabulary dies; execution obeys the same precedence the listings
display (today Recipe execution does not — the keystone defect);
domain surfaces stop writing each other's fields; and sync understands
"null means inherit". Zero regressions on the 82-tool MCP surface and
its walk harness.

## The evidence base

Read-only Wave 1 scoping audit on `b4c6aced` (2026-08-16), archived at
[assets/wave1-scoping-audit.md](./assets/wave1-scoping-audit.md): the
dual-API route/service/MCP map, the 14-run-kind inheritance table, the
writer-violation table, the `mir_profile` consumer census, the sync
merge-map anchors, a 5-item risk register, and the 8-story slicing this
charter adopts (plus docs and walk stories per house rule). Keystone
verified by the orchestrator on glass: `recipe_service.py` execution
resolves targets via `resolve_inference_target` (`_target()`, :168-171
region) while its listing path uses `resolve_placement` (:170) — the
only execution path bypassing the Phase-130 precedence authority
(`resolve_inference_targets.py:538-575`).

## Settled design (implement, don't relitigate)

- **Precedence:** invocation > workbench > agent > global — the
  Phase-130 `resolve_placement` chain is the ONLY execution resolver.
- **Null means inherit:** a nullable placement field on a domain object
  means "inherit from the next tier"; pinning local is an explicit
  `this_machine`. Sync transmits the field explicitly and must
  distinguish "null (inheriting)" from "absent from payload".
- **Vocabulary:** the outward name is **destination** (matches the
  product copy and MCP docs); `profile` survives only as internal
  storage until a later wave.
- **Ownership rulings from #450 verbatim:** Agent Edit owns agent
  placement and agent skills; Get Info summarizes and hands off;
  Workbench displays inherited skills read-only.
- **Ledger-not-gate rule applies:** provenance in responses is the
  point of this phase — every effective-target answer carries
  `{effective_target_id, source}` from `PlacementResolution.placement_dict()`.

## Scope

### In

The ten stories below — the audit's eight-story slicing plus the house
docs and walk stories. Anchors live in the audit; stories cite them.

### Out

- Wave 2 (product language: Daily Brief merge, Decision/Receipt
  convergence) and Wave 3 (structural guards) — later waves.
- `capability_ref` rename (Wave 2 vocabulary) — sync repair here works
  against today's field names with the null-inherit fix.
- Any Comfy Chair / design-language work — separate track, running in
  parallel as studies.
- New MCP tools beyond the `profile.*` → `destination.*` rename.

## Constitutional grounding

- **Article II (honest product):** a control that displays one
  provenance while execution obeys another is the class of lie this
  phase retires (the Recipe keystone).
- **Article XI.3 (immutable admission identity):** effective-target
  provenance rides the same admission snapshot Phase 130/131 built.
- **Article V (receipts):** `{effective_target_id, source}` in every
  placement-bearing response is the ledger made visible.

## Stories

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-134-01 | Recipe execution takes the precedence door | done | [story-01](./story-01-recipe-precedence.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-134-02 | One target spec, one API | done | [story-02](./story-02-one-target-spec.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-134-03 | MCP speaks destination | done | [story-03](./story-03-mcp-destination.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-134-04 | Every answer names its decider | done | [story-04](./story-04-provenance-everywhere.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-134-05 | Get Info hands off | done | [story-05](./story-05-get-info-handoff.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-134-06 | Skills belong to the Agent | done | [story-06](./story-06-agent-owns-skills.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-134-07 | Sync understands inherit | done | [story-07](./story-07-sync-null-inherit.md) | [evidence-story-07](./evidence-story-07.md) |
| HS-134-08 | The routing profile stands alone | done | [story-08](./story-08-routing-profile-cleanup.md) | [evidence-story-08](./evidence-story-08.md) |
| HS-134-09 | The docs speak destination | done | [story-09](./story-09-destination-docs.md) | [evidence-story-09](./evidence-story-09.md) |
| HS-134-10 | The walk | backlog | [story-10](./story-10-the-walk.md) | [evidence-story-10](./evidence-story-10.md) |

The ask each story answers, in one line: 01 — a Workbench override
actually changes where an Agent runs; 02 — one API speaks about
destinations, the dual routes die; 03 — MCP clients say destination.*
and the 82-tool walk stays green; 04 — every placement-bearing answer
carries who decided; 05 — Get Info summarizes placement and hands off
to the Agent editor; 06 — a Workbench shows inherited skills, only the
Agent edits them; 07 — a synced null placement means inherit, never
this_machine, and delegation revocation still fires; 08 — one routing
profile field, the legacy pair deleted; 09 — the entry-point docs use
the destination vocabulary; 10 — provenance proven live on `.43`, the
MCP walk re-run green, full suite zero regressions.

## Suggested order

01 (keystone) → 04 → 07 form the critical path. 02 → 03 is the second
chain. 05, 06, 08 are independent leaves (08 ships last of the leaves,
as cleanup). 09 after the renames land. 10 last, cannot be waived.
Parallel waves: {01, 02, 05, 06} then {03, 04, 08} then {07, 09} then 10.

## Risk register (from the audit, guards named)

1. Recipe placement migration silently a no-op if only the listing
   changes (guards: test_recipe_runner_migration, test_one_path_spine,
   test_placement_resolver).
2. `profile.*` → `destination.*` breaks the MCP walk harness and
   REQUIRED_TOOLS (guards: test_mcp_tools, test_mcp_phase133*,
   scripts/mcp_walk.py — story 03 updates all three in one commit).
3. Sync merge map and bounded-delegation revocation are keyed to
   `profile_id` changes (guards: test_primitive_contract sync-registry
   test; story 07 adds the round-trip test).
4. Dual-editor writes to recipe.profile_id (no guard today — story 05
   adds one on the settingsWriters pattern).
5. Workbench skill mutation has no guard (story 06 adds one).

## Ledger

- **Wave-one gate (2026-08-16): 1 real failure, fixed.** The committed
  API-surface manifest still carried the retired `/api/profiles` GET
  routes; regenerated (HS-134-02 rider). Also caught earlier by the
  HS-134-02 worker's wider sweep: the one-dial seam guard asserted the
  pre-keystone resolver (re-pointed in `eaeca3c8`). Process note: the
  keystone's focused set missed both guards — the wave gate exists for
  exactly this class and did its job.
- **P0 product bug surfaced (NOT this phase's doing): the owner's real
  DB (schema 59) fails the 59→60 migration** with
  `sqlite3.OperationalError: no such column: node_id` during
  `run_migrations` executescript. The current main build would hit
  this on the owner's next real hub start. Likely the Phase-132 v60
  schema meeting an older mesh-table shape. DB verified UNHARMED
  (logical dump identical to the pre-attempt backup
  `holdspeak.db.20260816-162131.bak`; mtime untouched; integrity ok).
  Needs a migration fix before the owner runs the hub on current main
  — flagged for the sitting and the next slice.
- **Process gotcha (orchestrator error, remediated):**
  `scripts/gen_api_surface.py` boots the real `MeetingWebServer`,
  which opens the REAL database via `Path.home()` — it must always run
  under an isolated HOME. It was run bare once; the schema-guard
  backup fired and no data was written.

## Exit criteria (evidence required)

- [ ] Recipe run and chat resolve through `resolve_placement`; a
  workbench-tier override changes actual execution (test proves it).
- [ ] The `/api/profiles` read routes are gone or redirect; one
  `_target_fields` remains; the `profile_alias` compatibility block is
  deleted.
- [ ] MCP tools are `destination.*`; REQUIRED_TOOLS, the phase-133
  tests, and `scripts/mcp_walk.py` all updated in the same commit;
  the walk runs 26/26 including the live leg.
- [ ] Every placement-resolving API and MCP response carries
  `{effective_target_id, source}`.
- [ ] `infoContract.ts` no longer writes `profile_id`; a writer-guard
  test enforces it.
- [ ] WorkbenchWindow renders skills read-only with an Agent hand-off;
  the mutation paths are deleted; a guard test enforces it.
- [ ] A sync round-trip with `profile_id: null` inherits on the
  receiving device; bounded-delegation revocation still fires on
  placement changes.
- [ ] `mir_profile` and `plugin_profile` are gone from config, schema,
  validation, and runtime vars; `effective_routing_profile` reads one
  field.
- [ ] README + docs/MCP_SIDECAR.md speak destination at the entry
  points.
- [ ] The walk: live `.43` provenance proof (a workbench override
  visibly redirects an agent run and the response names
  `source: workbench`), `scripts/mcp_walk.py --live-43` green, full
  suite zero regressions vs baseline.

## Where we are

HS-134-01 shipped: recipe run + chat now resolve through
`resolve_placement`; the keystone execution/listing split is closed.
42 focused tests green (8 new precedence + 34 existing guards).
HS-134-05 shipped: Get Info no longer writes profile_id; placement shows
as a read-only summary with "Edit in Agent" hand-off to RecipeEditor;
writer-guard test enforces single-writer rule. 13 focused tests green.
HS-134-06 shipped: WorkbenchWindow skill mutations deleted (updateSkill,
attachSkill, detachSkill, approveSkill, dismissSkill); skills render
read-only as INHERITED with "Edit in Agent" hand-off; source-level guard
test enforces zero mutation paths. 32 focused tests green (7 new guard).
HS-134-02 shipped: /api/profiles GET routes deleted; duplicated
_target_fields deleted (one definition in profile_service.py); PROFILE_ALIAS_VERSION
and profile_alias blocks retired; endpoint/node surfaced on the target contract;
web client migrated to /api/inference-targets; 90 focused tests green across
7 test files (unit + integration + UAT).
HS-134-03 shipped: profile.list/get/create/update/delete renamed to
destination.* (same schemas, same dispatch); holdspeak://profiles resource
renamed to holdspeak://destinations (static + template); phase-133 surface
test and walk harness updated in the same commit. 98 focused tests green;
walk harness 24/24 (82 tools, 14 static resources, 10 templates). One
residual grep hit in sync_service.py (profile.schema.json) is internal
storage, explicitly out of scope.
HS-134-04 shipped: every placement-resolving execution response carries
`{"placement": {"effective_target_id": ..., "source": ...}}` from the REAL
PlacementResolution used for that run. Covered surfaces: Ask, Recipe run,
Recipe chat, Workbench run, Sequence, Workflow, Cadence get_loop
(LLM-drafted path only; deterministic omits placement since no model ran).
MCP tools (ask.run, sequence.run, workflow.run, cadence.get_loop) pass
service dicts through unchanged -- the block arrives in tool results.
113 focused tests green (14 new provenance + 99 existing guards).
HS-134-08 shipped: `mir_profile` and `plugin_profile` deleted from
MeetingConfig (fields, validation, __post_init__); `effective_routing_profile`
reads only `routing_profile`; `migrate_routing_profile` deleted (`_coerce`
handles the tolerant-load guard for legacy config files); runtime instance
var `self.mir_profile` renamed to `self.routing_profile` in web_runtime,
activity, routing_glue; intel_queue call sites verified (already used
`effective_routing_profile` exclusively); settings_service retains a
tolerant `mir_profile` read-fallback for stale API clients (deliberate
leniency, not dual vocabulary); UAT decks updated. 356 unit + 96
integration focused tests green.
HS-134-09 shipped: docs/MCP_SIDECAR.md speaks destination throughout:
destination (5 tools) family section added, desk count corrected (52 to 47),
resource URIs updated (holdspeak://destinations, holdspeak://destinations/{id}),
stale "profile" vocabulary swept to "destination" in descriptions, placement
provenance note added (effective_target_id + source with four tiers).
README MCP sidecar section updated (ten families, destination added to list).
Two deliberate carve-outs: `intel_profile_id` kept (still a real config field),
`HOLDSPEAK_PROFILE_<ID>_KEY` kept (still the live env var name in code).
19 doc drift guard tests green; all relative links resolve.
HS-134-07 shipped: `_merge_primitive_spec` in sync_service.py fixed a real
bug where fields absent from the push payload clobbered existing receiving
values with NULL (the downstream upsert treated missing kwargs identically
to explicit None via `kwargs.get()` defaults). Now: present-with-null =
explicit inherit (writes NULL), absent-from-payload = no opinion (preserves
existing value via `existing.to_dict()` carry-forward). Bounded-delegation
revocation proven to fire on both null-to-value and value-to-null
`profile_id` transitions; proven NOT to fire on absent-field pushes (which
preserve the existing value). No path materializes `this_machine` or any
other default into the stored placement field during sync. 69 focused tests
green (11 new + 58 existing guards across 7 test files).
