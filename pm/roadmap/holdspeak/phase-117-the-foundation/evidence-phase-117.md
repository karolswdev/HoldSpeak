# Phase 117 — The Foundation: Evidence

**Date:** 2026-08-05
**Stories:** 16/16 done
**Method:** Opus implement -> Terra verify -> Orchestrator stamp

## Test suite baseline

- **Frontend:** 89 test files, 604 tests, all passing
- **Backend:** 3,434+ unit tests passing (pre-existing failures unrelated to this phase)
- **TypeScript:** `npx tsc --noEmit` clean, zero errors

## Story evidence

### 01 — The typed primitives
- 17-kind `Primitive` discriminated union complete
- wireGuard.ts: 6 safe field extractors, 41 tests
- All `fromWire*` mappers take `unknown`, return concrete types or `null`
- `WIRE_MAPPERS satisfies Record<WireKind, ...>` enforces mapper completeness
- Zero `any` inputs to mappers, zero `as JsonRecord` in desk layer
- Missing identity -> null + contextual warning, filtered in loadAll()

### 02 — The store split
- store.ts 1,305 lines -> 4 slices (compositor, data, desk, recording) + window factory
- 40 characterization tests added
- Zero consumer import changes (re-export shim)
- openPullout declaration-driven dispatch preserved from story 16

### 03 — The CSS foundation
- desk.css 6,072 -> 177 lines (root scope + 15 @import statements)
- 17 co-located CSS module files created
- 25 component files updated with co-located imports
- desk-tokens.css convenience re-export created
- Zero CSS rules added, removed, or renamed

### 04 — The window subsystem
- DeskWindow.tsx 1,766 -> 898 lines
- 9 extracted modules under window/ (geometry, registry, launcher, SnapGhost, Switcher, Expose, VerbGlyph, ShortcutSheet, Dock)
- windowGeometry.ts has zero React imports (pure functions)
- Circular dependency resolved via dependency injection

### 05 — The typed cores
- 16 core page components typed with concrete generics
- core-types.ts: CoreProps + ~50 endpoint response interfaces
- Zero `JsonRecord` in cores, zero `apiFetch<any>`
- Barrel re-export at cores/index.ts

### 06 — The component narrowing
- Zero `as any` in desk production code (was 49+ casts)
- `DeskItem = Primitive` temporary alias removed
- Proper discriminated union narrowing throughout (kind guards, `in` operator)

### 07 — The core unification
- 4 shared patterns extracted: useAction, useCoreWings, renderHeroSlot, CoreResourceGuard
- Adopted across 13 cores
- Net -107 lines

### 08 — The dictation decomposition
- DictationCore.tsx 1,803 -> 89 lines
- 13 sub-components under dictation/ (SpeakFace, InstrumentStrip, AimRow, UtteranceWell, ResultPanel, Blocks, Journal, Knowledge, Memory, Readiness, DictationSections, shared, useSpeakDeck)

### 09 — The history decomposition
- HistoryCore.tsx 1,311 -> 321 lines
- 16 sub-components under history/ (MeetingDetail, MeetingHeader, CaptureSlab, ArtifactsLibrary, NeedsYouTable, TranscriptWell, SettledList, AftercareGadgets, CatalogRail, DoorSection, ImportSection, helpers, useMeetingData, StateTokenSpan)

### 10 — The schema extraction
- core.py 2,314 -> 247 lines
- schema.py + migrations.py extracted
- models/ split into 7 domain modules (meeting, actions, knowledge, workbench, activity, infra, mixins)
- Serializable mixin applied to 20+ model classes
- Backwards-compatible barrel re-exports

### 11 — The backend errors
- holdspeak/errors.py: HoldSpeakError base + 6 domain subclasses
- 24 exception classes re-parented across 14 modules
- 2 DiscoveryError dataclasses fixed to be proper Exception subclasses
- Structured error responses wired in web_server.py

### 12 — The backend cleanup
- Repository registry via __init_subclass__ (38 repos auto-discovered)
- Database.__init__ simplified to registry loop (core.py -> 183 lines)
- Connection management extracted to connection.py
- config.py split into 7 domain modules under config/

### 13 — The detail contract
- detail-types.ts: WorkbenchDetail, WorkbenchItem, WorkbenchRun, Skill, MemoryEntry
- usePrimitiveDetail hook: fetch/loading/error/refocus, 7 tests
- 12 API endpoints extracted from WorkbenchWindow to api.ts
- WorkbenchWindow useState: 21 -> 16

### 14 — The kind exhaustiveness gate
- `satisfies Record<PrimitiveKind, ...>` on all full registries
- `satisfies Partial<Record<...>>` on partial registries
- AssertAllKinds type check on ORDER array
- assertNever.ts applied in Pullout.tsx and InlineEditor.tsx
- Phantom-kind test: adding "test_phantom" produces compile errors in PRIMITIVES, DESK_GROUPS, ORDER, TypedItems

### 15 — The pullout protocol
- Pullout.tsx 983 -> 94 lines (chrome shell)
- InlineEditor.tsx 577 -> 69 lines
- 10 per-kind pullout components + FallbackPullout
- 4 per-kind editor components + useDebouncedSave
- CapabilitySection shared component
- PULLOUT_CONTENT + INLINE_EDITOR_CONTENT registries with satisfies gates

### 16 — The surface declaration
- SurfaceDeclaration type: pullout | window | surface | none
- surface field added to PrimitiveDescriptor, populated for all 17 kinds
- openPullout refactored to declaration-driven dispatch via resolveKindFromId
- surfaceOf() accessor added
- Exhaustive switch with assertNever
