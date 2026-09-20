# Evidence - HS-201-09

- **Story:** HS-201-09 - Connect an engine from the face
- **Status:** done
- **Date:** 2026-09-20

## Proof

### Captured run — 2026-09-20T06:10:45Z

- **Command:** `bash -c HOME=$(mktemp -d) uv run pytest -q tests/unit/test_hs201_09_connect_an_engine_from_the_face.py tests/unit/test_hs170_concierge_wire.py tests/unit/test_hs201_summary_assignment.py tests/unit/test_model_library_providers.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
.........................................................                [100%]
57 passed in 3.06s
```

### Captured run — 2026-09-20T06:10:52Z

- **Command:** `bash -c cd web && npx vitest run src/features/concierge`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text

 RUN  v4.1.9 /Users/karol/dev/tools/wt-201-b/web


 Test Files  3 passed (3)
      Tests  48 passed (48)
   Start at  00:10:53
   Duration  1.15s (transform 595ms, setup 347ms, import 861ms, tests 461ms, environment 964ms)
```

### Captured run — 2026-09-20T06:10:54Z

- **Command:** `bash -c cd web && npx tsc --noEmit && echo "tsc clean"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
tsc clean
```

### Captured run — 2026-09-20T06:11:07Z

- **Command:** `bash -c HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q -s tests/e2e/test_hs201_09_connect_engine_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
ENGINE real LAN http://192.168.1.43:8080/v1 model=Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/models-cold-1440.png
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/add-engine-refused-1440.png
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/add-engine-ready-1440.png
SUMMARY ASSIGNED {'schema': 'ConciergeSummaryAssignmentProjection@1', 'capabilityId': 'meeting.deferred_analysis', 'status': 'assigned', 'assignmentRevision': 1, 'profileId': 'engine-192-168-1-43-8080', 'profileRevision': 1, 'label': '192.168.1.43:8080', 'boundary': 'lan', 'readiness': 'ready'}
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/models-engine-connected-1440.png
WAITING GROUPS ['speech_recognition']
SUMMARY OFF {'schema': 'ConciergeSummaryAssignmentProjection@1', 'capabilityId': 'meeting.deferred_analysis', 'status': 'off', 'assignmentRevision': 3, 'profileId': None, 'profileRevision': None, 'label': None, 'boundary': None, 'readiness': None} / roster no_assignment
REPAIR REASON This engine cannot give a structured result.
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/models-summary-off-1440.png
DOOR Go > Models opened the Models window
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/models-from-the-go-menu-1440.png
.GEOM ['line display=flex wrap=wrap w=337', 'surface-ledger-lead display=block flex=0 0 36px ovf=visible rect=28,36 scrollW=36 clientW=36', 'surface-ledger-primary display=block flex=1 1 calc(100% - 48px) ovf=visible rect=74,291 scrollW=291 clientW=291', 'concierge-set-cells display=contents flex=0 1 auto ovf=visible rect=0,0 scrollW=0 clientW=0', ' btn btn--ghost btn--sm concierge-picker-trigger display=flex flex=0 1 auto ovf=hidden rect=28,51 scrollW=49 clientW=49', ' concierge-set-state display=block flex=0 0 auto ovf=visible rect=287,78 scrollW=78 clientW=78', ' concierge-set-line2 display=flex flex=1 0 100% ovf=visible rect=28,337 scrollW=337 clientW=337']
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/models-cold-393.png
GEOM ['line display=flex wrap=wrap w=337', 'surface-ledger-lead display=block flex=0 0 36px ovf=visible rect=28,36 scrollW=36 clientW=36', 'surface-ledger-primary display=block flex=1 1 calc(100% - 48px) ovf=visible rect=74,291 scrollW=291 clientW=291', 'concierge-set-cells display=contents flex=0 1 auto ovf=visible rect=0,0 scrollW=0 clientW=0', ' btn btn--ghost btn--sm concierge-picker-trigger display=flex flex=0 1 auto ovf=hidden rect=28,51 scrollW=49 clientW=49', ' concierge-set-state display=block flex=0 0 auto ovf=visible rect=287,78 scrollW=78 clientW=78', ' concierge-set-line2 display=flex flex=1 0 100% ovf=visible rect=28,337 scrollW=337 clientW=337']
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/add-engine-refused-393.png
GEOM ['line display=flex wrap=wrap w=337', 'surface-ledger-lead display=block flex=0 0 36px ovf=visible rect=28,36 scrollW=36 clientW=36', 'surface-ledger-primary display=block flex=1 1 calc(100% - 48px) ovf=visible rect=74,291 scrollW=291 clientW=291', 'concierge-set-cells display=contents flex=0 1 auto ovf=visible rect=0,0 scrollW=0 clientW=0', ' btn btn--ghost btn--sm concierge-picker-trigger display=flex flex=0 1 auto ovf=hidden rect=28,51 scrollW=49 clientW=49', ' concierge-set-state display=block flex=0 0 auto ovf=visible rect=287,78 scrollW=78 clientW=78', ' concierge-set-line2 display=flex flex=1 0 100% ovf=visible rect=28,337 scrollW=337 clientW=337']
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/add-engine-ready-393.png
SUMMARY ASSIGNED {'schema': 'ConciergeSummaryAssignmentProjection@1', 'capabilityId': 'meeting.deferred_analysis', 'status': 'assigned', 'assignmentRevision': 1, 'profileId': 'engine-192-168-1-43-8080', 'profileRevision': 1, 'label': '192.168.1.43:8080', 'boundary': 'lan', 'readiness': 'ready'}
GEOM ['line display=flex wrap=wrap w=337', 'surface-ledger-lead display=block flex=0 0 36px ovf=visible rect=28,36 scrollW=36 clientW=36', 'surface-ledger-primary display=block flex=1 1 calc(100% - 48px) ovf=visible rect=74,291 scrollW=291 clientW=291', 'concierge-set-cells display=contents flex=0 1 auto ovf=visible rect=0,0 scrollW=0 clientW=0', ' btn btn--ghost btn--sm concierge-picker-trigger display=flex flex=0 1 auto ovf=hidden rect=28,152 scrollW=150 clientW=150', ' concierge-set-state display=block flex=0 0 auto ovf=visible rect=301,64 scrollW=64 clientW=64', ' concierge-set-line2 display=flex flex=1 0 100% ovf=visible rect=28,337 scrollW=337 clientW=337']
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/models-engine-connected-393.png
WAITING GROUPS ['speech_recognition']
SUMMARY OFF {'schema': 'ConciergeSummaryAssignmentProjection@1', 'capabilityId': 'meeting.deferred_analysis', 'status': 'off', 'assignmentRevision': 3, 'profileId': None, 'profileRevision': None, 'label': None, 'boundary': None, 'readiness': None} / roster no_assignment
REPAIR REASON This engine cannot give a structured result.
GEOM ['line display=flex wrap=wrap w=337', 'surface-ledger-lead display=block flex=0 0 36px ovf=visible rect=28,36 scrollW=36 clientW=36', 'surface-ledger-primary display=block flex=1 1 calc(100% - 48px) ovf=visible rect=74,291 scrollW=291 clientW=291', 'concierge-set-cells display=contents flex=0 1 auto ovf=visible rect=0,0 scrollW=0 clientW=0', ' btn btn--ghost btn--sm concierge-picker-trigger display=flex flex=0 1 auto ovf=hidden rect=28,51 scrollW=49 clientW=49', ' concierge-set-state display=block flex=0 0 auto ovf=visible rect=314,51 scrollW=51 clientW=51', ' concierge-set-line2 display=flex flex=1 0 100% ovf=visible rect=28,337 scrollW=337 clientW=337']
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/models-summary-off-393.png
DOOR Go > Models opened the Models window
GEOM ['line display=flex wrap=wrap w=337', 'surface-ledger-lead display=block flex=0 0 36px ovf=visible rect=28,36 scrollW=36 clientW=36', 'surface-ledger-primary display=block flex=1 1 calc(100% - 48px) ovf=visible rect=74,291 scrollW=291 clientW=291', 'concierge-set-cells display=contents flex=0 1 auto ovf=visible rect=0,0 scrollW=0 clientW=0', ' btn btn--ghost btn--sm concierge-picker-trigger display=flex flex=0 1 auto ovf=hidden rect=28,51 scrollW=49 clientW=49', ' concierge-set-state display=block flex=0 0 auto ovf=visible rect=314,51 scrollW=51 clientW=51', ' concierge-set-line2 display=flex flex=1 0 100% ovf=visible rect=28,337 scrollW=337 clientW=337']
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/models-from-the-go-menu-393.png
.
2 passed in 11.99s
```

## Red before green

Each fence was run against the pre-fix files before the fix landed. The
face files were restored from `git show HEAD:<path>` for the run and put
back from a sha256-verified copy afterwards (no `git stash`, `reset`,
`checkout --`, `restore`, `clean` or `switch` was used anywhere in this
story).

### 1. The four service fences — `tests/unit/test_hs201_09_connect_an_engine_from_the_face.py`

Run before any product change (`HOME=$(mktemp -d) uv run pytest -q`):

```text
FAILED …::test_face_draft_keys_are_exactly_the_endpoint_drafts_the_service_accepts
FAILED …::test_define_endpoint_accepts_the_face_draft
FAILED …::test_apply_off_on_the_summary_group_clears_the_exact_capability
FAILED …::test_summary_projection_says_off_after_the_assignment_was_cleared
FAILED …::test_summary_projection_stays_unassigned_when_nothing_was_ever_written
FAILED …::test_tool_incompatible_repair_carries_a_plain_reason
6 failed, 1 passed in 1.19s
```

(the one pass is `…_with_nothing_assigned_clears_nothing`, which holds both
before and after: it is the guard that OFF never clears what was never set.)

After: `7 passed`.

### 2. The face fences — `web/src/features/concierge/__tests__/connectAnEngine.test.tsx`

Run with `ConciergeCore.tsx`, `useConciergeController.ts`, `api.ts` and
`concierge.css` restored to `HEAD`:

```text
❯ src/features/concierge/__tests__/connectAnEngine.test.tsx (13 tests | 12 failed)
  × is enabled while an unrelated group is WAITING
  × never sends the WAITING group it did not touch
  × sends engineId OFF for meetings
  × shows OFF after the owner turned it off, not the proposal
  × names an assigned engine detection no longer lists
  × is a library Button, not a span            (expected 'SPAN' to be 'BUTTON')
  × shows the refusal's plain reason beside the verb
  × names the model the server serves after a good check
  × posts a lawful draft and then the one summary selection
  × refuses to claim success when the selection did not succeed
  × keeps one filled primary while the well holds a READY engine
  × draws the service's plain line on the row
