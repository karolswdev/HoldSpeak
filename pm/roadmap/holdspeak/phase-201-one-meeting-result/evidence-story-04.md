# Evidence - HS-201-04

- **Story:** HS-201-04 - Ask for the summary and find it again
- **Status:** done
- **Date:** 2026-09-19

## Proof

### Captured run — 2026-09-20T01:36:03Z

- **Command:** `bash -c cd web && npx vitest run src/meetings/__tests__/summaryRun.test.tsx src/desk/chair/arrivalSummaryRun.test.tsx src/meetings/MeetingIntelRecovery.test.tsx src/pages/cores/history/__tests__/catalogRailOriginLine.test.tsx`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a2be5e841891311e731399faec51b185ee44a9eb

```text

 RUN  v4.1.9 /Users/karol/dev/tools/wt-201-b/web


 Test Files  4 passed (4)
      Tests  24 passed (24)
   Start at  19:36:03
   Duration  1.13s (transform 961ms, setup 399ms, import 1.64s, tests 480ms, environment 1.35s)
```

### Captured run — 2026-09-20T01:36:09Z

- **Command:** `bash -c cd web && npx tsc --noEmit`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a2be5e841891311e731399faec51b185ee44a9eb

```text
(no output)
```

### Captured run — 2026-09-20T01:36:19Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.HvKGqxpxl4 PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q -s tests/e2e/test_hs201_summary_face_glass.py tests/e2e/test_hs201_summary_producer_chain.py tests/unit/test_hs201_summary_producer.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a2be5e841891311e731399faec51b185ee44a9eb

```text
RECORDED meeting=b0bc2563 segments=1
PLANNED host=same_device hash=sha256:61bf22f99653f8aa63f254ee12fab4cc324cd823438d8022ab120b2231e8de1e
ROW b0bc2563 MeetingSEP 19 · OFFSEP 19·3 WORDS·OFFTHIS DEVICERun intelligence
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-04-shots/record-before-run-1440.png
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-04-shots/record-before-run-393.png
RUN POST {'path': '/api/meetings/b0bc2563/intelligence/run', 'body': '{"expected_selection_hash":"sha256:61bf22f99653f8aa63f254ee12fab4cc324cd823438d8022ab120b2231e8de1e"}'}
RECEIPT {'attempts': [{'host': 'same_device', 'leg_ordinal': 1, 'operation_id': 'op_7d3ea51d5cad4f498407d47aa56a3cc7', 'outcome': 'succeeded'}], 'job_id': 'ij_c6ee9de7b2f8b53ede85271eb1749922ef405961a110d671161f71c23932a291', 'meeting_id': 'b0bc2563', 'outcome': 'succeeded', 'receipt_id': 'rr_eab28d7c3944cad44817bb2e0f731111', 'selection_hash': 'sha256:61bf22f99653f8aa63f254ee12fab4cc324cd823438d8022ab120b2231e8de1e'}
ROW b0bc2563 MeetingSEP 19 · RANSEP 19·3 WORDS·RANTHIS DEVICEOpen
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-04-shots/record-after-run-1440.png
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-04-shots/record-after-run-393.png
FAILED job attempts=1 state=failed
ROW dfc6544b MeetingSEP 19 · FAILEDSEP 19·3 WORDS·FAILEDTHIS DEVICEFAILEDTHIS DEVICERetry
FACTS width=243 of row=366
REFUSAL REFUSED · The summary route changed. Check it, then try again.
RECEIPT AFTER REFUSAL outcome=refused attempts=[]
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-04-shots/refusal-stale-hash-1440.png
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-04-shots/refusal-stale-hash-393.png
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-04-shots/ledger-retry-1440.png
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-04-shots/ledger-retry-393.png
RETRY POST {'path': '/api/meetings/dfc6544b/intelligence/run', 'body': '{"expected_selection_hash":"sha256:151329838eb9a278d91cb20c8ebd46254581eb57ffa64fe19a378c578face2f9"}'}
FOOTER CHIP 'THIS DEVICE'
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-04-shots/meetings-chip-1440.png
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-04-shots/meetings-chip-393.png
FOUND AFTER RESTART moves=1
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-04-shots/after-restart-1440.png
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-04-shots/after-restart-393.png
........
8 passed in 19.52s
```

