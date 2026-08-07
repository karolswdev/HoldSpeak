# Evidence - HS-123-12

- **Story:** HS-123-12 - Thin routes audit
- **Status:** in-progress — audit did not meet the database census criterion
- **Date:** 2026-08-06

## Proof

### Captured run — 2026-08-07T02:28:16Z

- **Command:** `grep -rn get_database() holdspeak/web/routes/ --include=*.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5031425ff6622cef5c93be348b9a5ad86491d9a0

```text
holdspeak/web/routes/sync.py:35:        service = SyncService(hsdb.get_database(), hub_model_name=lambda: _hub_model_name(None))
holdspeak/web/routes/desk_seed.py:30:        return DeskService(get_database())
holdspeak/web/routes/missioncontrol.py:280:            entries = await asyncio.to_thread(list_journal, get_database(), limit=limit)
holdspeak/web/routes/missioncontrol.py:428:            db = get_database()
holdspeak/web/routes/missioncontrol.py:474:                get_database(),
holdspeak/web/routes/activity/enrichment.py:15:def _svc()->ActivityEnrichmentService:return ActivityEnrichmentService(get_database())
holdspeak/web/routes/activity/plugin_jobs.py:15:def _svc()->PluginJobService:return PluginJobService(get_database())
holdspeak/web/routes/activity/nudges.py:14:def _svc()->ActivityNudgeService:return ActivityNudgeService(get_database())
holdspeak/web/routes/activity/ledger.py:16:def _svc() -> ActivityLedgerService: return ActivityLedgerService(get_database())
holdspeak/web/routes/activity/rules.py:15:def _svc()->ActivityRulesService:return ActivityRulesService(get_database())
holdspeak/web/routes/activity/candidates.py:15:def _svc()->ActivityMeetingCandidateService:return ActivityMeetingCandidateService(get_database())
holdspeak/web/routes/core.py:29:        return JSONResponse(DeskService(get_database()).health())
holdspeak/web/routes/delivery_terminal.py:118:            db = hub_db if hub_db is not None else get_database()
holdspeak/web/routes/primitives/chains.py:32:        return PrimitiveService(get_database())
holdspeak/web/routes/primitives/chains.py:108:            db = get_database()
holdspeak/web/routes/primitives/workbenches.py:24:        return WorkbenchService(get_database())
holdspeak/web/routes/primitives/kbs.py:24:        return PrimitiveService(get_database())
holdspeak/web/routes/primitives/directories.py:24:        return PrimitiveService(get_database())
holdspeak/web/routes/primitives/decisions.py:25:        return PrimitiveService(get_database())
holdspeak/web/routes/primitives/_shared.py:359:        get_database().plugins.record_artifact(
holdspeak/web/routes/primitives/notes.py:24:        return PrimitiveService(get_database())
holdspeak/web/routes/primitives/recipes.py:25:        return RecipeService(get_database())
holdspeak/web/routes/primitives/workflows.py:33:        return PrimitiveService(get_database())
holdspeak/web/routes/primitives/workflows.py:132:            db = get_database()
holdspeak/web/routes/primitives/profiles.py:53:        return ProfileService(get_database())
holdspeak/web/routes/system/gate_routes.py:165:    flipped = get_database().gate.invalidate_all_held(reason="hub restarted while the proposal was held")
holdspeak/web/routes/system/coders.py:296:        return CoderService(get_database())
holdspeak/web/routes/system/coder_steering_support.py:136:    blocks, unknown = hydrate_refs(get_database(), meeting_ids, artifact_ids, expand)
holdspeak/web/routes/system/coder_steering_support.py:178:            database = get_database()
holdspeak/web/routes/system/coder_steering_routes.py:546:                get_database().steering.list, session_key=session_key, limit=limit
holdspeak/web/routes/system/coder_steering_routes.py:590:                get_database().notes.upsert,
holdspeak/web/routes/meeting_import.py:202:        db = get_database()
holdspeak/web/routes/setup.py:101:            event = get_database().onboarding.record_event(
holdspeak/web/routes/delivery_prs.py:64:                rows = get_database().work_attempts.list()
holdspeak/web/routes/delivery_prs.py:166:            service = default_launch_service(get_database())
holdspeak/web/routes/delivery_prs.py:196:        service = default_launch_service(get_database())
holdspeak/web/routes/delivery_prs.py:248:            db = get_database()
holdspeak/web/routes/delivery_prs.py:418:        db = get_database()
holdspeak/web/routes/dictation/pipeline.py:399:                delivery_repo = get_database().dictation_deliveries
holdspeak/web/routes/dictation/pipeline.py:792:            get_database(),
holdspeak/web/routes/cadence.py:28:        service = CadenceService(hsdb.get_database(), Config.load().cadence)
holdspeak/web/routes/meetings/intel.py:22:    service = MeetingIntelService(get_database(), notify=lambda topic, value: ctx.broadcast(topic, value) if ctx.broadcast else None)  # _svc composition
holdspeak/web/routes/meetings/live.py:40:    service = MeetingService(get_database())  # _service composition
holdspeak/web/routes/meetings/aftercare.py:21:    service = MeetingAftercareService(get_database(), notify=lambda topic, value: ctx.broadcast(topic, value) if ctx.broadcast else None)  # _svc composition
holdspeak/web/routes/meetings/crud.py:27:    service = MeetingService(get_database())  # _service composition
holdspeak/web/routes/delivery_attempts.py:86:                get_database().work_attempts,
holdspeak/web/routes/delivery_attempts.py:109:                attempts=get_database().work_attempts,
holdspeak/web/routes/delivery_factory.py:98:                repo=get_database().delivery_receipts,
holdspeak/web/routes/delivery_factory.py:116:                attempts=get_database().work_attempts,
```

## Audit summary — 2026-08-06

**Result: not ready to mark done.** The database-acquisition census does not
meet the story's no-handler-level-lines criterion. After applying the requested
filters (including service-constructor, shared-module, comment, `DeskService`,
and generic service-return exclusions), **24 lines remain**. They are not
limited to run endpoints or documented construction exceptions:

- `sync.py:35`, `cadence.py:28` — inline service construction using
  `hsdb.get_database()`.
- `missioncontrol.py:280,428,474`; `primitives/chains.py:108`;
  `primitives/workflows.py:132`; `meeting_import.py:202`; `delivery_terminal.py:118` —
  handler/helper database acquisition.
- `setup.py:101`, `system/gate_routes.py:165`,
  `system/coder_steering_support.py:136,178`,
  `system/coder_steering_routes.py:546,590`, and
  `dictation/pipeline.py:399,792` — direct persistence/repository use.
- `delivery_prs.py:64,248,418`, `delivery_attempts.py:86,109`, and
  `delivery_factory.py:98,116` — delivery route persistence/repository use.

The focused structural/MCP test selection passed: **2 passed, 2 skipped,
4654 deselected** (`uv run pytest -q tests/ -k 'thin_route or route_audit or
mcp'`). The MCP stdio catalog check passed with **41 tools**, exceeding the
required 36 and containing the named Phase 123 subset with required schema
properties. The direct import count also reports **41 tools**. The service
census reports **31 service modules** after the requested exclusions.

The structural tests and MCP catalog are green, but the uncategorized
route-level database accesses above block the database census acceptance
criterion. Story status remains `in-progress` pending route/service extraction
or explicitly legitimate, documented exceptions.

```

### Captured run — 2026-08-07T02:48:54Z

- **Command:** `grep -rn get_database() holdspeak/web/routes/ --include=*.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0a1e5adb0c5ae007757f1ef7cb199012784888f7

```text
holdspeak/web/routes/sync.py:35:        service = SyncService(hsdb.get_database(), hub_model_name=lambda: _hub_model_name(None))
holdspeak/web/routes/desk_seed.py:30:        return DeskService(get_database())
holdspeak/web/routes/activity/enrichment.py:15:def _svc()->ActivityEnrichmentService:return ActivityEnrichmentService(get_database())
holdspeak/web/routes/activity/plugin_jobs.py:15:def _svc()->PluginJobService:return PluginJobService(get_database())
holdspeak/web/routes/activity/nudges.py:14:def _svc()->ActivityNudgeService:return ActivityNudgeService(get_database())
holdspeak/web/routes/activity/ledger.py:16:def _svc() -> ActivityLedgerService: return ActivityLedgerService(get_database())
holdspeak/web/routes/activity/rules.py:15:def _svc()->ActivityRulesService:return ActivityRulesService(get_database())
holdspeak/web/routes/activity/candidates.py:15:def _svc()->ActivityMeetingCandidateService:return ActivityMeetingCandidateService(get_database())
holdspeak/web/routes/core.py:29:        return JSONResponse(DeskService(get_database()).health())
holdspeak/web/routes/primitives/chains.py:32:        return PrimitiveService(get_database())
holdspeak/web/routes/primitives/chains.py:108:            db = get_database()
holdspeak/web/routes/primitives/workbenches.py:24:        return WorkbenchService(get_database())
holdspeak/web/routes/primitives/kbs.py:24:        return PrimitiveService(get_database())
holdspeak/web/routes/primitives/directories.py:24:        return PrimitiveService(get_database())
holdspeak/web/routes/primitives/decisions.py:25:        return PrimitiveService(get_database())
holdspeak/web/routes/primitives/_shared.py:359:        get_database().plugins.record_artifact(
holdspeak/web/routes/primitives/notes.py:24:        return PrimitiveService(get_database())
holdspeak/web/routes/primitives/recipes.py:25:        return RecipeService(get_database())
holdspeak/web/routes/primitives/workflows.py:33:        return PrimitiveService(get_database())
holdspeak/web/routes/primitives/workflows.py:132:            db = get_database()
holdspeak/web/routes/primitives/profiles.py:53:        return ProfileService(get_database())
holdspeak/web/routes/system/coders.py:296:        return CoderService(get_database())
holdspeak/web/routes/cadence.py:28:        service = CadenceService(hsdb.get_database(), Config.load().cadence)
holdspeak/web/routes/meetings/intel.py:22:    service = MeetingIntelService(get_database(), notify=lambda topic, value: ctx.broadcast(topic, value) if ctx.broadcast else None)  # _svc composition
holdspeak/web/routes/meetings/live.py:40:    service = MeetingService(get_database())  # _service composition
holdspeak/web/routes/meetings/aftercare.py:21:    service = MeetingAftercareService(get_database(), notify=lambda topic, value: ctx.broadcast(topic, value) if ctx.broadcast else None)  # _svc composition
holdspeak/web/routes/meetings/crud.py:27:    service = MeetingService(get_database())  # _service composition
```
