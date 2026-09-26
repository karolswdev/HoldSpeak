# Evidence - PHILO-8-04

- **Story:** PHILO-8-04 - The two small face notes (OPTIONAL)
- **Status:** done
- **Date:** 2026-09-26

## Summary

- **Scope:** part (a) only; part (b) dropped by the owner at ratification (2026-09-26).
- **Change:** `web/src/desk/pullouts/DecisionPullout.tsx` (the read view: a `SurfaceSection` per field, drawn only when the field has text); `web/src/desk/surface/surface.css` (in the decision window a section head draws no second hairline; the rule is scoped to `.desk-decision-card`).
- **Red on main:** the first captured run below (exit 1): "title-only at 1440: headings ['Decision context', 'Decision', 'Consequences'], want []", the same at 393.
- **Green:** the glass at 1440 and 393 (2 passed, shots written); vitest 15/15 (the three new cases: two red on main, verified by running them against `git show HEAD:` of the pullout); guards 207 passed; every generated-docs `--check` ok; web baseline zero branch-new (2876 passed).
- **Re-run after scoping the CSS rule to `.desk-decision-card`:** the glass again (2 passed, 16:10:54Z; the shots in the tree are from this run) and the CSS/atlas guards (105 passed, 16:11:27Z).
- **Shots:** `assets/story-04-shots/` — `title-only-{1440,393}.png` (no heading), `title-only-edit-{1440,393}.png` (the three fields), `context-only-{1440,393}.png` (only "Decision context"), `context-and-decision-{1440,393}.png` (the Phase 7 story 04 case: both headings, no "Consequences").
- **Known, not mine:** `tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence` fails on this branch on `tests/unit/test_philo7_file_and_find.py:26`, a file this story does not touch (main's state); not in the guard run below.

## Proof

### Captured run — 2026-09-26T16:00:28Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.8LJ16QrMEW PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q -p no:cacheprovider tests/e2e/test_philo8_04_empty_decision_heads_glass.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** c98dff8d1f5c1da7d93e530e580789a9ef54bf5b

```text
FF                                                                       [100%]
=================================== FAILURES ===================================
_ TestEmptyDecisionHeadsGlass.test_a_heading_shows_only_with_text_under_it[1440] _

self = <tests.e2e.test_philo8_04_empty_decision_heads_glass.TestEmptyDecisionHeadsGlass object at 0x10aaea350>
width = 1440

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_a_heading_shows_only_with_text_under_it(self, width: int) -> None:
        from playwright.sync_api import sync_playwright
    
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": width, "height": 900})
                errors: list[str] = []
                page.on("pageerror", lambda err: errors.append(str(err)))
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                ids = {}
                for slug, title, fields, _ in CASES:
                    created = _api(page, "POST", "/api/decisions",
                                   {"title": title, "status": "proposed", **fields}, token=TOKEN)
                    ids[slug] = created["decision"]["id"]
    
                for slug, title, _fields, want in CASES:
                    page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                    _normal_chair(page)
                    region = _open_decision(page, title, ids[slug])
                    card = region.locator(".desk-decision-card")
                    _settle(page)
                    heads = [h for h in card.evaluate(_HEADS_JS) if h in HEADS]
                    page.screenshot(path=str(SHOTS / f"{slug}-{width}.png"))
>                   assert tuple(heads) == want, f"{slug} at {width}: headings {heads}, want {list(want)}"
E                   AssertionError: title-only at 1440: headings ['Decision context', 'Decision', 'Consequences'], want []
E                   assert ('Decision co...Consequences') == ()
E                     
E                     Left contains 3 more items, first extra item: 'Decision context'
E                     Use -v to get more diff

tests/e2e/test_philo8_04_empty_decision_heads_glass.py:106: AssertionError
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestEmptyDecisionHeadsGlass.test_a_heading_shows_only_with_text_under_it[393] _

self = <tests.e2e.test_philo8_04_empty_decision_heads_glass.TestEmptyDecisionHeadsGlass object at 0x10adcbc50>
width = 393

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_a_heading_shows_only_with_text_under_it(self, width: int) -> None:
        from playwright.sync_api import sync_playwright
    
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": width, "height": 900})
                errors: list[str] = []
                page.on("pageerror", lambda err: errors.append(str(err)))
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                ids = {}
                for slug, title, fields, _ in CASES:
                    created = _api(page, "POST", "/api/decisions",
                                   {"title": title, "status": "proposed", **fields}, token=TOKEN)
                    ids[slug] = created["decision"]["id"]
    
                for slug, title, _fields, want in CASES:
                    page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                    _normal_chair(page)
                    region = _open_decision(page, title, ids[slug])
                    card = region.locator(".desk-decision-card")
                    _settle(page)
                    heads = [h for h in card.evaluate(_HEADS_JS) if h in HEADS]
                    page.screenshot(path=str(SHOTS / f"{slug}-{width}.png"))
>                   assert tuple(heads) == want, f"{slug} at {width}: headings {heads}, want {list(want)}"
E                   AssertionError: title-only at 393: headings ['Decision context', 'Decision', 'Consequences'], want []
E                   assert ('Decision co...Consequences') == ()
E                     
E                     Left contains 3 more items, first extra item: 'Decision context'
E                     Use -v to get more diff

tests/e2e/test_philo8_04_empty_decision_heads_glass.py:106: AssertionError
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
=========================== short test summary info ============================
FAILED tests/e2e/test_philo8_04_empty_decision_heads_glass.py::TestEmptyDecisionHeadsGlass::test_a_heading_shows_only_with_text_under_it[1440]
FAILED tests/e2e/test_philo8_04_empty_decision_heads_glass.py::TestEmptyDecisionHeadsGlass::test_a_heading_shows_only_with_text_under_it[393]
2 failed in 12.89s
```

### Captured run — 2026-09-26T16:06:44Z

- **Command:** `env HOLDSPEAK_EVIDENCE_WRITE=1 HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.UL8ALNTyHm PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q -p no:cacheprovider tests/e2e/test_philo8_04_empty_decision_heads_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7855181ac797d8b56daab4fb4e15f41e0e4f576e

```text
..                                                                       [100%]
2 passed in 76.93s (0:01:16)
```

### Captured run — 2026-09-26T16:08:18Z

- **Command:** `sh -c cd web && npx vitest run src/desk/__tests__/philo301DecisionFace.test.tsx src/desk/__tests__/philo605DecisionBodyDiagnosis.test.tsx src/desk/__tests__/philo301DecisionNoLoss.test.tsx`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7855181ac797d8b56daab4fb4e15f41e0e4f576e

```text

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-8-04/web


 Test Files  3 passed (3)
      Tests  15 passed (15)
   Start at  10:08:19
   Duration  2.40s (transform 1.79s, setup 330ms, import 2.63s, tests 869ms, environment 969ms)
```

### Captured run — 2026-09-26T16:08:22Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.zfLt0EoNij uv run pytest -q -p no:cacheprovider -n 8 tests/unit/test_api_surface.py tests/unit/test_design_system_guard.py tests/unit/test_doc_drift_guard.py tests/unit/test_docs_navigation.py tests/unit/test_frontend_density_guard.py tests/unit/test_interior_canon_guard.py tests/unit/test_philo_census.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo_graph_reference.py tests/unit/test_philo_graph_schema.py tests/unit/test_web_vocabulary_guard.py tests/unit/test_web_null_read_guard.py tests/unit/test_phase200_canon_guard.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7855181ac797d8b56daab4fb4e15f41e0e4f576e

```text
bringing up nodes...
bringing up nodes...

........................................................................ [ 34%]
........................................................................ [ 69%]
...............................................................          [100%]
207 passed in 6.40s
```

### Captured run — 2026-09-26T16:08:29Z

- **Command:** `sh -c for s in check_doc_coverage gen_operations_json generate_capability_docs philo_openapi_reference philo_config_reference philo_boundary_census philo_api_reference philo_doctor_reference philo_graph_reference philo_repository_census; do printf "%s: " $s; HOME=$(mktemp -d) uv run python scripts/$s.py --check >/dev/null 2>&1 && echo ok || { echo DRIFT; exit 1; }; done`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7855181ac797d8b56daab4fb4e15f41e0e4f576e

```text
check_doc_coverage: ok
gen_operations_json: ok
generate_capability_docs: ok
philo_openapi_reference: ok
philo_config_reference: ok
philo_boundary_census: ok
philo_api_reference: ok
philo_doctor_reference: ok
philo_graph_reference: ok
philo_repository_census: ok
```

### Captured run — 2026-09-26T16:08:56Z

- **Command:** `uv run python scripts/check_web_baseline.py --run`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7855181ac797d8b56daab4fb4e15f41e0e4f576e

```text
Running vitest...

=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 2876 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```

### Captured run — 2026-09-26T16:10:54Z

- **Command:** `env HOLDSPEAK_EVIDENCE_WRITE=1 HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.vqDX4QzBt0 PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q -p no:cacheprovider tests/e2e/test_philo8_04_empty_decision_heads_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e09599c65ee88a44d2f2585fb4e3ad9579e30ffe

```text
..                                                                       [100%]
2 passed in 25.30s
```

### Captured run — 2026-09-26T16:11:27Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.yJZs3D48AW uv run pytest -q -p no:cacheprovider -n 8 tests/unit/test_design_system_guard.py tests/unit/test_frontend_density_guard.py tests/unit/test_interior_canon_guard.py tests/unit/test_philo_graph_atlas.py tests/unit/test_web_vocabulary_guard.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e09599c65ee88a44d2f2585fb4e3ad9579e30ffe

```text
bringing up nodes...
bringing up nodes...

........................................................................ [ 68%]
.................................                                        [100%]
105 passed in 2.90s
```