### Captured run — 2026-09-20T01:40:14Z

- **Command:** `bash -c cd web && npx vitest run src/meetings/__tests__/summaryRun.test.tsx src/desk/chair/arrivalSummaryRun.test.tsx src/meetings/MeetingIntelRecovery.test.tsx src/pages/cores/history/__tests__/catalogRailOriginLine.test.tsx`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a2be5e841891311e731399faec51b185ee44a9eb

```text

 RUN  v4.1.9 /Users/karol/dev/tools/wt-201-b/web


 Test Files  4 passed (4)
      Tests  24 passed (24)
   Start at  19:40:15
   Duration  936ms (transform 983ms, setup 283ms, import 1.54s, tests 489ms, environment 821ms)
```

### Captured run — 2026-09-20T01:40:16Z

- **Command:** `bash -c cd web && npx tsc --noEmit`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a2be5e841891311e731399faec51b185ee44a9eb

```text
(no output)
```

### Captured run — 2026-09-20T01:40:29Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.67hJeYbvBT PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q -s tests/e2e/test_hs201_summary_face_glass.py tests/e2e/test_hs201_summary_producer_chain.py tests/unit/test_hs201_summary_producer.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a2be5e841891311e731399faec51b185ee44a9eb

```text
RECORDED meeting=91ac735f segments=1
PLANNED host=same_device hash=sha256:a6eac7b17e70d7688229dcbbca4b0e902a3484e50a262e5f5de2bf49feb42614
ROW 91ac735f MeetingSEP 19 · OFFSEP 19·3 WORDS·OFFTHIS DEVICERun intelligence
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-04-shots/record-before-run-1440.png
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-04-shots/record-before-run-393.png
RUN POST {'path': '/api/meetings/91ac735f/intelligence/run', 'body': '{"expected_selection_hash":"sha256:a6eac7b17e70d7688229dcbbca4b0e902a3484e50a262e5f5de2bf49feb42614"}'}
RECEIPT {'attempts': [{'host': 'same_device', 'leg_ordinal': 1, 'operation_id': 'op_c5e6ffb32a994ac796627927ca0357c3', 'outcome': 'succeeded'}], 'job_id': 'ij_23a6099d72e88d82c4751df197eaf00880ede8ce2864fb16cffa2de92b3111d2', 'meeting_id': '91ac735f', 'outcome': 'succeeded', 'receipt_id': 'rr_97cf422d7562099147addf531608894b', 'selection_hash': 'sha256:a6eac7b17e70d7688229dcbbca4b0e902a3484e50a262e5f5de2bf49feb42614'}
ROW 91ac735f MeetingSEP 19 · RANSEP 19·3 WORDS·RANTHIS DEVICEOpen
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-04-shots/record-after-run-1440.png
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-04-shots/record-after-run-393.png
FAILED job attempts=1 state=failed
ROW 07d94015 MeetingSEP 19 · FAILEDSEP 19·3 WORDS·FAILEDTHIS DEVICEFAILEDTHIS DEVICERetry
FACTS width=243 of row=366
REFUSAL REFUSED · The summary route changed. Check it, then try again.
RECEIPT AFTER REFUSAL outcome=refused attempts=[]
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-04-shots/refusal-stale-hash-1440.png
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-04-shots/refusal-stale-hash-393.png
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-04-shots/ledger-retry-1440.png
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-04-shots/ledger-retry-393.png
RETRY POST {'path': '/api/meetings/07d94015/intelligence/run', 'body': '{"expected_selection_hash":"sha256:e9c45aee18f55fe8abf1fb745f320abd1fb42f5dcee0ffae901921326b7c4374"}'}
FOOTER CHIP 'THIS DEVICE'
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-04-shots/meetings-chip-1440.png
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-04-shots/meetings-chip-393.png
FOUND AFTER RESTART moves=1
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-04-shots/after-restart-1440.png
SHOT /Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-04-shots/after-restart-393.png
........
8 passed in 19.63s
```

