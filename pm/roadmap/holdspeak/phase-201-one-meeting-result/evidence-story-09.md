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