```

(the 13th, "shows the applied engine when one is assigned", passes before
the fix too: the PROPOSAL happens to name the same engine there.)

After: `13 passed`.

### 3. The 393 overlap — `tests/e2e/test_hs201_09_connect_engine_glass.py`

Run with only `web/src/features/concierge/concierge.css` restored to `HEAD`:

```text
E   AssertionError: models-engine-connected at 393: [
      'ink escapes surface-ledger-primary scrollW=69 clientW=54 :: Thoughts & notes',
      'ink escapes surface-ledger-primary scrollW=64 clientW=54 :: Writing & dictation',
      'ink escapes surface-ledger-primary scrollW=68 clientW=54 :: Meetings',
      'ink escapes surface-ledger-primary scrollW=87 clientW=54 :: Background']
1 failed in 13.34s
```

That is the rehearsal's `02a-choose-an-engine-393.png` defect, measured:
the group name's box was squeezed to 54 px by the picker beside it while
`overflow: visible` let 69–87 px of text run over that picker. After the
fix the same run is `2 passed` and the primary reads
`flex=1 1 calc(100% - 48px)` (see the GEOM lines above).

### Captured run — 2026-09-20T06:15:18Z

- **Command:** `bash -c cd web && npx tsc --noEmit && npx vitest run src/features/concierge 2>&1 | tail -6`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text

 Test Files  3 passed (3)
      Tests  48 passed (48)
   Start at  00:15:27
   Duration  1.36s (transform 566ms, setup 270ms, import 814ms, tests 504ms, environment 1.64s)
```

### Captured run — 2026-09-20T06:15:29Z