## Red first — every face fence proven against the PRE-CHANGE components

Method (no `git stash`; the tree is shared with sibling lanes): each
component under test was written out beside itself at its HEAD revision —
`git show HEAD:<path> > <path>.baseline.tsx` — so every relative import
resolves identically, and the two fence files were copied with their
imports re-pointed at those baselines. The baselines and the red copies
were deleted after the run; nothing of them is staged.

Baselines used: `web/src/meetings/MeetingIntelRecovery.tsx`,
`web/src/pages/cores/history/CatalogRail.tsx`,
`web/src/pages/cores/history/NeedsYouTable.tsx`,
`web/src/desk/chair/ChairHome.tsx` (all at HEAD `f7aac8bf`).

```text
     × sends the disclosed selection hash, and shows the host first 24ms
     × withholds Run and says the reason when no route resolves 1008ms
     × shows a 409 as a refusal with its plain reason 1017ms
     × opens the meeting with the `meeting:<id>` grammar History parses 107ms
     × sends the disclosed selection hash with the run 1102ms
     × discloses the route before the click and the attempts after the run 15ms
     × shows a 409 as a refusal and keeps the earlier receipt 1016ms
     × withholds Retry and says why when no route resolves 1004ms
     × dispatches the run (the audit measured zero requests) 15ms
     × discloses the route beside the verb before the click 3ms
     × withholds the verb when no route resolves 2ms
     × shows the destinations contacted after the run 1ms
     × discloses the route and withholds Run when none resolves 1ms
⎯⎯⎯⎯⎯⎯ Failed Tests 13 ⎯⎯⎯⎯⎯⎯⎯
 Test Files  2 failed (2)
      Tests  13 failed | 5 passed (18)
```

The five that passed are the new pure components (`RouteDisclosure`,
`RunAttempts`, `MeetingSummarySlab`), which have no pre-change form.

The e2e (`tests/e2e/test_hs201_summary_face_glass.py`) was NOT run red as a
whole: a red run needs the web bundle rebuilt from baseline sources, which
would leave a stale bundle for the sibling lanes. Every behavior it asserts
was proven red at the unit level above.

## Shots — 1440 and 393, `assets/story-04-shots/`

| Shot | What it proves |
|---|---|
| `record-before-run` | the planned host beside the verb, BEFORE the click |
| `record-after-run` | the summary text, its topics, and the hosts contacted |
| `refusal-stale-hash` | a stale selection refused, with its plain reason |
| `ledger-retry` | the FAILED row's Retry with its route chip |
| `meetings-chip` | the Meetings footer chip reading the real route |
| `after-restart` | the summary found after a real hub restart, in ONE move |

## Two defects the shots caught that no unit test could

1. The summary slab's fact line ran UNDER the Retry/Skip verbs at 1440:
   `.gadget-row-label` is a column flex box that does not stretch its
   child, so the facts kept their max-content width. Fixed in
   `surface.css` (the label cell stretches; the facts wrap), and the e2e's
   `_assert_no_overlap` now covers the fact line, not only error surfaces.
2. The refusal token ran out of the window's right edge (token chips are
   `nowrap` by species). Fixed with `.summary-refusal`, and the same fence
   now asserts that nothing crosses its own window's right edge
   (UX-CANON A.6).

## Observed gap in lane A's backend (recorded, not worked around)

`record_route_refusal` REPLACES the durable run receipt with a refusal
receipt carrying `attempts: []`, so after a refusal the hub can no longer
say which destinations the previous run contacted:

```text
RECEIPT AFTER REFUSAL outcome=refused attempts=[]
```

The face keeps whichever receipt it still holds (`pickRunReceipt` prefers
a receipt that actually contacted something over a bare refusal receipt),
but it cannot recover what the hub overwrote. A refusal on one meeting
does NOT touch another meeting's receipt — the rig asserts that the first
meeting's successful receipt is byte-identical after the second meeting's
refusal.

### Captured run — 2026-09-20T01:41:56Z

