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

## Round two — the Astra-role check on built (`checks/story-04-built-astra-role-r1.md`, RATIFY-WITH-CONDITIONS)

- **C1 paid:** the held-prop negative control (`philo605DecisionBodyDiagnosis.test.tsx`) now proves the read view is showing after Done (`.desk-decision-editor` is null) and that the card does not carry "Keep the local ledger", then that the Decision section is absent. The mutant (drop `setEditingDecision(false)` from `commitDecisionEdit`, so Done never leaves the editor) now FAILS the control: `AssertionError: expected <div class="desk-decision-editor">…(3)</div> to be null` (capture 16:27:31Z). The last line of that capture, `mv: rename … No such file or directory`, is the capture script's restore step running from the wrong directory; the file was restored by hand right after (no diff against HEAD for `DecisionPullout.tsx`).
- **F3 paid:** the `[undefined, decisionSection()]` placeholders are gone; the tests call `decisionSection()` directly.
- **F4 paid:** the `surface.css` comment quotes the real selector, `.desk-next .desk-pullout-body section:not(:first-child)` (`window-chrome.css:202`).
- **F2:** the headings' size is unchanged (10 px on both builds; `.desk-next .desk-pullout-body h3` wins). Nothing in this tree says otherwise.
- **MISSED:** BACKLOG table "PHILO-8-04 follow-ups" (the Follow-through lanes' doubled hairline; computed only; home: the next surface pass).
- **Merged `origin/main`** (#670, the evidence scratch guard); the guard is green on the branch now (97 passed with the CSS/atlas guards, 16:28:31Z).
- **Re-run:** vitest 3 files, 15/15, no Errors line (16:27:48Z); glass 2 passed at 1440 and 393 (16:27:52Z); every `docs/generated` `--check` ok.

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

### Captured run — 2026-09-26T16:27:31Z

- **Command:** `sh /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/fd5ad72b-2ed6-4ad6-b127-8b5e72ca6caa/scratchpad/mutant.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5d730e4b281400c205373910d661d236439f3338

```text
     × negative control: a held pullout prop stays stale after the store write 198ms
⎯⎯⎯⎯⎯⎯⎯ Failed Tests 1 ⎯⎯⎯⎯⎯⎯⎯
AssertionError: expected <div class="desk-decision-editor">…(3)</div> to be null
      Tests  1 failed | 6 skipped (7)
mv: rename web/src/desk/pullouts/DecisionPullout.tsx.orig to web/src/desk/pullouts/DecisionPullout.tsx: No such file or directory
```

### Captured run — 2026-09-26T16:27:48Z

- **Command:** `sh -c cd web && npx vitest run src/desk/__tests__/philo301DecisionFace.test.tsx src/desk/__tests__/philo605DecisionBodyDiagnosis.test.tsx src/desk/__tests__/philo301DecisionNoLoss.test.tsx`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5d730e4b281400c205373910d661d236439f3338

```text

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-8-04/web


 Test Files  3 passed (3)
      Tests  15 passed (15)
   Start at  10:27:49
   Duration  2.50s (transform 2.00s, setup 275ms, import 2.86s, tests 850ms, environment 832ms)
```

### Captured run — 2026-09-26T16:27:52Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.IBpTGtG2hA PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q -p no:cacheprovider tests/e2e/test_philo8_04_empty_decision_heads_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5d730e4b281400c205373910d661d236439f3338

```text
..                                                                       [100%]
2 passed in 37.16s
```

### Captured run — 2026-09-26T16:28:31Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.fT3tDJCWJx uv run pytest -q -p no:cacheprovider -n 8 tests/unit/test_evidence_scratch_guard.py tests/unit/test_design_system_guard.py tests/unit/test_interior_canon_guard.py tests/unit/test_philo_graph_atlas.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5d730e4b281400c205373910d661d236439f3338

```text
bringing up nodes...
bringing up nodes...

........................................................................ [ 74%]
.........................                                                [100%]
=============================== warnings summary ===============================
tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
  tests/e2e/test_hs202_05_first_use_type_floor.py:260: SyntaxWarning: "\s" is an invalid escape sequence. Such sequences will not work in the future. Did you mean "\\s"? A raw string is also an option.
    ? '.' + el.className.trim().split(/\s+/)

tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
  tests/e2e/test_hs202_05_first_use_type_floor.py:439: SyntaxWarning: "\(" is an invalid escape sequence. Such sequences will not work in the future. Did you mean "\\("? A raw string is also an option.
    const m = /rgba?\(([^)]+)\)/.exec(s || '');

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
97 passed, 2 warnings in 3.14s
```