- **Command:** `bash -c HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q tests/e2e/test_hs170_concierge_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fe25701b9900a78a36ab8dd3bca7470f66f1d1cb

```text
.......                                                                  [100%]
7 passed in 52.36s
```

## The smallest honest change, named

The Scope allowed either side to move. **The FACE moved, not the service.**

`ModelLibraryApplicationService._provider_draft`
(`holdspeak/services/model_library_service.py:276-294`) refuses any body
whose key set is not exactly its allowed set — that strictness is the
command boundary's whole point, and widening it to mint `profile_id` and
`provider_family` from the endpoint would have added a second, looser way
into the same command. So the face now sends the body the service already
accepts: `web/src/features/concierge/endpointDraft.ts` mints the lawful
draft (a derived `profile_id` so the same address always replays to the
same profile, `provider_family: "openai_compatible"`, the label as
`host:port` because `_safe_field` refuses `/`, and the model the hub's own
`/models` read named). Nothing in `model_library_service.py` changed.

The two sides are pinned to each other: `ENDPOINT_DRAFT_KEYS` is declared
in that module, asserted against the built draft in vitest, and read by
`tests/unit/test_hs201_09_connect_an_engine_from_the_face.py::
test_face_draft_keys_are_exactly_the_endpoint_drafts_the_service_accepts`,
which compares it with the service's allowed set. They cannot drift apart
in silence again.

The other four changes:

- `concierge_service.apply` clears the exact `meeting.deferred_analysis`
  assignment on OFF, through the existing `clear_assignment` CAS seam.
- `summary_assignment_projection` reads the tombstoned head so a cleared
  assignment answers `off` instead of looking like "never chosen".
- `repairs` maps the assignment authority's issue code to one plain line.
- The face reads `summaryAssignment` for the Meetings row, applies per
  group, and keeps its 393 rows from overlapping.

### Captured run — 2026-09-20T07:16:09Z

- **Command:** `bash -c HOME=$(mktemp -d) uv run pytest -q tests/unit/test_hs201_09_connect_an_engine_from_the_face.py tests/unit/test_hs170_concierge_wire.py tests/unit/test_hs201_summary_assignment.py tests/unit/test_model_library_providers.py tests/unit/test_profile_key_live_resolution.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** abb141cc8f2e8a38c7f0e4dc70badbb8ccc59a9a

```text
...............................................................          [100%]
63 passed in 3.37s
```

### Captured run — 2026-09-20T07:16:18Z

- **Command:** `bash -c cd web && npx tsc --noEmit && echo TYPECHECK CLEAN && npx vitest run src/features/concierge 2>&1 | tail -6`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** abb141cc8f2e8a38c7f0e4dc70badbb8ccc59a9a

```text
TYPECHECK CLEAN

 Test Files  3 passed (3)
      Tests  56 passed (56)
   Start at  01:16:28
   Duration  1.24s (transform 581ms, setup 248ms, import 835ms, tests 650ms, environment 838ms)
```

### Captured run — 2026-09-20T07:16:29Z