- **Command:** `bash -c cd web && npx vitest run src/meetings/__tests__/summaryRun.test.tsx src/desk/chair/arrivalSummaryRun.test.tsx src/meetings/MeetingIntelRecovery.test.tsx src/pages/cores/history/__tests__/catalogRailOriginLine.test.tsx && npx tsc --noEmit`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a2be5e841891311e731399faec51b185ee44a9eb

```text

 RUN  v4.1.9 /Users/karol/dev/tools/wt-201-b/web


 Test Files  4 passed (4)
      Tests  24 passed (24)
   Start at  19:41:57
   Duration  920ms (transform 964ms, setup 267ms, import 1.52s, tests 486ms, environment 842ms)
```

### Captured run — 2026-09-20T01:42:06Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.3VdqhVHOCt PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q tests/e2e/test_hs201_summary_face_glass.py tests/e2e/test_hs201_summary_producer_chain.py tests/unit/test_hs201_summary_producer.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a2be5e841891311e731399faec51b185ee44a9eb

```text
........                                                                 [100%]
8 passed in 24.46s
```

### Captured run — 2026-09-20T01:53:55Z

- **Command:** `bash -c cd web && npx vitest run src/meetings/__tests__/summaryRun.test.tsx src/desk/chair/arrivalSummaryRun.test.tsx src/lib/productLanguage.test.ts src/pages/cores/historyHeadline.test.ts src/pages/cores/history/__tests__/ src/meetings/MeetingIntelRecovery.test.tsx && npx tsc --noEmit`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a2be5e841891311e731399faec51b185ee44a9eb

```text

 RUN  v4.1.9 /Users/karol/dev/tools/wt-201-b/web


 Test Files  10 passed (10)
      Tests  53 passed (53)
   Start at  19:53:55
   Duration  2.49s (transform 4.01s, setup 2.16s, import 7.04s, tests 1.45s, environment 6.37s)
```

### Captured run — 2026-09-20T01:54:11Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.CnpRupv4AS PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q tests/e2e/test_hs170_meetings_glass.py tests/e2e/test_hs170_arrival_glass.py tests/unit/test_product_copy.py tests/unit/test_product_language.py tests/unit/test_phase200_doc_claims.py tests/unit/test_ux_canon_scan.py tests/unit/test_hs170_faces_wire.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** a2be5e841891311e731399faec51b185ee44a9eb

```text
........................................................................ [ 72%]
...........................F                                             [100%]
=================================== FAILURES ===================================
___________ TestSettingsHub.test_hub_returns_integers_default_false ____________

self = <tests.unit.test_hs170_faces_wire.TestSettingsHub object at 0x10d10ae90>
tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-8937/test_hub_returns_integers_defa0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x1150c31c0>

    def test_hub_returns_integers_default_false(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Hub returns integer counts and defaultSet=false on empty install."""
        # Patch Config.load to return defaults + point at isolated config
        from holdspeak.config.core import Config
        from holdspeak.web.routes.system.settings import build_settings_router
        from holdspeak.web.context import WebContext
        from holdspeak.services.settings_service import SettingsService
    
        config_path = tmp_path / "config.json"
        config_path.write_text("{}")
    
        monkeypatch.setattr("holdspeak.config.core.CONFIG_FILE", config_path)
        monkeypatch.setattr("holdspeak.config.CONFIG_FILE", config_path)
    
        default_config = Config()
        monkeypatch.setattr(Config, "load", staticmethod(lambda path=None: default_config))
    
        # Mock services to return empty/default state
        class FakeModelLibrary:
            def get_library(self, principal):
                return {"summary": {"state": "empty", "label": "Add model", "ready_count": 0, "attention_count": 0}, "rows": []}
    
        class FakeAssignmentService:
            def assignment_summary(self, principal):
                return {"rows": [{"id": "global", "status": "no_assignment", "repair": "Choose default"}]}
    
        class FakeCadenceService:
            def list_loops(self, principal):
                return {"loops": []}
    
        class FakeSettingsService(SettingsService):
            def __init__(self):
                pass  # skip real init
    
        class FakeCredentialService:
            pass
    
        ctx = WebContext(get_state=lambda: {})
        ctx.settings_service = FakeSettingsService()
        ctx.model_library_service = FakeModelLibrary()
        ctx.inference_assignment_service = FakeAssignmentService()
        ctx.cadence_service = FakeCadenceService()
        ctx.credential_service = FakeCredentialService()
    
        # Patch get_database to return something with automations
        class FakeAutomations:
            def list_provider_connections(self):
                return []
    
        class FakeDB:
            automations = FakeAutomations()
    
        monkeypatch.setattr("holdspeak.web.routes.system.settings.get_database", lambda: FakeDB(), raising=False)
        # The import is inside the function, so we need to patch the right module
        import holdspeak.web.routes.system.settings as settings_mod
        original_code = settings_mod.build_settings_router.__code__
    
        app = FastAPI()
        app.include_router(build_settings_router(ctx))
    
        client = TestClient(app)
        resp = client.get("/api/settings/hub")
        assert resp.status_code == 200
        body = resp.json()
    
        # Models
        assert isinstance(body["models"]["engines"], int)
        assert body["models"]["engines"] == 0
        assert isinstance(body["models"]["groupsSet"], int)
        assert body["models"]["groupsSet"] == 0
        assert body["models"]["defaultSet"] is False
    
        # Connections
        assert isinstance(body["connections"]["connected"], int)
>       assert body["connections"]["connected"] == 0
E       assert 1 == 0

tests/unit/test_hs170_faces_wire.py:426: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_hs170_faces_wire.py::TestSettingsHub::test_hub_returns_integers_default_false
1 failed, 99 passed in 41.34s
```

