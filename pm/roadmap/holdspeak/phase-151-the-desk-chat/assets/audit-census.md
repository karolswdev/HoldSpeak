# DC-01 "The Thread" — seam census (2026-08-29)

Audited against main `c9b0cd25` + the plan commit. Every anchor is
file:line at audit time; builders re-verify before editing.

## 1. Schema
- `holdspeak/db/schema.py` — `SCHEMA_SQL` L15–3403; last table
  `calendar_events` ends L3401; new block goes before the closing
  `"""`. `SCHEMA_VERSION = 64` (L12) is informational.
- Pattern: `scheduled_recordings` L3355–3396 (CHECKs + indexes);
  `tool_turns` cluster L3137–3249 (relational depth); FTS with sync
  triggers `notes_memory_fts` L1190–1198; `segments_fts` L186.
- `holdspeak/db/reconcile.py` — `reconcile_schema` L359; invariants
  L391–396 (additive only, idempotent, ALTER-safe, no version gate);
  `_add_missing_columns` L601; `_apply_data_backfills` L640; FTS
  shadows excluded `_is_fts_shadow` L27.
- Snapshot: `tests/unit/test_db.py:1731`
  `test_fresh_schema_matches_canonical_snapshot` vs
  `tests/fixtures/db_schema_canonical.txt` — regenerate same commit.
- Repository pattern: `holdspeak/db/calendar_events.py:57`
  (`BaseRepository` at `holdspeak/db/base.py:8`); full CRUD example
  `holdspeak/db/scheduled_recordings.py:64`.

## 2. Runner + providers
- `holdspeak/kernel/inference_runner.py:73` `InferenceRunner`
  (SYNC); `invoke` L147; `_dispatch → adapter.dispatch(engine,
  payload, cancellation: threading.Event)`; receipt `_persist_receipt`
  L109–126 via `broker.receipt(...)`; cancel L82/L104 →
  `inference_cancel_signal.perform_cancel`; `indeterminate` at L290,
  L325, L353, L435, L442. **No stream variant exists.**
- `holdspeak/intel/providers.py` — resolution + egress only
  (`resolve_intel_provider` L140, `effective_intel_cloud` L610,
  `egress_boundary` L405). Zero stream code.
- `holdspeak/intel/engine.py:337` `MeetingIntel._chat_completion_stream`
  — EXISTS (OpenAI SDK, local GGUF + cloud), yields `str` deltas; only
  `analyze(stream=True)` uses it. The seam to extend.
- Ask chain: `holdspeak/web/routes/primitives/ask.py:45` →
  `holdspeak/services/ask_service.py:177` (`ask`, async) → routed path
  L232–269 `inference_adoption_service.admit(...)` / `.execute(...)`
  via `asyncio.to_thread`; receipt in
  `result["route_execution_receipt"]` L297; cancel L442/L456;
  principal `ask.py:30` `Principal(PrincipalKind.OWNER,
  "owner-session")`.
- Web server FastAPI `holdspeak/web_server.py:481`; no
  StreamingResponse/SSE anywhere.

## 3. Capability registry
- `holdspeak/inference_capabilities.py` `builtin_capability_definitions`
  L1039–1082 (`ask.answer` L1051, `recipe.chat` L1069);
  `InferenceCapabilityRegistry.compose` L567 (sealed, sha256).
- Ledgers under `pm/roadmap/holdspeak/phase-143-intelligence-router/assets/`:
  `generated-inference-capability-census.md` ↔
  `tests/unit/test_phase143_inference_capability_census.py:525`
  (`EXPECTED_CALL_SITES` L57, `SEMANTIC_HELPER_CALLERS` L275);
  `generated-routing-authority-census.md` ↔
  `test_phase143_routing_authority_census.py:16`;
  `generated-surface-fallback-census.md` ↔
  `test_phase143_surface_fallback_census.py:20`.
- Assignments: `holdspeak/services/inference_assignment_service.py:382`
  `set_assignment`; not seeded from YAML → additive backfill family.

## 4. Realtime frames
- `holdspeak/realtime_frames.py:40–81` `RUNTIME_FRAME_TYPES` (35,
  sorted, underscore dialect) + `web/src/runtime/frames.ts` hand-
  mirrored; drift test `tests/unit/test_realtime_frame_registry.py:42`.
- `holdspeak/web_server.py:75` `WebSocketManager.broadcast(BroadcastMessage(type, data))`.
- `web/src/runtime/RuntimeBus.tsx:18` `{state, lastFrame, subscribe}`;
  `useRuntimeFrame<T>(type)` L113; example
  `web/src/components/AmbientLayer.tsx:24`.

## 5. Kernel admission — see §2 Ask chain (the exact envelope to copy).

## 6. Web
- `web/src/lib/primitives.ts:28–47` `PrimitiveKind` (19); type gates
  `web/src/desk/world.ts:30–56` and
  `web/src/desk/pullouts/registry.ts:24–44`.
- Pullout contract `pullouts/types.ts` `{object, onClose}`; copy
  `DirectoryPullout.tsx` (85 LOC).
- Surface kit `web/src/desk/surface/Surface.tsx` — `SurfaceVerbs` L27,
  `SurfaceSection` L45, `SurfaceRows` L70, `SurfaceRow` L77,
  `SurfaceState` L140.
- Verbs `web/src/desk/verbRegistry.ts:44–65` shape, `VERBS` L165,
  "Open" L372–384; object menus `web/src/desk/floorMenu.ts`
  `objectMenuEntries`; `DeskMenu.tsx:180`.
- List view `web/src/desk/components/DeskListView.tsx` `BAND_LABEL`
  L31–40, `DeskListRow` L45–47.
- `MicButton.tsx:41–76` props; `InletAutocomplete.tsx:145–157` props,
  hook L219 (zones only today).
- Markdown `web/src/desk/surface/Material.tsx:82` (custom, no
  innerHTML) used by `NotePullout.tsx:396`, `ArtifactPullout.tsx:28`.
- Egress `web/src/desk/inferenceEgress.ts` `boundaryEgressLamp` L9,
  `egressScopeLamp` L35. Receipts `hooks/useWriteReceipt.ts:116`.
- To delete: `web/src/desk/chat.ts` (226) + `__tests__/chat.test.ts`;
  re-point `window.test.ts:17,70–71`, `DeskApp.test.tsx:28,72`,
  `writeReceiptGuard.test.ts:20`. (The "chat egress" inherited red is a
  pytest parametrization `[Recipe chat]`, not a vitest.)

## 7. Grounding
- `web/src/desk/grounding.ts` `GroundingSelection` L34, `hubGrounding`
  L53, `fetchGroundingResource` L203; server
  `holdspeak/grounding.py:76` `hydrate_refs_detailed(db, meeting_ids,
  artifact_ids, expand, qualified_refs?, *, query?)`; unknown → L93.

## 8. FTS federation
- `holdspeak/db/memory.py:99` `MemoryRepository.search` L108,
  `_VALID_KINDS` L12, merge L158–167.

## 9. Attachments — no general upload route, no PDF extraction. OUT of DC-01.

## 10. Tests + walks
- Web: `npm run test:web` / `test:desk` (vitest); pytest scoped:
  `HOME=$(mktemp -d) uv run pytest -q tests/ -k <pattern>`.
- Glass rig pattern: `phase-149-one-on-one-loop/assets/story-04-rig.py`
  (in-process `MeetingWebServer`, Playwright, 1440×900 + 393×852).
- Walk: `scripts/door_walk_hs144.py` `ALL_LEGS` L46, `reporter.check`
  L98, `reporter.finding` L113, `reporter.shot`.