- **Command:** `bash -c HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q -s tests/e2e/test_hs201_09_connect_engine_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** abb141cc8f2e8a38c7f0e4dc70badbb8ccc59a9a

```text
ENGINE real LAN http://192.168.1.43:8080/v1 model=Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/models-cold-1440.png
REFUSED REASON Nothing answers at this address.
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/add-engine-refused-1440.png
STALE CHECK dropped on address edit
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/add-engine-ready-1440.png
SUMMARY ASSIGNED {'schema': 'ConciergeSummaryAssignmentProjection@1', 'capabilityId': 'meeting.deferred_analysis', 'status': 'assigned', 'assignmentRevision': 1, 'profileId': 'engine-192-168-1-43-8080', 'profileRevision': 1, 'label': '192.168.1.43:8080', 'boundary': 'lan', 'readiness': 'ready'} (one gesture, no Use these)
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/models-engine-connected-1440.png
WAITING GROUPS ['speech_recognition']
SUMMARY OFF {'schema': 'ConciergeSummaryAssignmentProjection@1', 'capabilityId': 'meeting.deferred_analysis', 'status': 'off', 'assignmentRevision': 3, 'profileId': None, 'profileRevision': None, 'label': None, 'boundary': None, 'readiness': None} / roster no_assignment
REPAIR REASON This engine cannot give a structured result.
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/models-summary-off-1440.png
SUMMARY BACK ON {'schema': 'ConciergeSummaryAssignmentProjection@1', 'capabilityId': 'meeting.deferred_analysis', 'status': 'assigned', 'assignmentRevision': 4, 'profileId': 'engine-192-168-1-43-8080', 'profileRevision': 1, 'label': '192.168.1.43:8080', 'boundary': 'lan', 'readiness': 'ready'}
FACE CENSUS presets=0 repairs=1
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/models-engine-back-on-1440.png
DOOR Go > Models opened the Models window
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/models-from-the-go-menu-1440.png
.GEOM ['line display=flex wrap=wrap w=337', 'surface-ledger-lead display=block flex=0 0 36px ovf=visible rect=28,36 scrollW=36 clientW=36', 'surface-ledger-primary display=block flex=1 1 calc(100% - 48px) ovf=visible rect=74,291 scrollW=291 clientW=291', 'concierge-set-cells display=contents flex=0 1 auto ovf=visible rect=0,0 scrollW=0 clientW=0', ' btn btn--ghost btn--sm concierge-picker-trigger display=flex flex=0 1 auto ovf=hidden rect=28,51 scrollW=49 clientW=49', ' concierge-set-state display=block flex=0 0 auto ovf=visible rect=287,78 scrollW=78 clientW=78', ' concierge-set-line2 display=flex flex=1 0 100% ovf=visible rect=28,337 scrollW=337 clientW=337']
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/models-cold-393.png
REFUSED REASON Nothing answers at this address.
GEOM ['line display=flex wrap=wrap w=337', 'surface-ledger-lead display=block flex=0 0 36px ovf=visible rect=28,36 scrollW=36 clientW=36', 'surface-ledger-primary display=block flex=1 1 calc(100% - 48px) ovf=visible rect=74,291 scrollW=291 clientW=291', 'concierge-set-cells display=contents flex=0 1 auto ovf=visible rect=0,0 scrollW=0 clientW=0', ' btn btn--ghost btn--sm concierge-picker-trigger display=flex flex=0 1 auto ovf=hidden rect=28,51 scrollW=49 clientW=49', ' concierge-set-state display=block flex=0 0 auto ovf=visible rect=287,78 scrollW=78 clientW=78', ' concierge-set-line2 display=flex flex=1 0 100% ovf=visible rect=28,337 scrollW=337 clientW=337']
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/add-engine-refused-393.png
STALE CHECK dropped on address edit
GEOM ['line display=flex wrap=wrap w=337', 'surface-ledger-lead display=block flex=0 0 36px ovf=visible rect=28,36 scrollW=36 clientW=36', 'surface-ledger-primary display=block flex=1 1 calc(100% - 48px) ovf=visible rect=74,291 scrollW=291 clientW=291', 'concierge-set-cells display=contents flex=0 1 auto ovf=visible rect=0,0 scrollW=0 clientW=0', ' btn btn--ghost btn--sm concierge-picker-trigger display=flex flex=0 1 auto ovf=hidden rect=28,51 scrollW=49 clientW=49', ' concierge-set-state display=block flex=0 0 auto ovf=visible rect=287,78 scrollW=78 clientW=78', ' concierge-set-line2 display=flex flex=1 0 100% ovf=visible rect=28,337 scrollW=337 clientW=337']
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/add-engine-ready-393.png
SUMMARY ASSIGNED {'schema': 'ConciergeSummaryAssignmentProjection@1', 'capabilityId': 'meeting.deferred_analysis', 'status': 'assigned', 'assignmentRevision': 1, 'profileId': 'engine-192-168-1-43-8080', 'profileRevision': 1, 'label': '192.168.1.43:8080', 'boundary': 'lan', 'readiness': 'ready'} (one gesture, no Use these)
GEOM ['line display=flex wrap=wrap w=337', 'surface-ledger-lead display=block flex=0 0 36px ovf=visible rect=28,36 scrollW=36 clientW=36', 'surface-ledger-primary display=block flex=1 1 calc(100% - 48px) ovf=visible rect=74,291 scrollW=291 clientW=291', 'concierge-set-cells display=contents flex=0 1 auto ovf=visible rect=0,0 scrollW=0 clientW=0', ' btn btn--ghost btn--sm concierge-picker-trigger display=flex flex=0 1 auto ovf=hidden rect=28,152 scrollW=150 clientW=150', ' concierge-set-state display=block flex=0 0 auto ovf=visible rect=301,64 scrollW=64 clientW=64', ' concierge-set-line2 display=flex flex=1 0 100% ovf=visible rect=28,337 scrollW=337 clientW=337']
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/models-engine-connected-393.png
WAITING GROUPS ['speech_recognition']
SUMMARY OFF {'schema': 'ConciergeSummaryAssignmentProjection@1', 'capabilityId': 'meeting.deferred_analysis', 'status': 'off', 'assignmentRevision': 3, 'profileId': None, 'profileRevision': None, 'label': None, 'boundary': None, 'readiness': None} / roster no_assignment
REPAIR REASON This engine cannot give a structured result.
GEOM ['line display=flex wrap=wrap w=337', 'surface-ledger-lead display=block flex=0 0 36px ovf=visible rect=28,36 scrollW=36 clientW=36', 'surface-ledger-primary display=block flex=1 1 calc(100% - 48px) ovf=visible rect=74,291 scrollW=291 clientW=291', 'concierge-set-cells display=contents flex=0 1 auto ovf=visible rect=0,0 scrollW=0 clientW=0', ' btn btn--ghost btn--sm concierge-picker-trigger display=flex flex=0 1 auto ovf=hidden rect=28,51 scrollW=49 clientW=49', ' concierge-set-state display=block flex=0 0 auto ovf=visible rect=314,51 scrollW=51 clientW=51', ' concierge-set-line2 display=flex flex=1 0 100% ovf=visible rect=28,337 scrollW=337 clientW=337']
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/models-summary-off-393.png
SUMMARY BACK ON {'schema': 'ConciergeSummaryAssignmentProjection@1', 'capabilityId': 'meeting.deferred_analysis', 'status': 'assigned', 'assignmentRevision': 4, 'profileId': 'engine-192-168-1-43-8080', 'profileRevision': 1, 'label': '192.168.1.43:8080', 'boundary': 'lan', 'readiness': 'ready'}
FACE CENSUS presets=0 repairs=1
GEOM ['line display=flex wrap=wrap w=337', 'surface-ledger-lead display=block flex=0 0 36px ovf=visible rect=28,36 scrollW=36 clientW=36', 'surface-ledger-primary display=block flex=1 1 calc(100% - 48px) ovf=visible rect=74,291 scrollW=291 clientW=291', 'concierge-set-cells display=contents flex=0 1 auto ovf=visible rect=0,0 scrollW=0 clientW=0', ' btn btn--ghost btn--sm concierge-picker-trigger display=flex flex=0 1 auto ovf=hidden rect=28,152 scrollW=150 clientW=150', ' concierge-set-state display=block flex=0 0 auto ovf=visible rect=301,64 scrollW=64 clientW=64', ' concierge-set-line2 display=flex flex=1 0 100% ovf=visible rect=28,337 scrollW=337 clientW=337']
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/models-engine-back-on-393.png
DOOR Go > Models opened the Models window
GEOM ['line display=flex wrap=wrap w=337', 'surface-ledger-lead display=block flex=0 0 36px ovf=visible rect=28,36 scrollW=36 clientW=36', 'surface-ledger-primary display=block flex=1 1 calc(100% - 48px) ovf=visible rect=74,291 scrollW=291 clientW=291', 'concierge-set-cells display=contents flex=0 1 auto ovf=visible rect=0,0 scrollW=0 clientW=0', ' btn btn--ghost btn--sm concierge-picker-trigger display=flex flex=0 1 auto ovf=hidden rect=28,152 scrollW=150 clientW=150', ' concierge-set-state display=block flex=0 0 auto ovf=visible rect=301,64 scrollW=64 clientW=64', ' concierge-set-line2 display=flex flex=1 0 100% ovf=visible rect=28,337 scrollW=337 clientW=337']
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/models-from-the-go-menu-393.png
.
2 passed in 15.20s
```

### Captured run — 2026-09-20T07:16:52Z

- **Command:** `bash -c HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q tests/e2e/test_hs170_concierge_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** abb141cc8f2e8a38c7f0e4dc70badbb8ccc59a9a