### Captured run — 2026-09-20T01:55:15Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.eSZ9t0sFt7 PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q tests/e2e/test_hs170_meetings_glass.py tests/e2e/test_hs170_arrival_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a2be5e841891311e731399faec51b185ee44a9eb

```text
.......                                                                  [100%]
7 passed in 35.57s
```

### Captured run — 2026-09-20T01:55:53Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.QiFpxFTJp0 uv run pytest -q tests/unit/test_product_copy.py tests/unit/test_product_language.py tests/unit/test_phase200_doc_claims.py tests/unit/test_ux_canon_scan.py tests/unit/test_hs170_faces_wire.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a2be5e841891311e731399faec51b185ee44a9eb

```text
........................................................................ [ 77%]
.....................                                                    [100%]
93 passed in 4.71s
```

### Captured run — 2026-09-20T01:56:06Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.cvKWjAWCHL PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q tests/e2e/test_hs201_summary_face_glass.py tests/e2e/test_hs201_summary_producer_chain.py tests/unit/test_hs201_summary_producer.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a2be5e841891311e731399faec51b185ee44a9eb

```text
........                                                                 [100%]
8 passed in 20.94s
```

## Follow-on round — the three loose ends

1. **`PRODUCT_TERMS.summary`** (`web/src/lib/productLanguage.ts:16`).
   HS-201-06 added the term to `docs/product-language.json` and not to this
   table, so the registry contract test failed on the branch. Added; the
   branch-new failure is HEALED and `scripts/check_web_baseline.py --run`
   now reports **2587 passed, 0 failed, zero branch-new**.

2. **The two HS-170 rigs seeded.** `seed_meeting_engines()` now runs before
   the run-verb assertions in `tests/e2e/test_hs170_meetings_glass.py:222`
   and `tests/e2e/test_hs170_arrival_glass.py:348` (the second call site at
   `:478` was already there for the quiet-arrival rig). Both green:
   `7 passed in 37.63s`.

3. **`Run intelligence` → `Run summary`** on the whole meeting path
   (Constitution tenet 4). The verb string is also the row-state
   discriminator, so it moved together: `history/helpers.ts:236`
   (`meetingRowState().verb`), `history/CatalogRail.tsx` (all five
   comparisons), `history/NeedsYouTable.tsx:100`, `chair/ChairHome.tsx:1910`
   and its write-failure label at `:734`. The headline above the verb moved
   with it — `1 meeting needs intelligence` is now `1 meeting needs a
   summary` (`helpers.ts:211`), because one job may not have two names on
   one face. Canon docs updated: `docs/internal/POSITIONING.md:200` (the
   canonical-name row, with the old label recorded as a banned alias),
   `docs/USER_GUIDE.md` (4 places), `docs/ARCHITECTURE.md:830`.

   NOT renamed, and why: the queue's `reason="Run intelligence"` string in
   `holdspeak/services/meeting_intel_service.py:160` is a durable ledger
   reason, not a face label, and `tests/unit/test_phase200_intel_drain.py:520`
   asserts it. Historical PMO evidence and closed-phase audits keep the old
   word — they record what was true then.

### A defect the HS-170 rig caught in THIS story's work

The row's in-flight egress chip echoed the POST response's `host` straight
to the glass, so with the route projection in place it printed the wire
word `same_device` at a person, and the row carried TWO egress chips:

```text
E  strict mode violation: locator("[data-testid='meeting-row-m-off-words'] .gadget-chip-egress") resolved to 2 elements:
E      1) <span class="gadget-chip gadget-chip-egress" …>same_device</span>
E      2) <span data-scope="local" class="gadget-chip gadget-chip-egress" …>THIS DEVICE</span>
```

Fixed by deleting the echoed chip and its `runHost` state
(`HistoryCore.tsx`, `CatalogRail.tsx`): the row's own disclosed route
(`row-route`) now carries the host before, during and after the click,
through the one `egressFor` mapper. HS-170's S-3 assertion was re-pointed
at it and strengthened — it now asserts the host is disclosed BEFORE the
click as well as after.

### Shots re-taken

Every `assets/story-04-shots/` shot was re-shot after the rename; the verb
now reads `Run summary` and the Meetings headline `1 meeting needs a
summary`.

## Counsel fix round

Astra's counsel on built (`checks/story-04-built-astra.md`, DO-NOT-RATIFY)
reviewed `c31a4da0`. Every fence below was proven RED against that commit
by the same method as the first round (`git show HEAD:<path>` written
beside itself so relative imports resolve identically; baselines and red
copies deleted after the run, nothing staged).

```text
     × shows a 409 as a refusal and keeps the EXECUTED receipt 18ms
     × dispatches the run with the route it DISPLAYED 15ms
     × puts the DISPLAYED selection hash on the run request 1040ms
     × a finished meeting with no proposals reads NOT RUN, never EXTRACTED 1014ms
 Test Files  3 failed (3)
```

The deep-link red says exactly what finding 1 predicted — the request went
out with an empty hash while the chip beside the button showed a real host:

```text
-       "expected_selection_hash": "sha256:from-the-detail",
+       "expected_selection_hash": "",
```

…and with the honest fixture (the hub's bare refusal receipt from BOTH the
409 and the read after it) the pre-counsel face lost the executed run's
destinations altogether:

```text
TestingLibraryElementError: Unable to find an element by: [data-testid="recovery-attempts"]
```

### 1. Route source — the displayed route IS the request

`HistoryCore.handleRunIntelligence` now takes the route as an argument
(`HistoryCore.tsx:153`); `CatalogRail` hands it the route the ROW drew
(`CatalogRail.tsx:224`) and `MeetingDetail` the route the RECORD drew
(`MeetingDetail.tsx:83`, `:135`). The list lookup survives only as a
fallback for a caller that has none. Fence:
`web/src/pages/cores/__tests__/summaryDeepLink.test.tsx` — a meeting the
list never loaded, opened by `meeting:<id>`, asserts the hash on the wire
equals the hash of the route on the glass.

### 2. Receipt retention — the hub's job, with a one-response fallback

Lane A's `a07d4bb5` makes `run_receipt` the last EXECUTED receipt and
serves the no-call refusal separately as `last_refusal`. The face reads
both (`summaryRoute.ts:readLastRefusal`, rendered by one `RefusalToken`
species in all four faces) and keeps `executedReceipt()` — a per-meeting
memory — only for the interval between a 409 RESPONSE, whose body still
carries the bare refusal receipt, and the next read. The masking fixture is
gone: `summaryRun.test.tsx` now returns `REFUSED_RECEIPT` from the 409 AND
from the reload, and asserts the executed attempts are still on the face; a
second fence renders `run_receipt` beside `last_refusal` with no 409 held.