```text
.......                                                                  [100%]
7 passed in 51.13s
```

## Counsel fix round

Astra's counsel-on-built (`checks/sitting-fixes-built-astra.md`) returned
DO-NOT-RATIFY with four findings against story 09. All four are fixed, each
with a fence that was red first. The captures above this section are the
green runs after the round; the red tails are below.

### 1. One gesture finishes setup

`Use this for summaries` saved the assignment and only reloaded Models, so
the arrival could keep its SETUP row. It now ends the way ordinary Apply
ends (`web/src/features/concierge/useConciergeController.ts` — the same
close + `announceTaskReturn(from)` block as `apply`), with `from` captured
synchronously before the await.

Red (vitest, against the pre-round controller):

```text
× fires the one readiness signal the arrival listens for
× closes the Models window, like ordinary Apply
```

Green on the glass, with no second click:

```text
SUMMARY ASSIGNED {… 'status': 'assigned', 'profileId': 'engine-192-168-1-43-8080',
  'profileRevision': 1, 'boundary': 'lan'} (one gesture, no Use these)
```

The walk now asserts the SETUP row is present BEFORE the gesture, that the
window closes itself, that both blocker verbs are gone afterwards, and that
`Choose an engine` is nowhere in the page behind the reopened Models.
`assets/story-09-shots/models-engine-connected-1440.png` shows the desk
with no SETUP row.

### 2. OFF then ON

`_summary_assignment_revision` reads ACTIVE heads only, so after a clear it
answered 0 while `set_assignment`
(`holdspeak/services/inference_assignment_service.py:402`) compared against
`_current`, which still saw the tombstone. New
`_summary_expected_revision(assignment_service, principal, db)` presents the
same number the projection publishes. The OFF path keeps the active-only
read, so re-applying OFF writes no second tombstone
(`test_apply_off_twice_clears_only_once`).

Red (pytest): `test_apply_on_after_off_presents_the_tombstone_revision`.
Red on the GLASS, with only that one call site reverted:

```text
E  AssertionError: {'assignmentRevision': 3, …}
E  assert 'off' == 'assigned'
1 failed in 7.05s
```

Green:

```text
SUMMARY OFF     {… 'status': 'off',      'assignmentRevision': 3} / roster no_assignment
SUMMARY BACK ON {… 'status': 'assigned', 'assignmentRevision': 4,
                   'profileId': 'engine-192-168-1-43-8080'}
```

### 3. A changed address invalidates the check

The field used the raw setter. It now goes through `editAddEngineUrl`,
which drops READY and the model it named the moment the address differs,
and a check answer whose address no longer matches the field is discarded
(`addEngineUrlRef`). The repair row's `endpoint_editor` handoff goes through
the same setter.

Red (vitest): `× drops READY and the named model when the address changes`,
`× ignores a check answer for an address already replaced`.
Green on the glass: `STALE CHECK dropped on address edit`.

### 4. The visual bar

- **One filled primary, arbitrated once.** `primarySlot()`
  (`web/src/features/concierge/ConciergeCore.tsx`) names the single
  claimant — the Add-engine submit while it holds a READY engine, else the
  first repair, else the footer's `Use these`, else the first preset
  `Download`. Every verb asks it; none decides for itself. Red (vitest):
  three cases, including `× keeps exactly one with two repairs and two
  presets on the face`. Green: `["Choose"]`, `["Use this for summaries"]`,
  `["Download"]` respectively.
- **The refusal is in plain words.** `unreachable_reason`
  (`holdspeak/setup_runtime.py`) replaces
  `<urlopen error [Errno 61] Connection refused>`; the socket's words stay
  in the hub log. Red (pytest): three parametrised cases. Green on the
  glass: `REFUSED REASON Nothing answers at this address.`
- **The Check row names its host.** An `EgressChip` for the typed address
  sits before the `Check` verb (Article III at the point of decision), with
  `isLanAddress` deciding the scope. Red (vitest): `× draws the egress chip
  for the typed address`. Green on the glass: the rig asserts `127.0.0.1`
  for the refused address and `192.168.1.43` for the LAN one.

### What this round could NOT measure on the glass

`FACE CENSUS presets=0 repairs=1`: an isolated HOME lists no downloadable
catalog presets, so the **rig** never had a preset `Download` beside the
other claimants. The three-way arbitration (two repairs + two presets + a
READY Add-engine well) is measured in vitest, where those rows are present
by construction, not in the browser walk.

### Captured run — 2026-09-20T07:31:07Z

- **Command:** `bash -c cd web && npx tsc --noEmit && echo TYPECHECK CLEAN && npx vitest run src/features/concierge 2>&1 | tail -6`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9704e435d2c361e0e162399cd9305b96fc7bccd1

```text
TYPECHECK CLEAN

 Test Files  3 passed (3)
      Tests  58 passed (58)
   Start at  01:31:21
   Duration  1.91s (transform 774ms, setup 693ms, import 1.49s, tests 778ms, environment 1.19s)
```

### Captured run — 2026-09-20T07:31:23Z

- **Command:** `bash -c HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q -s tests/e2e/test_hs201_09_connect_engine_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9704e435d2c361e0e162399cd9305b96fc7bccd1

```text
[glass_infra] web bundle rebuilt in 8.5s
ENGINE real LAN http://192.168.1.43:8080/v1 model=Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/models-cold-1440.png
REFUSED REASON Nothing answers at this address.
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/add-engine-refused-1440.png
STALE CHECK dropped on address edit
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/add-engine-ready-1440.png
SUMMARY ASSIGNED {'schema': 'ConciergeSummaryAssignmentProjection@1', 'capabilityId': 'meeting.deferred_analysis', 'status': 'assigned', 'assignmentRevision': 1, 'profileId': 'engine-192-168-1-43-8080', 'profileRevision': 1, 'label': '192.168.1.43:8080', 'boundary': 'lan', 'readiness': 'ready'} (one gesture, no Use these)
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/models-engine-connected-1440.png
WAITING GROUPS ['speech_recognition']
SUMMARY OFF {'schema': 'ConciergeSummaryAssignmentProjection@1', 'capabilityId': 'meeting.deferred_analysis', 'status': 'off', 'assignmentRevision': 3, 'profileId': None, 'profileRevision': None, 'label': None, 'boundary': None, 'readiness': None} / roster no_assignment
REPAIR REASON This engine cannot give a structured result.
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/models-summary-off-1440.png
SUMMARY BACK ON {'schema': 'ConciergeSummaryAssignmentProjection@1', 'capabilityId': 'meeting.deferred_analysis', 'status': 'assigned', 'assignmentRevision': 4, 'profileId': 'engine-192-168-1-43-8080', 'profileRevision': 1, 'label': '192.168.1.43:8080', 'boundary': 'lan', 'readiness': 'ready'}
FACE CENSUS presets=0 repairs=1
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/models-engine-back-on-1440.png
DOOR Go > Models opened the Models window
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/models-from-the-go-menu-1440.png
.GEOM ['line display=flex wrap=wrap w=337', 'surface-ledger-lead display=block flex=0 0 36px ovf=visible rect=28,36 scrollW=36 clientW=36', 'surface-ledger-primary display=block flex=1 1 calc(100% - 48px) ovf=visible rect=74,291 scrollW=291 clientW=291', 'concierge-set-cells display=contents flex=0 1 auto ovf=visible rect=0,0 scrollW=0 clientW=0', ' btn btn--ghost btn--sm concierge-picker-trigger display=flex flex=0 1 auto ovf=hidden rect=28,51 scrollW=49 clientW=49', ' concierge-set-state display=block flex=0 0 auto ovf=visible rect=287,78 scrollW=78 clientW=78', ' concierge-set-line2 display=flex flex=1 0 100% ovf=visible rect=28,337 scrollW=337 clientW=337']
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/models-cold-393.png
REFUSED REASON Nothing answers at this address.
GEOM ['line display=flex wrap=wrap w=337', 'surface-ledger-lead display=block flex=0 0 36px ovf=visible rect=28,36 scrollW=36 clientW=36', 'surface-ledger-primary display=block flex=1 1 calc(100% - 48px) ovf=visible rect=74,291 scrollW=291 clientW=291', 'concierge-set-cells display=contents flex=0 1 auto ovf=visible rect=0,0 scrollW=0 clientW=0', ' btn btn--ghost btn--sm concierge-picker-trigger display=flex flex=0 1 auto ovf=hidden rect=28,51 scrollW=49 clientW=49', ' concierge-set-state display=block flex=0 0 auto ovf=visible rect=287,78 scrollW=78 clientW=78', ' concierge-set-line2 display=flex flex=1 0 100% ovf=visible rect=28,337 scrollW=337 clientW=337']
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/add-engine-refused-393.png
STALE CHECK dropped on address edit
GEOM ['line display=flex wrap=wrap w=337', 'surface-ledger-lead display=block flex=0 0 36px ovf=visible rect=28,36 scrollW=36 clientW=36', 'surface-ledger-primary display=block flex=1 1 calc(100% - 48px) ovf=visible rect=74,291 scrollW=291 clientW=291', 'concierge-set-cells display=contents flex=0 1 auto ovf=visible rect=0,0 scrollW=0 clientW=0', ' btn btn--ghost btn--sm concierge-picker-trigger display=flex flex=0 1 auto ovf=hidden rect=28,51 scrollW=49 clientW=49', ' concierge-set-state display=block flex=0 0 auto ovf=visible rect=287,78 scrollW=78 clientW=78', ' concierge-set-line2 display=flex flex=1 0 100% ovf=visible rect=28,337 scrollW=337 clientW=337']
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/add-engine-ready-393.png
SUMMARY ASSIGNED {'schema': 'ConciergeSummaryAssignmentProjection@1', 'capabilityId': 'meeting.deferred_analysis', 'status': 'assigned', 'assignmentRevision': 1, 'profileId': 'engine-192-168-1-43-8080', 'profileRevision': 1, 'label': '192.168.1.43:8080', 'boundary': 'lan', 'readiness': 'ready'} (one gesture, no Use these)
GEOM ['line display=flex wrap=wrap w=337', 'surface-ledger-lead display=block flex=0 0 36px ovf=visible rect=28,36 scrollW=36 clientW=36', 'surface-ledger-primary display=block flex=1 1 calc(100% - 48px) ovf=visible rect=74,291 scrollW=291 clientW=291', 'concierge-set-cells display=contents flex=0 1 auto ovf=visible rect=0,0 scrollW=0 clientW=0', ' btn btn--ghost btn--sm concierge-picker-trigger display=flex flex=0 1 auto ovf=hidden rect=28,152 scrollW=150 clientW=150', ' concierge-set-state display=block flex=0 0 auto ovf=visible rect=301,64 scrollW=64 clientW=64', ' concierge-set-line2 display=flex flex=1 0 100% ovf=visible rect=28,337 scrollW=337 clientW=337']
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/models-engine-connected-393.png
WAITING GROUPS ['speech_recognition']
SUMMARY OFF {'schema': 'ConciergeSummaryAssignmentProjection@1', 'capabilityId': 'meeting.deferred_analysis', 'status': 'off', 'assignmentRevision': 3, 'profileId': None, 'profileRevision': None, 'label': None, 'boundary': None, 'readiness': None} / roster no_assignment
REPAIR REASON This engine cannot give a structured result.
GEOM ['line display=flex wrap=wrap w=337', 'surface-ledger-lead display=block flex=0 0 36px ovf=visible rect=28,36 scrollW=36 clientW=36', 'surface-ledger-primary display=block flex=1 1 calc(100% - 48px) ovf=visible rect=74,291 scrollW=291 clientW=291', 'concierge-set-cells display=contents flex=0 1 auto ovf=visible rect=0,0 scrollW=0 clientW=0', ' btn btn--ghost btn--sm concierge-picker-trigger display=flex flex=0 1 auto ovf=hidden rect=28,51 scrollW=49 clientW=49', ' concierge-set-state display=block flex=0 0 auto ovf=visible rect=314,51 scrollW=51 clientW=51', ' concierge-set-line2 display=flex flex=1 0 100% ovf=visible rect=28,337 scrollW=337 clientW=337']
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/models-summary-off-393.png
SUMMARY BACK ON {'schema': 'ConciergeSummaryAssignmentProjection@1', 'capabilityId': 'meeting.deferred_analysis', 'status': 'assigned', 'assignmentRevision': 4, 'profileId': 'engine-192-168-1-43-8080', 'profileRevision': 1, 'label': '192.168.1.43:8080', 'boundary': 'lan', 'readiness': 'ready'}
FACE CENSUS presets=0 repairs=1
GEOM ['line display=flex wrap=wrap w=337', 'surface-ledger-lead display=block flex=0 0 36px ovf=visible rect=28,36 scrollW=36 clientW=36', 'surface-ledger-primary display=block flex=1 1 calc(100% - 48px) ovf=visible rect=74,291 scrollW=291 clientW=291', 'concierge-set-cells display=contents flex=0 1 auto ovf=visible rect=0,0 scrollW=0 clientW=0', ' btn btn--ghost btn--sm concierge-picker-trigger display=flex flex=0 1 auto ovf=hidden rect=28,152 scrollW=150 clientW=150', ' concierge-set-state display=block flex=0 0 auto ovf=visible rect=301,64 scrollW=64 clientW=64', ' concierge-set-line2 display=flex flex=1 0 100% ovf=visible rect=28,337 scrollW=337 clientW=337']
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/models-engine-back-on-393.png
DOOR Go > Models opened the Models window
GEOM ['line display=flex wrap=wrap w=337', 'surface-ledger-lead display=block flex=0 0 36px ovf=visible rect=28,36 scrollW=36 clientW=36', 'surface-ledger-primary display=block flex=1 1 calc(100% - 48px) ovf=visible rect=74,291 scrollW=291 clientW=291', 'concierge-set-cells display=contents flex=0 1 auto ovf=visible rect=0,0 scrollW=0 clientW=0', ' btn btn--ghost btn--sm concierge-picker-trigger display=flex flex=0 1 auto ovf=hidden rect=28,152 scrollW=150 clientW=150', ' concierge-set-state display=block flex=0 0 auto ovf=visible rect=301,64 scrollW=64 clientW=64', ' concierge-set-line2 display=flex flex=1 0 100% ovf=visible rect=28,337 scrollW=337 clientW=337']
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots/models-from-the-go-menu-393.png
.
2 passed in 30.89s
```

## Round 2 residual

Astra's second pass left one (b) product defect on 09 and one gap in the
sitting script. Both are fixed; the captures immediately above this section
are the green runs.

### 1. A stale check left `Check` disabled for ever

Round 1 taught `checkNewEngine` to DROP an answer whose address the owner
had already corrected — but both stale branches returned before clearing
`addEngineChecking`, so the verb stayed disabled
(`web/src/features/concierge/ConciergeCore.tsx`, `disabled={ctrl.addEngineChecking || …}`)
and the corrected address could never be checked at all. Dropping the
answer is right; ending the flight was missing.

Both branches — the resolved one and the thrown one — now clear the flag
before returning (`web/src/features/concierge/useConciergeController.ts`,
`checkNewEngine`). Nothing else changes: READY, the named model and the
reason were already cleared by `editAddEngineUrl` when the address moved.

Red first, both paths:

```text
× lets him check the corrected address after a stale ANSWER   1020ms
× lets him check the corrected address after a stale FAILURE  1024ms

 FAIL  …connectAnEngine.test.tsx > a changed address invalidates the check
       (counsel 3) > lets him check the corrected address after a stale ANSWER