### 3. Review says NOT RUN, and never EXTRACTED

`extractionRan(model)` is true only when a proposal exists — the review read
model's `job` is the SUMMARY job and `extracted_at` is the SUMMARY's
completion stamp (`proposal_bridge_service.py:1046`, `:1048`), so neither
proves extraction ran (`reviewModel.ts:275`). The finished Review headline
reads `Not run` and the head token reads `PROPOSALS · NOT RUN` instead of
`EXTRACTED <time>` (`MeetingReview.tsx:362`). Fenced in vitest both ways
(with and without proposals) and on the glass: the rig now opens the Review
wing after a real run and asserts the token, the absence of `EXTRACTED` and
the absence of `Nothing to review` (`review-not-run-1440/393`).

### 4. Egress

The Chair's click receipt goes through `egressFor` like the ledger's
(`ChairHome.tsx:ReceiptChip`) — it printed the wire word `same_device` and
called every host but "local" a cloud host. The Meetings footer draws NO
chip when no route was read (`HistoryCore.tsx:250`), and the Review wing's
own footer fallback was the same claim and is gone too
(`MeetingReview.tsx:754`).

### 5. Canon — measured, not eyeballed

The rig now counts the filled primaries inside each window and looks for a
zero counter (`_assert_canon`). It caught what the shots hid:

```text
CANON primaries=['Run summary', 'Run summary'] zeros=[]
E   AssertionError: ['Run summary', 'Run summary']
```

The row's run verb steps down to the default species while its own record
is open (`CatalogRail.tsx:147`); the record keeps the filled verb because
that is where the owner is working. `Record meeting` on the Meetings head
had already dropped to default (`HistoryCore.tsx:286`) and the Chair's
`0 MIN` was already gone (`ChairHome.tsx:219` — a 30-second meeting rounded
to zero); the probe confirms both. Green at both stations:

```text
CANON primaries=['Run summary'] zeros=[]
CANON primaries=['Retry'] zeros=[]
```

The refusal is now ONE short fact line: `REFUSED · ROUTE CHANGED`, with the
hub's full sentence on the token's title (`summaryRoute.ts:refusalFact`).

### 6. The guide

`docs/USER_GUIDE.md:719` no longer promises the plugin chain: "read its
transcript and write its summary, topics and action items; it does not run
the proposal plugins."

### 7. The batch capture failure — classified (c), real cross-file pollution

Narrowed to ONE pair, reproduced and then fixed:

```text
# before
tests/e2e/test_hs170_arrival_glass.py -k needs_you_1440  +  test_hs170_faces_wire.py -k hub_returns
  →  1 failed, 1 passed        (assert 1 == 0)
# after
  →  2 passed
# the original seven-file batch
  →  100 passed in 33.66s
```

Two defects meet:

- **The leak (fixed here).** `tests/e2e/glass_infra.py:_boot` calls
  `reset_database()` on the way IN and never on the way out, so the
  singleton it creates — pointing at its own seeded tmp database — outlived
  the module. Two lines now hand `db_core._db` / `_observer` to
  `monkeypatch`, which restores the `None` they hold at that moment, so the
  next module builds its own. It belongs here: it is shared rig
  infrastructure I touched this round, every glass rig leaks the same way,
  and the fix is verified by the reproduction above.
- **The ineffective patch (LEDGERED to HS-170's owner).**
  `tests/unit/test_hs170_faces_wire.py:403` patches
  `holdspeak.web.routes.system.settings.get_database`, but the route does a
  function-local `from ....db import get_database`
  (`holdspeak/web/routes/system/settings.py:186`) and never reads that
  name. The test therefore asserts against the process-global database and
  its green in isolation is an accident. Repointing the patch — or hoisting
  the route's import — changes what that test asserts, so it is HS-170's
  call, not this story's.

### Shots re-taken (both widths)

`record-before-run`, `record-after-run`, `review-not-run` (new),
`refusal-stale-hash`, `ledger-retry`, `meetings-chip`, `after-restart`.