Error: expect(element).not.toBeDisabled()
Received element is disabled:
  <button …
 Test Files  1 failed (1)
      Tests  2 failed | 21 passed (23)
```

Green — `web/src/features/concierge/__tests__/connectAnEngine.test.tsx`
now drives a second Check on the replacement address through to its model:

```text
TYPECHECK CLEAN
 Test Files  3 passed (3)
      Tests  58 passed (58)
```

The glass walk is unchanged and still green at both widths against the real
LAN engine (`2 passed`, capture above): `STALE CHECK dropped on address
edit`, `SUMMARY BACK ON … assignmentRevision: 4`.

### 2. The sitting's step 7 had no gesture

`SITTING-07.md` step 7 said only "Dictate one sentence into another app". A
stranger cannot start dictation from that. The step now names the product's
own default gesture, read from the product, not invented:

- `holdspeak/config/ui.py:15-16` — `key: str = "alt_r"`, `display: str = "⌥R"`.
- `holdspeak/hotkey.py:63,71` — "Default hotkey is Right Option (Alt_R)";
  press starts, release stops (`on_press` / `on_release`).
- `holdspeak/web_runtime.py:580` — the hub prints
  `Voice typing hotkey is active: hold ⌥R, speak, release.` at start, and
  the unavailable case tells him to grant Accessibility / Input Monitoring
  and restart (`:582`).

Step 7 now reads: *"Open a different app and click in a text box. Hold the
Right Option key (⌥R), say one sentence, then release the key."* → *"Your
words become text in that app, at the cursor."* A note under the table
points at the startup line and the permission repair.

### Captured run — 2026-09-20T08:48:18Z

- **Command:** `bash -c HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q tests/integration/test_web_history_import_ui.py tests/unit/test_api_surface.py tests/unit/test_doc_drift_guard.py tests/unit/test_phase143_inference_capability_census.py tests/unit/test_phase143_routing_authority_census.py tests/unit/test_phase143_surface_fallback_census.py tests/unit/test_phase200_readiness.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6de419109a60daa1bc1c9e8e515ce1d1df48437b

```text
........................................................................ [ 93%]
.....                                                                    [100%]
77 passed in 31.59s
```

### Captured run — 2026-09-20T08:49:00Z

- **Command:** `bash -c cd web && npx tsc --noEmit && echo TYPECHECK CLEAN && npx vitest run src/features/concierge 2>&1 | tail -4`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6de419109a60daa1bc1c9e8e515ce1d1df48437b

```text
TYPECHECK CLEAN
      Tests  58 passed (58)
   Start at  02:49:09
   Duration  1.33s (transform 597ms, setup 281ms, import 872ms, tests 679ms, environment 914ms)
```

### Captured run — 2026-09-20T08:49:11Z

- **Command:** `bash -c HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q tests/e2e/test_hs201_09_connect_engine_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6de419109a60daa1bc1c9e8e515ce1d1df48437b

```text
..                                                                       [100%]
2 passed in 16.24s
```

## CI fallout

Nine branch-new failures on PR #590 (`120f993d`), classified per
`docs/internal/ORCHESTRATION.md:201` §4: **(a)** the test asserts the OLD
posture, so the test moves to the new law with the still-valid states
pinned explicitly; **(b)** a REAL regression the change exposed, fixed in
code and said loudly; **(c)** unrelated flake, proven serial-green twice.

**Result: eight (a), one (b) in user-facing prose, zero (c), zero real code
regressions.** No guard, census or fence was weakened anywhere; every (a)
edit ADDED a pin rather than removing one.

| # | Test | Class | Why | Change |
|---|---|---|---|---|
| 1 | `tests/integration/test_web_history_import_ui.py::test_history_has_audio_and_transcript_import` | **(a)** — story **10** | It pinned `started_at_ms` and `lastModified` in the import door. HS-201-10 deliberately removed exactly that (rehearsal defect 10: a WAV copied in June landed the meeting under JUN 03). | The door's four real fields (`file`, `title`, `speaker`, `tags`) are now pinned, and BOTH removed fields are pinned as ABSENT from every `body.append(` line, so the mtime cannot come back in silence. |
| 2 | `tests/unit/test_api_surface.py::test_committed_openapi_matches_reference_app` | **(a)** | `docs/generated/openapi.json` is a pin of the old route set. `/api/concierge/summary-selection` is a real route (lane A's story 06 seam, now the face's own path in 09). | Regenerated with the documented regenerator, never hand-edited: `HOME=$(mktemp -d) uv run python scripts/philo_openapi_reference.py` → `OpenAPI: 569 paths`; the diff is the one new path, +22 lines. |
| 3 | `tests/unit/test_doc_drift_guard.py::test_no_user_facing_doc_leaks_roadmap_vocabulary` | **(b)** — story **10** | **A real defect in what a USER reads.** Story 10's doc edits put `HS-201-10` into `docs/MEETING_ARCHITECTURE.md:71,73` and `docs/MEETING_INTELLIGENCE.md:54`. The guard is right; the prose was wrong. | Reworded in product-tense ("An import asks for no summary.", "It enqueues nothing;", "an import runs no summary of its own"). The guard is untouched. |
| 4 | `tests/unit/test_doc_drift_guard.py::test_no_user_facing_doc_uses_dashes_in_prose` | **(b)** — story **10** | Same edit, same line: an em dash in user-facing prose against the ratified voice rules. | The dash became a period in the same rewording. The guard is untouched. |
| 5 | `tests/unit/test_phase143_inference_capability_census.py::test_phase143_call_site_fixture_is_complete_and_fail_closed` | **(a)** — story **10** | Line-number pin drift only: `holdspeak/meeting_import.py:313 → :329`. Same function (`_transcribe_import_windows`), same capability (`transcribe`), same kind (`call`) — story 10 moved code above it. | Both pins moved to `:329`. Nothing was added to or removed from the census. |
| 6 | `tests/unit/test_phase143_inference_capability_census.py::test_phase143_every_censused_site_has_one_capability_and_source_owner` | **(a)** — story **10** | The same one pin, read by the second assertion. | Covered by the same move. |
| 7 | `tests/unit/test_phase143_routing_authority_census.py::test_ast_census_is_exact_for_every_routing_resolver_reference_and_pointer` | **(a)** | Line-number pin drift: `holdspeak/setup_runtime.py:198 → :224`, because 09 inserted `unreachable_reason` above `discover_endpoint_models`. Same pointer, same file. | The pin moved to `:224`. |
| 8 | `tests/unit/test_phase143_surface_fallback_census.py::test_web_route_pointer_controls_are_classified_and_single_owned` | **(a)** — the census doing its job | Two 09 web files now carry a profile pointer and were unregistered: `endpointDraft.ts` (new) and `useConciergeController.ts`. | Registered with one owner each, the way `summaryRoute.ts` was registered in 04, with a reasoned row in the reviewed artifact (`pm/roadmap/holdspeak/phase-143-intelligence-router/assets/generated-surface-fallback-census.md`): `endpointDraft.ts` = **display-transport** (it mints a `profile_id` for the Model Library `define-endpoint` command, which snapshots assignment heads on both sides and can never change an assignment); `useConciergeController.ts` = **inference-route** (it sends the owner's explicit summary selection and the per-group apply rows; the hub's assignment authority stays the only writer). |
| 9 | `tests/unit/test_phase200_readiness.py::test_a_blocking_compatibility_issue_is_tool_incompatible_with_the_picker_verb` | **(a)** | The verb survived: `Choose` / `engine_picker` / `["agents_tools"]` are all still asserted and all still true. Only `detail` changed, from the raw issue code to a plain line, which is 09's whole point (rehearsal defect 7). | The assertion now reads the mapping by name (`cs._INCOMPATIBILITY_REASONS["capability_class_unsupported"]`) AND its literal text. **A lying fixture was fixed at the same time:** the test minted `capability_tools_unsupported`, a code nothing in `holdspeak/` ever emits; it now mints `capability_class_unsupported`, which `inference_assignment_service.py:1881` really returns. A new case (`test_an_unknown_blocking_code_still_says_something_a_person_can_read`) pins the fail-closed path so an unmapped future code is never shown raw. |

### Green

All nine, in one run, isolated HOME:

```text
........................................................................ [ 93%]
.....                                                                    [100%]
77 passed in 31.59s
```

Story 09's own suites, after these edits:

```text
TYPECHECK CLEAN
      Tests  58 passed (58)      web/src/features/concierge
2 passed in 16.24s               tests/e2e/test_hs201_09_connect_engine_glass.py (real LAN engine)
```

### Not covered here

The full suite was not run (this lane's rule). Items 1, 3, 4, 5 and 6 are
fallout from **story 10**, fixed here because the CI list came to this
lane; items 2, 7, 8 and 9 are 09's own. Nothing was classified **(c)**, so
no serial-green-twice proof was owed.
