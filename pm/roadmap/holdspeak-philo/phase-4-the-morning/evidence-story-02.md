# Evidence - PHILO-4-02

- **Story:** PHILO-4-02 - The new decision is in the visible rows (order + a real recency source; the cap kept)
- **Status:** done
- **Date:** 2026-09-24

## Proof

Final proof: all five story acceptance boxes have citations in
[story 02](story-02-decision-in-the-visible-rows.md). The complete
[lane report](../../../../docs/internal/philo/phase-4/rows/lane-report.md)
separates the retained reds, final greens, actual runs and remaining costs.

- Final as-written case, real LAN engine: 1440 `20260924T072614Z`,
  393 `20260924T072514Z`, both PASS. Decision first, all nine hit points
  owned; one next-day Generate; old DB rows and empty triage shelf unchanged.
- Breakage variant: 1440 `20260924T072814Z`, 393 `20260924T072722Z`,
  both PASS, same failure source under distinct brief-scoped ids.
- Scoped final tests: 92 Python, 81 ChairHome, 1 direct browser transition.
  Red tests ran against archived `origin/main` at `566495b0`.
- [Built counsel](checks/rows-built-muaddib.md): RATIFY-WITH-CONDITIONS,
  all paid; revised C2 RATIFY. Full suites belong to PR CI. No owner sitting
  or summary-usefulness claim; no merge is authorized.

### Captured run — 2026-09-24T06:36:42Z

- **Command:** `bash -c set -o pipefail; cd .tmp/philo402-main && uv run --no-sync pytest -q tests/unit/test_philo4_02_readable_rows.py 2>&1 | tee ../../docs/internal/philo/phase-4/rows/red-readable.log`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 549696da704d91e91d5f6fd0038ae74ea765caca

```text
F.....FF                                                                 [100%]
=================================== FAILURES ===================================
____ test_readable_text_uses_element_from_point_and_rejects_a_covering_dock ____

    def test_readable_text_uses_element_from_point_and_rejects_a_covering_dock():
        """A visible row is readable only when all sampled hit points are owned."""
        predicate = {"kind": "readable_text", "value": "Review decision: New"}
        uncovered = _snapshot(covered=False)
        covered = _snapshot(covered=True)
    
        ok, reading = rig.check_predicate(predicate, {}, uncovered)
>       assert ok, reading
E       AssertionError: unknown predicate kind 'readable_text'
E       assert False

tests/unit/test_philo4_02_readable_rows.py:61: AssertionError
_______ test_atlas_declares_readable_text_for_the_as_written_chain_case ________

    def test_atlas_declares_readable_text_for_the_as_written_chain_case():
        atlas = json.loads(ATLAS.read_text())
        case = next(case for case in atlas["cases"] if case["id"] == CASE_ID)
        expected = case["expected"]
    
>       assert expected["observe_at"] == "[data-testid=arrival-brief-row]"
E       AssertionError: assert '[data-testid...urface-ledger' == '[data-testid...al-brief-row]'
E         
E         - [data-testid=arrival-brief-row]
E         ?                             ---
E         + [data-testid=arrival-brief] .surface-ledger
E         ?                           ++++++++++ +++++

tests/unit/test_philo4_02_readable_rows.py:94: AssertionError
____________ test_readable_text_is_in_the_shared_schema_vocabulary _____________

    def test_readable_text_is_in_the_shared_schema_vocabulary():
        for path in (SCHEMA, GRAPH_SCHEMA):
            schema = json.loads(path.read_text())
            predicate = schema["$defs"]["case"]["properties"]["expected"]["properties"]["predicate"]
>           assert "readable_text" in predicate["properties"]["kind"]["enum"], path
E           AssertionError: PosixPath('/Users/karol/dev/tools/wt-philo-4-02/.tmp/philo402-main/docs/internal/philo/graph/atlas.schema.json')
E           assert 'readable_text' in ['attr_equals', 'input_value', 'presentation_change', 'protocol_field', 'protocol_rows', 'protocol_rows_gone', ...]

tests/unit/test_philo4_02_readable_rows.py:115: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_philo4_02_readable_rows.py::test_readable_text_uses_element_from_point_and_rejects_a_covering_dock
FAILED tests/unit/test_philo4_02_readable_rows.py::test_atlas_declares_readable_text_for_the_as_written_chain_case
FAILED tests/unit/test_philo4_02_readable_rows.py::test_readable_text_is_in_the_shared_schema_vocabulary
3 failed, 5 passed in 5.13s
```

### Captured run — 2026-09-24T06:42:01Z

- **Command:** `bash -c set -o pipefail; uv run --no-sync python docs/internal/philo/phase-4/rows/verify_this_week.py 2>&1 | tee docs/internal/philo/phase-4/rows/this-week.log`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 549696da704d91e91d5f6fd0038ae74ea765caca

```text
{
  "decision_id": "dec-cb7f735b7f4fb465996e",
  "commitment_id": "commitment-372827a350fe47e8a46ef11121d0730b",
  "days": [
    {
      "producer_day": "2026-09-23T17:40:00",
      "brief_id": "brief-48585f91336141a394dc702defd8f5b5",
      "this_week": {
        "text": "1 commitment due this week",
        "detail": "Send the Q4 plan to Dana | 2026-09-25"
      },
      "decisions": [],
      "without_this_week_exclusion": [
        "Commitment due 2026-09-25: Send the Q4 plan to Dana"
      ]
    },
    {
      "producer_day": "2026-09-24T08:02:00",
      "brief_id": "brief-6b33bfd6b380405e93ae1e263bc77104",
      "this_week": {
        "text": "1 commitment due this week",
        "detail": "Send the Q4 plan to Dana | 2026-09-25"
      },
      "decisions": [],
      "without_this_week_exclusion": [
        "Commitment due 2026-09-25: Send the Q4 plan to Dana"
      ]
    }
  ],
  "verdict": "PASS: c1 belongs to THIS WEEK"
}
```

### Captured run — 2026-09-24T06:42:55Z

- **Command:** `bash -c set -o pipefail; cd .tmp/philo402-main && uv run --no-sync pytest -q tests/unit/test_philo4_02_decision_rows.py 2>&1 | tee ../../docs/internal/philo/phase-4/rows/red-producer.log`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 549696da704d91e91d5f6fd0038ae74ea765caca

```text
FF                                                                       [100%]
=================================== FAILURES ===================================
___________ test_generate_carries_created_at_on_every_decision_item ____________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-465/test_generate_carries_created_0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10c830d60>

    def test_generate_carries_created_at_on_every_decision_item(tmp_path, monkeypatch):
        db = Database(tmp_path / "brief.db")
        service = MondayBriefService(db, clock=lambda: NOW)
        _upsert_desk_decision(
            db,
            decision_id="decision-z-old",
            title="Old decision one",
            created_at="2026-08-01T08:45:00",
        )
        _upsert_desk_decision(
            db,
            decision_id="decision-a-new",
            title="Newest decision",
            created_at="2026-08-04T08:45:00",
        )
        monkeypatch.setattr(
            brief_module,
            "uuid",
            SimpleNamespace(uuid4=_fixed_uuid4("f" * 32, "0" * 32, "1" * 32)),
        )
    
        generated = service.generate(None, now=NOW)
        reloaded = service.get_latest(None)
        assert reloaded is not None
        assert generated.id == reloaded.id
>       assert [item.created_at for item in reloaded.sections["decisions"]] == [
                ^^^^^^^^^^^^^^^
            "2026-08-04T08:45:00",
            "2026-08-01T08:45:00",
        ]
E       AttributeError: 'BriefItem' object has no attribute 'created_at'

tests/unit/test_philo4_02_decision_rows.py:64: AttributeError
________ test_generate_and_reload_sorts_decisions_by_record_created_at _________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-465/test_generate_and_reload_sorts0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10db47bb0>

    def test_generate_and_reload_sorts_decisions_by_record_created_at(tmp_path, monkeypatch):
        db = Database(tmp_path / "brief.db")
        service = MondayBriefService(db, clock=lambda: NOW)
        _upsert_desk_decision(
            db,
            decision_id="decision-z-old",
            title="Old decision one",
            created_at="2026-08-01T08:45:00",
        )
        _upsert_desk_decision(
            db,
            decision_id="decision-m-old",
            title="Old decision two",
            created_at="2026-08-02T08:45:00",
        )
        _upsert_desk_decision(
            db,
            decision_id="decision-a-new",
            title="Newest decision",
            created_at="2026-08-04T08:45:00",
        )
        # The generated item ids are fixed only to make the pre-fix reload order
        # deterministic. The assertion below uses the record timestamps/text.
        monkeypatch.setattr(
            brief_module,
            "uuid",
            SimpleNamespace(uuid4=_fixed_uuid4("f" * 32, "0" * 32, "1" * 32, "2" * 32)),
        )
    
        service.generate(None, now=NOW)
        reloaded = service.get_latest(None)
        assert reloaded is not None
>       assert [item.text for item in reloaded.sections["decisions"]] == [
            "Review decision: Newest decision",
            "Review decision: Old decision two",
            "Review decision: Old decision one",
        ]
E       AssertionError: assert ['Review deci...est decision'] == ['Review deci...decision one']
E         
E         At index 0 diff: 'Review decision: Old decision one' != 'Review decision: Newest decision'
E         Use -v to get more diff

tests/unit/test_philo4_02_decision_rows.py:103: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_philo4_02_decision_rows.py::test_generate_carries_created_at_on_every_decision_item
FAILED tests/unit/test_philo4_02_decision_rows.py::test_generate_and_reload_sorts_decisions_by_record_created_at
2 failed in 0.71s
```

### Captured run — 2026-09-24T06:43:13Z

- **Command:** `bash -c set -o pipefail; cd .tmp/philo402-main/web && npx vitest run src/desk/chair/__tests__/decisionRows.philo402.test.tsx --maxWorkers=2 2>&1 | tee ../../../docs/internal/philo/phase-4/rows/red-rendered.log`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 549696da704d91e91d5f6fd0038ae74ea765caca

```text

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-4-02/.tmp/philo402-main/web

 ❯ src/desk/chair/__tests__/decisionRows.philo402.test.tsx (2 tests | 2 failed) 1052ms
     × shows the newest decision first with an honest cap and fold 26ms
     × keeps the result ordered after Generate replaces an existing brief 1025ms

⎯⎯⎯⎯⎯⎯⎯ Failed Tests 2 ⎯⎯⎯⎯⎯⎯⎯

 FAIL  src/desk/chair/__tests__/decisionRows.philo402.test.tsx > PHILO-4-02: decision rows lead the Arrival cap > shows the newest decision first with an honest cap and fold
AssertionError: expected [ …(3) ] to deeply equal [ StringContaining{…}, …(2) ]

- Expected
+ Received

  [
-   StringContaining "Review decision: Newest decision",
-   StringContaining "Review decision: Old decision one",
-   StringContaining "Review decision: Old decision two",
+   "Meeting recorded: Older meetingAckDefer",
+   "Older breakageAckDefer",
+   "Open loop: Older loopAckDefer",
  ]

 ❯ expectDecisionRows src/desk/chair/__tests__/decisionRows.philo402.test.tsx:111:46
    109|   const rows = screen.getAllByTestId("arrival-brief-row");
    110|   expect(rows).toHaveLength(3);
    111|   expect(rows.map((row) => row.textContent)).toEqual([
       |                                              ^
    112|     expect.stringContaining("Review decision: Newest decision"),
    113|     expect.stringContaining("Review decision: Old decision one"),
 ❯ src/desk/chair/__tests__/decisionRows.philo402.test.tsx:131:5

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[1/2]⎯

 FAIL  src/desk/chair/__tests__/decisionRows.philo402.test.tsx > PHILO-4-02: decision rows lead the Arrival cap > keeps the result ordered after Generate replaces an existing brief
TestingLibraryElementError: Unable to find an element with the text: Review decision: Newest decision. This could be because the text is broken up by multiple elements. In this case, you can provide a function for your text matcher to make your matcher more flexible.

Ignored nodes: comments, script, style
[36m<body>[39m
  [36m<div>[39m
    [36m<div[39m
      [33mclass[39m=[32m"chair"[39m
      [33mdata-testid[39m=[32m"chair"[39m
    [36m>[39m
      [36m<div[39m
        [33mclass[39m=[32m"arrival-headline"[39m
        [33mdata-testid[39m=[32m"arrival-headline"[39m
      [36m>[39m
        [36m<h1[39m
          [33mclass[39m=[32m"arrival-display arrival-display--muted"[39m
          [33mdata-testid[39m=[32m"arrival-display"[39m
        [36m>[39m
          [0mNothing needs you[0m
        [36m</h1>[39m
      [36m</div>[39m
      [36m<div[39m
        [33mdata-testid[39m=[32m"arrival-brief"[39m
      [36m>[39m
        [36m<section[39m
          [33mclass[39m=[32m"surface-section"[39m
        [36m>[39m
          [36m<header[39m
            [33mclass[39m=[32m"surface-section-head"[39m
          [36m>[39m
            [36m<h3>[39m
              [0mBRIEF · 7 THINGS WAITING[0m
            [36m</h3>[39m
            [36m<span[39m
              [33mclass[39m=[32m"gadget-chip gadget-chip-egress"[39m
              [33mdata-scope[39m=[32m"local"[39m
              [33mtitle[39m=[32m"The brief is built from this desk's own records."[39m
            [36m>[39m
              [0mTHIS DEVICE[0m
            [36m</span>[39m
            [36m<button[39m
              [33mclass[39m=[32m"btn btn--ghost btn--sm "[39m
              [33mdata-testid[39m=[32m"arrival-brief-generate"[39m
              [33mtype[39m=[32m"button"[39m
            [36m>[39m
              [0mGenerate[0m
            [36m</button>[39m
          [36m</header>[39m
          [36m<div[39m
            [33mclass[39m=[32m"surface-ledger"[39m
            [33mdata-cols[39m=[32m"room"[39m
          [36m>[39m
            [36m<div[39m
              [33mclass[39m=[32m"surface-ledger-head"[39m
            [36m>[39m
              [36m<span[39m
                [33mclass[39m=[32m"surface-ledger-count"[39m
              [36m/>[39m
            [36m</div>[39m
            [36m<li[39m
              [33mclass[39m=[32m"surface-ledger-row"[39m
              [33mdata-wrap[39m=[32m"true"[39m
            [36m>[39m
              [36m<div[39m
                [33mclass[39m=[32m"surface-ledger-line"[39m
                [33mdata-has-trailing[39m=[32m"true"[39m
                [33mdata-testid[39m=[32m"arrival-brief-row"[39m
                [33mrole[39m=[32m"button"[39m
                [33mtabindex[39m=[32m"0"[39m
              [36m>[39m
                [36m<span[39m
                  [33mclass[39m=[32m"surface-ledger-primary"[39m
                [36m>[39m
                  [0mMeeting recorded: Older meeting[0m
                [36m</span>[39m
                [36m<span[39m
                  [33mclass[39m=[32m"surface-ledger-trailing"[39m
                [36m>[39m
                  [36m<button[39m
                    [33mclass[39m=[32m"btn btn--ghost btn--sm "[39m
                    [33mtype[39m=[32m"button"[39m
                  [36m>[39m
                    [0mAck[0m
                  [36m</button>[39m
                  [36m<button[39m
                    [33mclass[39m=[32m"btn btn--ghost btn--sm "[39m
                    [33mtype[39m=[32m"button"[39m
                  [36m>[39m
                    [0mDefer[0m
                  [36m</button>[39m
                [36m</span>[39m
              [36m</div>[39m
            [36m</li>[39m
            [36m<li[39m
              [33mclass[39m=[32m"surface-ledger-row"[39m
              [33mdata-wrap[39m=[32m"true"[39m
            [36m>[39m
              [36m<div[39m
                [33mclass[39m=[32m"surface-ledger-line"[39m
                [33mdata-has-trailing[39m=[32m"true"[39m
                [33mdata-testid[39m=[32m"arrival-brief-row"[39m
                [33mrole[39m=[32m"button"[39m
                [33mtabindex[39m=[32m"-1"[39m
              [36m>[39m
                [36m<span[39m
                  [33mclass[39m=[32m"surface-ledger-primary"[39m
                [36m>[39m
                  [0mOlder breakage[0m
                [36m</span>[39m
                [36m<span[39m
                  [33mclass[39m=[32m"surface-ledger-trailing"[39m
                [36m>[39m
                  [36m<button[39m
                    [33mclass[39m=[32m"btn btn--ghost btn--sm "[39m
                    [33mtype[39m=[32m"button"[39m
                  [36m>[39m
                    [0mAck[0m
                  [36m</button>[39m
                  [36m<button[39m
                    [33mclass[39m=[32m"btn btn--ghost btn--sm "[39m
                    [33mtype[39m=[32m"button"[39m
                  [36m>[39m
                    [0mDefer[0m
                  [36m</button>[39m
                [36m</span>[39m
              [36m</div>[39m
            [36m</li>[39m
            [36m<li[39m
              [33mclass[39m=[32m"surface-ledger-row"[39m
              [33mdata-wrap[39m=[32m"true"[39m
            [36m>[39m
              [36m<div[39m
                [33mclass[39m=[32m"surface-ledger-line"[39m
                [33mdata-has-trailing[39m=[32m"true"[39m
                [33mdata-testid[39m=[32m"arrival-brief-row"[39m
                [33mrole[39m=[32m"button"[39m
                [33mtabindex[39m=[32m"-1"[39m
              [36m>[39m
                [36m<span[39m
                  [33mclass[39m=[32m"surface-ledger-primary"[39m
                [36m>[39m
                  [0mOpen loop: Older loop[0m
                [36m</span>[39m
                [36m<span[39m
                  [33mclass[39m=[32m"surface-ledger-trailing"[39m
                [36m>[39m
                  [36m<button[39m
                    [33mclass[39m=[32m"btn btn--ghost btn--sm "[39m
                    [33mtype[39m=[32m"button"[39m
                  [36m>[39m
                    [0mAck[0m
                  [36m</button>[39m
                  [36m<button[39m
                    [33mclass[39m=[32m"btn btn--ghost btn--sm "[39m
                    [33mtype[39m=[32m"button"[39m
                  [36m>[39m
                    [0mDefer[0m
                  [36m</button>[39m
                [36m</span>[39m
              [36m</div>[39m
            [36m</li>[39m
          [36m</div>[39m
          [36m<button[39m
            [33mclass[39m=[32m"btn btn--ghost btn--sm "[39m
            [33mdata-testid[39m=[32m"arrival-brief-more"[39m
            [33mtype[39m=[32m"button"[39m
          [36m>[39m
            [0m4[0m
            [0m more[0m
          [36m</button>[39m
        [36m</section>[39m
        [36m<span[39m
          [33mclass[39m=[32m"surface-receipt-line"[39m
          [33mdata-testid[39m=[32m"arrival-brief-date"[39m
        [36m>[39m
          [0mSEP 21 – 24 · GENERATED SEP 24 08:02[0m
        [36m</span>[39m
        [36m<span[39m
          [33mclass[39m=[32m"surface-receipt-line"[39m
          [33mdata-testid[39m=[32m"arrival-brief-receipt"[39m
          [33mrole[39m=[32m"status"[39m
        [36m>[39m
          [0mBrief ready · 7 items · 8:02 AM[0m
        [36m</span>[39m
      [36m</div>[39m
      [36m<footer[39m
        [33mclass[39m=[32m"arrival-capture-bar"[39m
        [33mdata-testid[39m=[32m"arrival-capture-bar"[39m
      [36m>[39m
        [36m<span[39m
          [33mclass[39m=[32m"arrival-capture-talk"[39m
        [36m/>[39m
        [36m<button[39m
          [33mclass[39m=[32m"btn btn--ghost "[39m
          [33mdata-testid[39m=[32m"arrival-develop-thought"[39m
          [33mtype[39m=[32m"button"[39m
        [36m>[39m
          [0mWrite a thought[0m
        [36m</button>[39m
        [36m<button[39m
          [33mclass[39m=[32m"btn btn--ghost "[39m
          [33mdata-testid[39m=[32m"arrival-record-meeting"[39m
          [33mtype[39m=[32m"button"[39m
        [36m>[39m
          [0mRecord meeting[0m
        [36m</button>[39m
        [36m<button[39m
          [33mclass[39m=[32m"btn btn--ghost "[39m
          [33mdata-testid[39m=[32m"arrival-schedule"[39m
          [33mtype[39m=[32m"button"[39m
        [36m>[39m
          [0mSchedule[0m
        [36m</button>[39m
      [36m</footer>[39m
    [36m</div>[39m
  [36m</div>[39m
[36m</body>[39m

Ignored nodes: comments, script, style
[36m<html>[39m
  [36m<head />[39m
  [36m<body>[39m
    [36m<div>[39m
      [36m<div[39m
        [33mclass[39m=[32m"chair"[39m
        [33mdata-testid[39m=[32m"chair"[39m
      [36m>[39m
        [36m<div[39m
          [33mclass[39m=[32m"arrival-headline"[39m
          [33mdata-testid[39m=[32m"arrival-headline"[39m
        [36m>[39m
          [36m<h1[39m
            [33mclass[39m=[32m"arrival-display arrival-display--muted"[39m
            [33mdata-testid[39m=[32m"arrival-display"[39m
          [36m>[39m
            [0mNothing needs you[0m
          [36m</h1>[39m
        [36m</div>[39m
        [36m<div[39m
          [33mdata-testid[39m=[32m"arrival-brief"[39m
        [36m>[39m
          [36m<section[39m
            [33mclass[39m=[32m"surface-section"[39m
          [36m>[39m
            [36m<header[39m
              [33mclass[39m=[32m"surface-section-head"[39m
            [36m>[39m
              [36m<h3>[39m
                [0mBRIEF · 7 THINGS WAITING[0m
              [36m</h3>[39m
              [36m<span[39m
                [33mclass[39m=[32m"gadget-chip gadget-chip-egress"[39m
                [33mdata-scope[39m=[32m"local"[39m
                [33mtitle[39m=[32m"The brief is built from this desk's own records."[39m
              [36m>[39m
                [0mTHIS DEVICE[0m
              [36m</span>[39m
              [36m<button[39m
                [33mclass[39m=[32m"btn btn--ghost btn--sm "[39m
                [33mdata-testid[39m=[32m"arrival-brief-generate"[39m
                [33mtype[39m=[32m"button"[39m
              [36m>[39m
                [0mGenerate[0m
              [36m</button>[39m
            [36m</header>[39m
            [36m<div[39m
              [33mclass[39m=[32m"surface-ledger"[39m
              [33mdata-cols[39m=[32m"room"[39m
            [36m>[39m
              [36m<div[39m
                [33mclass[39m=[32m"surface-ledger-head"[39m
              [36m>[39m
                [36m<span[39m
                  [33mclass[39m=[32m"surface-ledger-count"[39m
                [36m/>[39m
              [36m</div>[39m
              [36m<li[39m
                [33mclass[39m=[32m"surface-ledger-row"[39m
                [33mdata-wrap[39m=[32m"true"[39m
              [36m>[39m
                [36m<div[39m
                  [33mclass[39m=[32m"surface-ledger-line"[39m
                  [33mdata-has-trailing[39m=[32m"true"[39m
                  [33mdata-testid[39m=[32m"arrival-brief-row"[39m
                  [33mrole[39m=[32m"button"[39m
                  [33mtabindex[39m=[32m"0"[39m
                [36m>[39m
                  [36m<span[39m
                    [33mclass[39m=[32m"surface-ledger-primary"[39m
                  [36m>[39m
                    [0mMeeting recorded: Older meeting[0m
                  [36m</span>[39m
                  [36m<span[39m
                    [33mclass[39m=[32m"surface-ledger-trailing"[39m
                  [36m>[39m
                    [36m<button[39m
                      [33mclass[39m=[32m"btn btn--ghost btn--sm "[39m
                      [33mtype[39m=[32m"button"[39m
                    [36m>[39m
                      [0mAck[0m
                    [36m</button>[39m
                    [36m<button[39m
                      [33mclass[39m=[32m"btn btn--ghost btn--sm "[39m
                      [33mtype[39m=[32m"button"[39m
                    [36m>[39m
                      [0mDefer[0m
                    [36m</button>[39m
                  [36m</span>[39m
                [36m</div>[39m
              [36m</li>[39m
              [36m<li[39m
                [33mclass[39m=[32m"surface-ledger-row"[39m
                [33mdata-wrap[39m=[32m"true"[39m
              [36m>[39m
                [36m<div[39m
                  [33mclass[39m=[32m"surface-ledger-line"[39m
                  [33mdata-has-trailing[39m=[32m"true"[39m
                  [33mdata-testid[39m=[32m"arrival-brief-row"[39m
                  [33mrole[39m=[32m"button"[39m
                  [33mtabindex[39m=[32m"-1"[39m
                [36m>[39m
                  [36m<span[39m
                    [33mclass[39m=[32m"surface-ledger-primary"[39m
                  [36m>[39m
                    [0mOlder breakage[0m
                  [36m</span>[39m
                  [36m<span[39m
                    [33mclass[39m=[32m"surface-ledger-trailing"[39m
                  [36m>[39m
                    [36m<button[39m
                      [33mclass[39m=[32m"btn btn--ghost btn--sm "[39m
                      [33mtype[39m=[32m"button"[39m
                    [36m>[39m
                      [0mAck[0m
                    [36m</button>[39m
                    [36m<button[39m
                      [33mclass[39m=[32m"btn btn--ghost btn--sm "[39m
                      [33mtype[39m=[32m"button"[39m
                    [36m>[39m
                      [0mDefer[0m
                    [36m</button>[39m
                  [36m</span>[39m
                [36m</div>[39m
              [36m</li>[39m
              [36m<li[39m
                [33mclass[39m=[32m"surface-ledger-row"[39m
                [33mdata-wrap[39m=[32m"true"[39m
              [36m>[39m
                [36m<div[39m
                  [33mclass[39m=[32m"surface-ledger-line"[39m
                  [33mdata-has-trailing[39m=[32m"true"[39m
                  [33mdata-testid[39m=[32m"arrival-brief-row"[39m
                  [33mrole[39m=[32m"button"[39m
                  [33mtabindex[39m=[32m"-1"[39m
                [36m>[39m
                  [36m<span[39m
                    [33mclass[39m=[32m"surface-ledger-primary"[39m
                  [36m>[39m
                    [0mOpen loop: Older loop[0m
                  [36m</span>[39m
                  [36m<span[39m
                    [33mclass[39m=[32m"surface-ledger-trailing"[39m
                  [36m>[39m
                    [36m<button[39m
                      [33mclass[39m=[32m"btn btn--ghost btn--sm "[39m
                      [33mtype[39m=[32m"button"[39m
                    [36m>[39m
                      [0mAck[0m
                    [36m</button>[39m
                    [36m<button[39m
                      [33mclass[39m=[32m"btn btn--ghost btn--sm "[39m
                      [33mtype[39m=[32m"button"[39m
                    [36m>[39m
                      [0mDefer[0m
                    [36m</button>[39m
                  [36m</span>[39m
                [36m</div>[39m
              [36m</li>[39m
            [36m</div>[39m
            [36m<button[39m
              [33mclass[39m=[32m"btn btn--ghost btn--sm "[39m
              [33mdata-testid[39m=[32m"arrival-bri...
 ❯ Proxy.waitForWrapper node_modules/@testing-library/dom/dist/wait-for.js:163:27
 ❯ src/desk/chair/__tests__/decisionRows.philo402.test.tsx:142:11
    140|       screen.getByTestId("arrival-brief-generate").click();
    141|     });
    142|     await waitFor(() => {
       |           ^
    143|       expect(screen.getByText("Review decision: Newest decision")).toB…
    144|     });

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[2/2]⎯


 Test Files  1 failed (1)
      Tests  2 failed (2)
   Start at  00:43:13
   Duration  1.79s (transform 328ms, setup 55ms, import 445ms, tests 1.05s, environment 167ms)
```

### Captured run — 2026-09-24T06:48:01Z

- **Command:** `bash -c set -o pipefail; cd .tmp/philo402-main && uv run --no-sync pytest -q tests/unit/test_philo4_02_decision_rows.py 2>&1 | tee ../../docs/internal/philo/phase-4/rows/red-producer-final.log`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 549696da704d91e91d5f6fd0038ae74ea765caca

```text
FFF                                                                      [100%]
=================================== FAILURES ===================================
___________ test_generate_carries_created_at_on_every_decision_item ____________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-474/test_generate_carries_created_0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10e4236f0>

    def test_generate_carries_created_at_on_every_decision_item(tmp_path, monkeypatch):
        db = Database(tmp_path / "brief.db")
        service = MondayBriefService(db, clock=lambda: NOW)
        _upsert_desk_decision(
            db,
            decision_id="decision-z-old",
            title="Old decision one",
            created_at="2026-08-01T08:45:00",
        )
        _upsert_desk_decision(
            db,
            decision_id="decision-a-new",
            title="Newest decision",
            created_at="2026-08-04T08:45:00",
        )
        monkeypatch.setattr(
            brief_module,
            "uuid",
            SimpleNamespace(uuid4=_fixed_uuid4("f" * 32, "0" * 32, "1" * 32)),
        )
    
        generated = service.generate(None, now=NOW)
        reloaded = service.get_latest(None)
        assert reloaded is not None
        assert generated.id == reloaded.id
>       assert [item.created_at for item in reloaded.sections["decisions"]] == [
                ^^^^^^^^^^^^^^^
            "2026-08-04T08:45:00",
            "2026-08-01T08:45:00",
        ]
E       AttributeError: 'BriefItem' object has no attribute 'created_at'

tests/unit/test_philo4_02_decision_rows.py:65: AttributeError
________ test_generate_and_reload_sorts_decisions_by_record_created_at _________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-474/test_generate_and_reload_sorts0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10e6008a0>

    def test_generate_and_reload_sorts_decisions_by_record_created_at(tmp_path, monkeypatch):
        db = Database(tmp_path / "brief.db")
        service = MondayBriefService(db, clock=lambda: NOW)
        _upsert_desk_decision(
            db,
            decision_id="decision-z-old",
            title="Old decision one",
            created_at="2026-08-01T08:45:00",
        )
        _upsert_desk_decision(
            db,
            decision_id="decision-m-old",
            title="Old decision two",
            created_at="2026-08-02T08:45:00",
        )
        _upsert_desk_decision(
            db,
            decision_id="decision-a-new",
            title="Newest decision",
            created_at="2026-08-04T08:45:00",
        )
        # The generated item ids are fixed only to make the pre-fix reload order
        # deterministic. The assertion below uses the record timestamps/text.
        monkeypatch.setattr(
            brief_module,
            "uuid",
            SimpleNamespace(uuid4=_fixed_uuid4("f" * 32, "0" * 32, "1" * 32, "2" * 32)),
        )
    
        service.generate(None, now=NOW)
        reloaded = service.get_latest(None)
        assert reloaded is not None
>       assert [item.text for item in reloaded.sections["decisions"]] == [
            "Review decision: Newest decision",
            "Review decision: Old decision two",
            "Review decision: Old decision one",
        ]
E       AssertionError: assert ['Review deci...est decision'] == ['Review deci...decision one']
E         
E         At index 0 diff: 'Review decision: Old decision one' != 'Review decision: Newest decision'
E         Use -v to get more diff

tests/unit/test_philo4_02_decision_rows.py:104: AssertionError
______ test_generate_carries_created_at_from_meeting_decision_projection _______

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-474/test_generate_carries_created_1')

    def test_generate_carries_created_at_from_meeting_decision_projection(tmp_path):
        db = Database(tmp_path / "brief.db")
        db.meetings.save_meeting(
            MeetingState(
                id="meeting-decision-source",
                title="Decision fixture",
                started_at=datetime.datetime(2026, 8, 3, 8),
                ended_at=datetime.datetime(2026, 8, 3, 8, 30),
            )
        )
        db.plugins.record_artifact(
            artifact_id="decision-artifact",
            meeting_id="meeting-decision-source",
            artifact_type="decisions",
            title="Decision fixture",
            structured_json={"decisions": [{"decision": "Use the local desk"}]},
            plugin_id="decision_capture",
        )
        decision = db.decisions.list(lifecycle="recorded")[0]
    
        service = MondayBriefService(db, clock=lambda: NOW)
        service.generate(None, now=NOW)
        reloaded = service.get_latest(None)
        assert reloaded is not None
        item = next(
            item for item in reloaded.sections["decisions"]
            if item.text == "Review decision: Use the local desk"
        )
>       assert item.created_at == decision.created_at
               ^^^^^^^^^^^^^^^
E       AttributeError: 'BriefItem' object has no attribute 'created_at'

tests/unit/test_philo4_02_decision_rows.py:139: AttributeError
=========================== short test summary info ============================
FAILED tests/unit/test_philo4_02_decision_rows.py::test_generate_carries_created_at_on_every_decision_item
FAILED tests/unit/test_philo4_02_decision_rows.py::test_generate_and_reload_sorts_decisions_by_record_created_at
FAILED tests/unit/test_philo4_02_decision_rows.py::test_generate_carries_created_at_from_meeting_decision_projection
3 failed in 1.29s
```

### Captured run — 2026-09-24T06:49:15Z

- **Command:** `bash -c set -o pipefail; uv run --no-sync pytest --collect-only -q tests/unit/test_philo4_02_decision_rows.py tests/unit/test_philo4_02_readable_rows.py tests/unit/test_monday_brief_service.py tests/unit/test_philo4_03_breakage_ids.py tests/unit/test_hs175_week_brief.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo_graph_schema.py tests/unit/test_graph_walk_calibration.py 2>&1 | tee docs/internal/philo/phase-4/rows/collect-python.log`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 549696da704d91e91d5f6fd0038ae74ea765caca

```text
tests/unit/test_philo4_02_decision_rows.py::test_generate_carries_created_at_on_every_decision_item
tests/unit/test_philo4_02_decision_rows.py::test_generate_and_reload_sorts_decisions_by_record_created_at
tests/unit/test_philo4_02_decision_rows.py::test_generate_carries_created_at_from_meeting_decision_projection
tests/unit/test_philo4_02_readable_rows.py::test_readable_text_uses_element_from_point_and_rejects_a_covering_dock
tests/unit/test_philo4_02_readable_rows.py::test_readable_text_rejects_missing_text_or_unreadable_geometry[<lambda>0]
tests/unit/test_philo4_02_readable_rows.py::test_readable_text_rejects_missing_text_or_unreadable_geometry[<lambda>1]
tests/unit/test_philo4_02_readable_rows.py::test_readable_text_rejects_missing_text_or_unreadable_geometry[<lambda>2]
tests/unit/test_philo4_02_readable_rows.py::test_readable_text_rejects_missing_text_or_unreadable_geometry[<lambda>3]
tests/unit/test_philo4_02_readable_rows.py::test_readable_text_rejects_missing_text_or_unreadable_geometry[<lambda>4]
tests/unit/test_philo4_02_readable_rows.py::test_atlas_declares_readable_text_for_the_as_written_chain_case
tests/unit/test_philo4_02_readable_rows.py::test_readable_text_is_in_the_shared_schema_vocabulary
tests/unit/test_monday_brief_service.py::test_compute_window_on_monday_starts_previous_friday
tests/unit/test_monday_brief_service.py::test_compute_window_on_wednesday_starts_previous_day
tests/unit/test_monday_brief_service.py::test_compute_window_preserves_timezone_across_dst
tests/unit/test_monday_brief_service.py::test_generate_creates_empty_brief
tests/unit/test_monday_brief_service.py::test_generate_is_idempotent_for_same_day
tests/unit/test_monday_brief_service.py::test_get_latest_returns_most_recent_brief
tests/unit/test_monday_brief_service.py::test_generate_collects_write_operations_as_persisted_changes
tests/unit/test_monday_brief_service.py::test_collect_changes_excludes_read_only_operations
tests/unit/test_monday_brief_service.py::test_collect_changes_collapses_a_correlated_retry
tests/unit/test_monday_brief_service.py::test_collect_changes_collapses_an_uncorrelated_failed_retry
tests/unit/test_monday_brief_service.py::test_collect_changes_excludes_events_outside_the_window
tests/unit/test_monday_brief_service.py::test_collect_changes_returns_no_items_for_an_empty_window
tests/unit/test_monday_brief_service.py::test_compose_headline_mentions_each_populated_section
tests/unit/test_monday_brief_service.py::test_compose_headline_is_specific_to_the_populated_section
tests/unit/test_monday_brief_service.py::test_compose_empty_brief_has_honest_headline
tests/unit/test_monday_brief_service.py::test_compose_sorts_items_within_each_section_by_priority
tests/unit/test_monday_brief_service.py::test_compose_headline_is_deterministic
tests/unit/test_philo4_03_breakage_ids.py::test_a_pipeline_failure_in_two_lookbacks_generates_both_briefs
tests/unit/test_philo4_03_breakage_ids.py::test_a_connector_failure_in_two_lookbacks_generates_both_briefs
tests/unit/test_hs175_week_brief.py::TestComputeWindowUnchanged::test_monday_still_looks_back_to_friday
tests/unit/test_hs175_week_brief.py::TestComputeWindowUnchanged::test_wednesday_looks_back_to_tuesday
tests/unit/test_hs175_week_brief.py::TestComputeLookahead::test_wednesday_to_sunday
tests/unit/test_hs175_week_brief.py::TestComputeLookahead::test_monday_to_sunday
tests/unit/test_hs175_week_brief.py::TestComputeLookahead::test_sunday_to_same_sunday
tests/unit/test_hs175_week_brief.py::TestComputeLookahead::test_default_now_is_tz_aware
tests/unit/test_hs175_week_brief.py::TestCollectCalendarEvents::test_counts_events_in_range
tests/unit/test_hs175_week_brief.py::TestCollectCalendarEvents::test_next_event_after_now
tests/unit/test_hs175_week_brief.py::TestCollectCalendarEvents::test_empty_when_no_events
tests/unit/test_hs175_week_brief.py::TestCollectCalendarEvents::test_armed_count
tests/unit/test_hs175_week_brief.py::TestCollectMeetingWatch::test_new_decisions
tests/unit/test_hs175_week_brief.py::TestCollectMeetingWatch::test_commitments_due_this_week
tests/unit/test_hs175_week_brief.py::TestCollectMeetingWatch::test_empty_when_no_data
tests/unit/test_hs175_week_brief.py::TestBriefGenerationThisWeek::test_generate_lookback_unchanged
tests/unit/test_hs175_week_brief.py::TestBriefGenerationThisWeek::test_sections_include_this_week
tests/unit/test_hs175_week_brief.py::TestBriefGenerationThisWeek::test_calendar_items_land_in_this_week
tests/unit/test_hs175_week_brief.py::TestBriefGenerationThisWeek::test_meeting_watch_items_land_in_this_week
tests/unit/test_hs175_week_brief.py::TestBriefGenerationThisWeek::test_headline_includes_meeting_count
tests/unit/test_hs175_week_brief.py::TestBriefGenerationThisWeek::test_commitment_detail_includes_text_and_date
tests/unit/test_hs175_week_brief.py::TestComputeWindowByteIdentical::test_body_digest_pinned
tests/unit/test_hs175_week_brief.py::TestForwardHalfReadsFromNow::test_monday_afternoon_counts_only_what_is_coming
tests/unit/test_hs175_week_brief.py::TestForwardHalfReadsFromNow::test_naive_local_now_is_read_as_local
tests/unit/test_hs175_week_brief.py::TestForwardHalfReadsFromNow::test_commitment_due_today_counts_and_next_week_does_not
tests/unit/test_hs175_week_brief.py::TestRecordedOccurrenceDedup::test_recorded_occurrence_is_since_fridays_not_this_weeks
tests/unit/test_hs175_week_brief.py::TestRecordedOccurrenceDedup::test_recurring_series_next_occurrence_survives
tests/unit/test_hs175_week_brief.py::TestComposeCountsCalendarItems::test_headline_names_meetings_armed_and_due
tests/unit/test_hs175_week_brief.py::TestComposeCountsCalendarItems::test_headline_with_decisions
tests/unit/test_hs175_week_brief.py::TestCommitmentSaidOnce::test_commitment_due_today_appears_once_in_this_week
tests/unit/test_hs175_week_brief.py::TestShadeReadOfSeededBrief::test_latest_returns_the_seed_before_and_after_a_hub_generate
tests/unit/test_hs175_week_brief.py::TestComposeNeverPrintsABareStop::test_next_row_alone_is_one_item
tests/unit/test_philo_graph_atlas.py::test_every_atlas_file_is_read
tests/unit/test_philo_graph_atlas.py::test_schema_is_a_valid_2020_12_schema
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas-phase3.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase3.json]
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas.json]
tests/unit/test_philo_graph_atlas.py::test_ids_are_unique
tests/unit/test_philo_graph_atlas.py::test_every_case_state_id_resolves
tests/unit/test_philo_graph_atlas.py::test_every_case_reference_inside_the_atlas_resolves
tests/unit/test_philo_graph_atlas.py::test_every_clock_a_case_uses_is_declared
tests/unit/test_philo_graph_atlas.py::test_every_applicable_case_carries_one_trigger
tests/unit/test_philo_graph_atlas.py::test_no_timer_edge_is_triggered_by_a_substitute_button
tests/unit/test_philo_graph_atlas.py::test_every_api_setup_step_exists_in_the_generated_openapi
tests/unit/test_philo_graph_atlas.py::test_every_fixture_step_exists_and_hashes_as_claimed
tests/unit/test_philo_graph_atlas.py::test_every_phase1_reference_resolves_to_a_record
tests/unit/test_philo_graph_atlas.py::test_every_selected_job_has_an_applicable_case_except_j8
tests/unit/test_philo_graph_atlas.py::test_every_brief_family_is_present
tests/unit/test_philo_graph_atlas.py::test_quiet_is_never_an_attention_state
tests/unit/test_philo_graph_atlas.py::test_face_cases_carry_both_ruled_viewports
tests/unit/test_philo_graph_atlas.py::test_unexercised_states_name_a_mechanism_and_a_cost
tests/unit/test_philo_graph_atlas.py::test_source_commit_is_the_revision_the_atlas_was_derived_from
tests/unit/test_philo_graph_atlas.py::test_every_applicable_predicate_is_a_kind_the_rig_implements
tests/unit/test_philo_graph_atlas.py::test_every_predicate_observes_a_selector_or_a_route
tests/unit/test_philo_graph_atlas.py::test_protocol_predicates_ask_for_a_new_row
tests/unit/test_philo_graph_atlas.py::test_every_case_keeps_its_human_sentence
tests/unit/test_philo_graph_atlas.py::test_every_ui_action_is_one_the_rig_implements
tests/unit/test_philo_graph_atlas.py::test_every_boundary_names_its_substitution
tests/unit/test_philo_graph_atlas.py::test_summary_cases_use_the_retained_architect_import_fixture
tests/unit/test_philo_graph_atlas.py::test_summary_run_cases_have_one_run_trigger
tests/unit/test_philo_graph_atlas.py::test_summary_running_reads_the_claimed_job_wire_status
tests/unit/test_philo_graph_atlas.py::test_summary_queued_reads_the_run_admission_response
tests/unit/test_philo_graph_atlas.py::test_summary_preconditions_do_not_require_future_or_consumed_run_state
tests/unit/test_philo_graph_atlas.py::test_summary_state_reads_do_not_require_a_new_row_after_setup_run
tests/unit/test_philo_graph_atlas.py::test_summary_manual_retry_requires_failed_producer_and_current_route
tests/unit/test_philo_graph_atlas.py::test_summary_planned_host_cases_check_real_text_and_control_ownership
tests/unit/test_philo_graph_atlas.py::test_summary_failure_cases_retain_reply_at_the_provider_boundary
tests/unit/test_philo_graph_atlas.py::test_summary_imports_wait_for_real_completion_and_retain_title
tests/unit/test_philo_graph_atlas.py::test_summary_arrival_observations_name_the_rendered_states
tests/unit/test_philo_graph_atlas.py::test_summary_models_window_closes_before_arrival_steps
tests/unit/test_philo_graph_atlas.py::test_summary_restart_proof_retains_summary_receipt_and_identity
tests/unit/test_philo_graph_atlas.py::test_summary_microphone_cases_keep_the_lawful_blocked_boundary
tests/unit/test_philo_graph_atlas.py::test_summary_cases_do_not_claim_the_old_pangram
tests/unit/test_philo_graph_atlas.py::test_summary_stop_cases_require_a_real_active_meeting
tests/unit/test_philo_graph_atlas.py::test_the_two_schemas_agree_on_the_case_contract
tests/unit/test_philo_graph_atlas.py::test_every_case_validates_against_the_graph_case_schema
tests/unit/test_philo_graph_atlas.py::test_the_graph_predicate_enum_does_not_outrun_the_rig
tests/unit/test_philo_graph_atlas.py::test_a_case_without_a_predicate_is_unreachable_with_a_reason
tests/unit/test_philo_graph_atlas.py::test_every_council_reading_names_its_sources
tests/unit/test_philo_graph_atlas.py::test_no_precondition_check_compares_two_snapshots
tests/unit/test_philo_graph_atlas.py::test_every_precondition_check_observes_a_selector_or_a_route
tests/unit/test_philo_graph_atlas.py::test_no_check_asserts_the_result_the_trigger_must_produce
tests/unit/test_philo_graph_atlas.py::test_every_protocol_field_path_with_a_placeholder_is_a_json_pointer
tests/unit/test_philo_graph_atlas.py::test_no_step_acts_on_a_root_placeholder
tests/unit/test_philo_graph_atlas.py::test_navigation_steps_carry_no_selector
tests/unit/test_philo_graph_atlas.py::test_every_click_and_fill_names_a_control
tests/unit/test_philo_graph_atlas.py::test_every_desk_face_case_crosses_the_gate_first
tests/unit/test_philo_graph_atlas.py::test_no_gate_case_crosses_the_gate_in_setup
tests/unit/test_philo_graph_atlas.py::test_gate_cases_check_the_gate_not_the_desk
tests/unit/test_philo_graph_atlas.py::test_every_captured_id_names_the_field_it_reads
tests/unit/test_philo_graph_atlas.py::test_same_day_generate_again_binds_returned_displayed_and_retained
tests/unit/test_philo_graph_atlas.py::test_no_populated_brief_case_reads_the_headline
tests/unit/test_philo_graph_atlas.py::test_the_brief_recipe_fence_refuses_its_mutations
tests/unit/test_philo_graph_atlas.py::test_the_populated_brief_predicate_needs_the_minted_row
tests/unit/test_philo_graph_atlas.py::test_j11_kept_verifies_the_saved_words_in_the_store
tests/unit/test_philo_graph_atlas.py::test_same_day_same_id_fails_a_different_id_by_machine
tests/unit/test_philo_graph_atlas.py::test_j10_retention_is_proven_after_another_reload
tests/unit/test_philo_graph_atlas.py::test_summary_failure_settings_reach_the_real_drainer_after_restart
tests/unit/test_philo_graph_atlas.py::test_summary_no_engine_absence_is_read_inside_the_existing_meetings_scope
tests/unit/test_philo_graph_atlas.py::test_summary_reload_reads_the_same_already_persisted_summary
tests/unit/test_philo_graph_atlas.py::test_summary_terminal_cases_read_durable_meeting_not_active_queue[case.j6.run_summary.intel_ready-/intel_job/status]
tests/unit/test_philo_graph_atlas.py::test_summary_terminal_cases_read_durable_meeting_not_active_queue[case.j6.run_summary.host_named-/run_receipt/attempts/0/host]
tests/unit/test_philo_graph_schema.py::test_schema_is_a_valid_draft_2020_12_schema
tests/unit/test_philo_graph_schema.py::test_worked_example_passes_schema_and_integrity
tests/unit/test_philo_graph_schema.py::test_worked_example_joins_phase1_records_and_api_pairs
tests/unit/test_philo_graph_schema.py::test_observations_are_stored_one_per_brain_pass_viewport
tests/unit/test_philo_graph_schema.py::test_unresolved_link_endpoint_is_refused
tests/unit/test_philo_graph_schema.py::test_observation_without_provenance_is_refused
tests/unit/test_philo_graph_schema.py::test_finding_without_a_bin_is_refused
tests/unit/test_philo_graph_schema.py::test_case_without_an_expected_predicate_is_refused
tests/unit/test_philo_graph_schema.py::test_duplicate_ids_are_refused
tests/unit/test_philo_graph_schema.py::test_phase1_record_id_must_exist_in_that_inventory
tests/unit/test_philo_graph_schema.py::test_phase1_api_reference_must_exist_as_that_method_and_path
tests/unit/test_philo_graph_schema.py::test_phase1_api_reference_must_match_the_declared_method
tests/unit/test_philo_graph_schema.py::test_phase1_inventory_must_be_a_file_in_the_tree
tests/unit/test_philo_graph_schema.py::test_claim_review_record_reference_must_exist
tests/unit/test_philo_graph_schema.py::test_source_path_must_exist_in_the_tree
tests/unit/test_philo_graph_schema.py::test_evidence_path_must_exist_in_the_tree
tests/unit/test_philo_graph_schema.py::test_cli_exits_zero_on_the_example_and_one_on_a_broken_graph
tests/unit/test_graph_walk_calibration.py::test_rig_is_versioned
tests/unit/test_graph_walk_calibration.py::test_six_calibration_cases_get_their_expected_verdicts
tests/unit/test_graph_walk_calibration.py::test_no_calibration_verdict_comes_from_the_presence_of_a_diff
tests/unit/test_graph_walk_calibration.py::test_the_wrong_target_case_records_where_the_result_landed
tests/unit/test_graph_walk_calibration.py::test_the_operation_that_never_completes_is_incomplete_not_settled
tests/unit/test_graph_walk_calibration.py::test_every_observation_carries_provenance_and_before_after
tests/unit/test_graph_walk_calibration.py::test_run_ids_are_unique_per_case_brain_viewport
tests/unit/test_graph_walk_calibration.py::test_home_under_the_owners_local_share_is_refused
tests/unit/test_graph_walk_calibration.py::test_a_temporary_home_is_accepted
tests/unit/test_graph_walk_calibration.py::test_an_unexplained_zero_diff_is_not_a_pass
tests/unit/test_graph_walk_calibration.py::test_a_window_already_open_before_the_trigger_is_not_the_trigger_opening_it
tests/unit/test_graph_walk_calibration.py::test_every_negative_control_comes_out_as_stated
tests/unit/test_graph_walk_calibration.py::test_a_refresh_with_its_handler_removed_fails
tests/unit/test_graph_walk_calibration.py::test_a_replay_identity_must_name_an_attribute_or_the_response
tests/unit/test_graph_walk_calibration.py::test_a_result_after_the_bound_is_never_a_pass
tests/unit/test_graph_walk_calibration.py::test_an_absence_needs_a_scope_that_exists
tests/unit/test_graph_walk_calibration.py::test_the_ui_vocabulary_is_closed_and_blocks_before_anything_fires
tests/unit/test_graph_walk_calibration.py::test_a_precondition_that_does_not_hold_blocks_the_case
tests/unit/test_graph_walk_calibration.py::test_a_precondition_that_holds_lets_the_case_run
tests/unit/test_graph_walk_calibration.py::test_a_words_only_case_is_blocked_and_never_a_keyerror
tests/unit/test_graph_walk_calibration.py::test_an_unreachable_case_keeps_its_reason_verbatim
tests/unit/test_graph_walk_calibration.py::test_a_captured_value_drives_a_later_step_and_the_predicate
tests/unit/test_graph_walk_calibration.py::test_an_unresolved_placeholder_is_blocked_and_never_sent
tests/unit/test_graph_walk_calibration.py::test_substitution_fills_only_identifiers
tests/unit/test_graph_walk_calibration.py::test_a_capture_without_a_value_blocks
tests/unit/test_graph_walk_calibration.py::test_a_check_step_in_setup_blocks_where_it_stands
tests/unit/test_graph_walk_calibration.py::test_a_check_step_that_holds_lets_the_case_run
tests/unit/test_graph_walk_calibration.py::test_the_step_vocabulary_is_closed_and_exported
tests/unit/test_graph_walk_calibration.py::test_a_relative_goto_resolves_against_the_hub
tests/unit/test_graph_walk_calibration.py::test_a_fixture_step_captures_from_its_own_response
tests/unit/test_graph_walk_calibration.py::test_a_trigger_identity_is_read_from_the_response_not_the_page
tests/unit/test_graph_walk_calibration.py::test_identity_display_requires_the_returned_id_to_be_the_displayed_one
tests/unit/test_graph_walk_calibration.py::test_a_row_match_reaches_a_nested_field
tests/unit/test_graph_walk_calibration.py::test_prose_in_expected_words_is_not_a_placeholder
tests/unit/test_graph_walk_calibration.py::test_a_label_only_boundary_is_refused
tests/unit/test_graph_walk_calibration.py::test_an_engine_reply_boundary_blocks_when_it_was_never_installed
tests/unit/test_graph_walk_calibration.py::test_an_engine_reply_boundary_records_the_installed_reply
tests/unit/test_graph_walk_calibration.py::test_the_replay_engine_answers_the_recorded_reply
tests/unit/test_graph_walk_calibration.py::test_the_scheduler_wait_adapter_lets_a_timer_edge_produce_the_result
tests/unit/test_graph_walk_calibration.py::test_every_new_predicate_kind_gets_its_verdict
tests/unit/test_graph_walk_calibration.py::test_a_refusal_status_is_read_from_the_triggers_own_response
tests/unit/test_graph_walk_calibration.py::test_a_row_gone_is_named_never_merely_fewer
tests/unit/test_graph_walk_calibration.py::test_protocol_field_reads_one_named_field
tests/unit/test_graph_walk_calibration.py::test_input_value_reads_the_field_not_the_dom_text
tests/unit/test_graph_walk_calibration.py::test_a_restart_is_a_real_restart_and_the_value_survives
tests/unit/test_graph_walk_calibration.py::test_any_other_cli_command_stays_blocked_with_its_name
tests/unit/test_graph_walk_calibration.py::test_a_refusal_must_name_what_is_missing
tests/unit/test_graph_walk_calibration.py::test_an_asserted_absence_is_earned_by_the_named_bound
tests/unit/test_graph_walk_calibration.py::test_the_new_kinds_are_branches_the_atlas_fence_can_read
tests/unit/test_graph_walk_calibration.py::test_a_prose_predicate_is_blocked_not_guessed
tests/unit/test_graph_walk_calibration.py::test_protocol_rows_needs_a_NEW_matching_row_not_any_change
tests/unit/test_graph_walk_calibration.py::test_a_clock_step_blocks_instead_of_claiming_the_state
tests/unit/test_graph_walk_calibration.py::test_a_fixture_step_without_a_declared_boundary_blocks
tests/unit/test_graph_walk_calibration.py::test_an_unknown_step_kind_blocks
tests/unit/test_graph_walk_calibration.py::test_a_not_applicable_case_is_recorded_not_skipped
tests/unit/test_graph_walk_calibration.py::test_the_real_j4_import_case_fires_the_upload_and_binds_the_meeting_id
tests/unit/test_graph_walk_calibration.py::test_a_placeholder_nothing_binds_blocks_before_the_trigger
tests/unit/test_graph_walk_calibration.py::test_a_placeholder_still_unbound_after_the_trigger_blocks_naming_it
tests/unit/test_graph_walk_calibration.py::test_a_clicked_verb_reads_its_identity_from_its_own_response
tests/unit/test_graph_walk_calibration.py::test_a_clicked_verb_status_is_read_by_its_declared_route
tests/unit/test_graph_walk_calibration.py::test_a_different_id_beside_unchanged_old_content_fails
tests/unit/test_graph_walk_calibration.py::test_a_longer_id_does_not_display_a_shorter_one

210 te
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-09-24T06:49:33Z

- **Command:** `bash -c set -o pipefail; uv run --no-sync pytest -q tests/unit/test_philo4_02_decision_rows.py tests/unit/test_philo4_02_readable_rows.py tests/unit/test_monday_brief_service.py tests/unit/test_philo4_03_breakage_ids.py tests/unit/test_hs175_week_brief.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo_graph_schema.py tests/unit/test_graph_walk_calibration.py 2>&1 | tee docs/internal/philo/phase-4/rows/green-python-attempt1.log`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 549696da704d91e91d5f6fd0038ae74ea765caca

```text
.................................................................F...... [ 34%]
........................................................................ [ 68%]
..................................................................       [100%]
=================================== FAILURES ===================================
_________ test_every_source_reference_lands_on_its_symbol[atlas.json] __________

every_atlas = {'cases': [{'applicability': 'applicable', 'completion_bound_s': 20, 'edge_ids': ['edge.face.first_words_continue_late...son': 'the gate holds ONE capture state and ONE failure (web/src/desk/components/FirstWords.tsx:50, :51).'}, ...], ...}

    def test_every_source_reference_lands_on_its_symbol(every_atlas: dict) -> None:
        """A line number is evidence, not identity (brief section 1).
    
        The cited line must still hold the cited symbol, or the reference has
        drifted and the claim behind it is no longer proven.
        """
        problems: list[str] = []
        for state in every_atlas["states"]:
            for ref in state["sources"]:
                target = REPO / ref["path"]
                if not target.is_file():
                    problems.append(f"{state['id']}: missing file {ref['path']}")
                    continue
                lines = target.read_text(errors="replace").splitlines()
                if not 1 <= ref["line"] <= len(lines):
                    problems.append(
                        f"{state['id']}: {ref['path']}:{ref['line']} is past the end of the file"
                    )
                    continue
                line = lines[ref["line"] - 1]
                if ref["symbol"] not in line:
                    problems.append(
                        f"{state['id']}: {ref['path']}:{ref['line']} no longer holds "
                        f"{ref['symbol']!r} (line reads {line.strip()[:80]!r})"
                    )
>       assert not problems, "\n".join(problems)
E       AssertionError: state.briefs.absent: web/src/desk/chair/ChairHome.tsx:1278 no longer holds '!briefLoading && !brief' (line reads '>')
E         state.briefs.loading: web/src/desk/chair/ChairHome.tsx:522 no longer holds 'setBriefLoading' (line reads 'const readBrief = useCallback(() => {')
E         state.briefs.generating: web/src/desk/chair/ChairHome.tsx:713 no longer holds 'generating' (line reads 'idiom) or failed (BRIEF DID NOT GENERATE · <cause>). */')
E         state.briefs.generation_failure: web/src/desk/chair/ChairHome.tsx:688 no longer holds 'setGenerateFailed' (line reads '} catch (error) {')
E         state.briefs.generated_empty: holdspeak/services/monday_brief_service.py:1189 no longer holds 'is_empty' (line reads 'state = excluded.state,')
E         state.briefs.generated_empty: holdspeak/services/monday_brief_service.py:341 no longer holds 'No changes' (line reads 'for section in _SECTIONS')
E         state.briefs.populated: holdspeak/services/monday_brief_service.py:114 no longer holds 'is_empty' (line reads 'headline: str')
E         state.briefs.populated: web/src/desk/chair/ChairHome.tsx:846 no longer holds 'briefItems' (line reads 'const sortDecisionItems = (items: BriefItem[]) => [...items].sort((a, b) => {')
E         state.briefs.reload_persisted: web/src/desk/chair/ChairHome.tsx:1333 no longer holds 'arrival-brief' (line reads '</div>')
E         state.briefs.item.untouched: holdspeak/services/monday_brief_service.py:115 no longer holds 'untouched' (line reads 'sections: dict[str, list[BriefItem]]')
E         state.briefs.item.untouched: web/src/desk/chair/ChairHome.tsx:849 no longer holds 'briefShelf' (line reads 'return bTime - aTime;')
E         state.briefs.item.deferred: holdspeak/services/monday_brief_service.py:1117 no longer holds 'SHELF_STATES' (line reads '"""SELECT DISTINCT m.calendar_event_id AS event_id')
E         state.briefs.same_day_idempotent: holdspeak/services/monday_brief_service.py:198 no longer holds 'date_key' (line reads '"""Generate or return the existing brief for the current local date."""')
E         state.briefs.same_day_idempotent: holdspeak/services/monday_brief_service.py:213 no longer holds '_load_brief' (line reads '(date_key,),')
E         state.briefs.next_day_window: holdspeak/services/monday_brief_service.py:197 no longer holds 'self._clock()' (line reads ') -> MondayBrief:')
E         state.briefs.next_day_window: holdspeak/services/monday_brief_service.py:198 no longer holds 'date_key' (line reads '"""Generate or return the existing brief for the current local date."""')
E         state.meetings.transcription.present: web/src/desk/chair/ChairHome.tsx:2240 no longer holds 'hasTranscript' (line reads "// job with nothing to execute it says so here, in the badge species'")
E         state.desk_presentation.reload_reconnect: web/src/desk/chair/ChairHome.tsx:626 no longer holds 're-reads' (line reads '// `desk/returnToTask.ts:113`), and every face holding an unfinished task')
E         state.desk_presentation.reload_reconnect: web/src/desk/chair/ChairHome.tsx:525 no longer holds 'apiFetch' (line reads 'setGenerateFailed(null);')
E         state.time.next_day: holdspeak/services/monday_brief_service.py:198 no longer holds 'date_key' (line reads '"""Generate or return the existing brief for the current local date."""')
E       assert not ["state.briefs.absent: web/src/desk/chair/ChairHome.tsx:1278 no longer holds '!briefLoading && !brief' (line reads '>'...dspeak/services/monday_brief_service.py:341 no longer holds 'No changes' (line reads 'for section in _SECTIONS')", ...]

tests/unit/test_philo_graph_atlas.py:279: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas.json]
1 failed, 209 passed in 106.98s (0:01:46)
```

### Captured run — 2026-09-24T06:52:33Z

- **Command:** `bash -c set -o pipefail; cd .tmp/philo402-main && uv run --no-sync pytest -q tests/unit/test_philo_graph_atlas.py -k source_reference 2>&1 | tee ../../docs/internal/philo/phase-4/rows/baseline-atlas-anchors.log`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 549696da704d91e91d5f6fd0038ae74ea765caca

```text
.F                                                                       [100%]
=================================== FAILURES ===================================
_________ test_every_source_reference_lands_on_its_symbol[atlas.json] __________

every_atlas = {'cases': [{'applicability': 'applicable', 'completion_bound_s': 20, 'edge_ids': ['edge.face.first_words_continue_late...son': 'the gate holds ONE capture state and ONE failure (web/src/desk/components/FirstWords.tsx:50, :51).'}, ...], ...}

    def test_every_source_reference_lands_on_its_symbol(every_atlas: dict) -> None:
        """A line number is evidence, not identity (brief section 1).
    
        The cited line must still hold the cited symbol, or the reference has
        drifted and the claim behind it is no longer proven.
        """
        problems: list[str] = []
        for state in every_atlas["states"]:
            for ref in state["sources"]:
                target = REPO / ref["path"]
                if not target.is_file():
                    problems.append(f"{state['id']}: missing file {ref['path']}")
                    continue
                lines = target.read_text(errors="replace").splitlines()
                if not 1 <= ref["line"] <= len(lines):
                    problems.append(
                        f"{state['id']}: {ref['path']}:{ref['line']} is past the end of the file"
                    )
                    continue
                line = lines[ref["line"] - 1]
                if ref["symbol"] not in line:
                    problems.append(
                        f"{state['id']}: {ref['path']}:{ref['line']} no longer holds "
                        f"{ref['symbol']!r} (line reads {line.strip()[:80]!r})"
                    )
>       assert not problems, "\n".join(problems)
E       AssertionError: state.briefs.generated_empty: holdspeak/services/monday_brief_service.py:1189 no longer holds 'is_empty' (line reads 'detail=item["detail"],')
E         state.briefs.generated_empty: holdspeak/services/monday_brief_service.py:341 no longer holds 'No changes' (line reads 'counts = {section: len(items) for section, items in finalized_sections.items()}')
E         state.briefs.item.deferred: holdspeak/services/monday_brief_service.py:1117 no longer holds 'SHELF_STATES' (line reads ').fetchone()')
E       assert not ['state.briefs.generated_empty: holdspeak/services/monday_brief_service.py:1189 no longer holds \'is_empty\' (line rea....deferred: holdspeak/services/monday_brief_service.py:1117 no longer holds 'SHELF_STATES' (line reads ').fetchone()')"]

tests/unit/test_philo_graph_atlas.py:279: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas.json]
1 failed, 1 passed, 69 deselected in 0.70s
```

### Captured run — 2026-09-24T06:53:21Z

- **Command:** `bash -c set -o pipefail; uv run --no-sync pytest -q tests/unit/test_philo4_02_decision_rows.py tests/unit/test_philo4_02_readable_rows.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo4_01_atlas_contracts.py 2>&1 | tee docs/internal/philo/phase-4/rows/green-python.log`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 549696da704d91e91d5f6fd0038ae74ea765caca

```text
........................................................................ [ 80%]
..................                                                       [100%]
90 passed in 3.35s
```

### Captured run — 2026-09-24T06:53:41Z

- **Command:** `bash -c set -o pipefail; cd web && npx vitest list src/desk/chair/__tests__/decisionRows.philo402.test.tsx 2>&1 | tee ../docs/internal/philo/phase-4/rows/collect-rendered.log && npx vitest run src/desk/chair --maxWorkers=2 2>&1 | tee ../docs/internal/philo/phase-4/rows/green-rendered.log`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 549696da704d91e91d5f6fd0038ae74ea765caca

```text
src/desk/chair/__tests__/decisionRows.philo402.test.tsx > PHILO-4-02: decision rows lead the Arrival cap > shows the newest decision first with an honest cap and fold
src/desk/chair/__tests__/decisionRows.philo402.test.tsx > PHILO-4-02: decision rows lead the Arrival cap > keeps the result ordered after Generate replaces an existing brief

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-4-02/web


 Test Files  14 passed (14)
      Tests  81 passed (81)
   Start at  00:53:42
   Duration  5.20s (transform 627ms, setup 581ms, import 2.38s, tests 4.01s, environment 2.34s)
```

### Captured run — 2026-09-24T06:54:01Z

- **Command:** `bash -c set -o pipefail; uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.closure.chain.s5_next_day_brief_has_it --brain astra --viewport 1440 --engine real --out pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/ 2>&1 | tee docs/internal/philo/phase-4/rows/rig-1440.log`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 549696da704d91e91d5f6fd0038ae74ea765caca

```text
[glass_infra] web bundle rebuilt in 4.5s
PASS: live
BRAIN: astra
SOURCE: 566495b076f8db7387f7e050be30d8065ee8841b dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-Dgg98rIX.js'] hub=http://127.0.0.1:50849 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-yzfbadl_/.local/share/holdspeak/holdspeak.db engine=real
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/20260924T065401Z-case.closure.chain.s5_next_day_brief_has_it-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/20260924T065401Z-case.closure.chain.s5_next_day_brief_has_it-astra-1440/after.png']
NOTE: predicate: 'Review decision: Keep summary retrieval on the local desk' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 256, 'y': 359, 'w': 928, 'h': 44}
```

### Captured run — 2026-09-24T06:58:29Z

- **Command:** `bash -c set -o pipefail; uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.closure.chain.s5_next_day_brief_has_it --brain astra --viewport 393 --engine real --no-build --out pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/ 2>&1 | tee docs/internal/philo/phase-4/rows/rig-393.log`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 549696da704d91e91d5f6fd0038ae74ea765caca

```text
PASS: live
BRAIN: astra
SOURCE: 566495b076f8db7387f7e050be30d8065ee8841b dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-Dgg98rIX.js'] hub=http://127.0.0.1:51031 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-us4pdd0d/.local/share/holdspeak/holdspeak.db engine=real
JOB: j10
VERDICT: fail terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/20260924T065829Z-case.closure.chain.s5_next_day_brief_has_it-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/20260924T065829Z-case.closure.chain.s5_next_day_brief_has_it-astra-393/after.png']
NOTE: predicate: a covering element owns hit points: [{'x': 14, 'y': 582, 'owned': False, 'owner': 'div#desk-next > div.chair > footer.arrival-capture-bar'}, {'x': 197, 'y': 582, 'owned': False, 'owner': 'div#desk-next > div.chair > footer.arrival-capture-bar'}, {'x': 379, 'y': 582, 'owned': False, 'owner': 'div#desk-next > div.chair > footer.arrival-capture-bar'}]
NOTE: a nonzero diff with the wrong result is a finding, not a pass (changed: ['api_reads', 'document_text_len', 'document_text_sha256', 'focus_label', 'rect', 'text']).
```

### Captured run — 2026-09-24T07:12:41Z

- **Command:** `bash -c set -o pipefail; uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.closure.chain.s5_next_day_brief_has_it --brain astra --viewport 393 --engine real --out pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/ 2>&1 | tee docs/internal/philo/phase-4/rows/rig-393-seam.log`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 549696da704d91e91d5f6fd0038ae74ea765caca

```text
[glass_infra] web bundle rebuilt in 4.6s
PASS: live
BRAIN: astra
SOURCE: 566495b076f8db7387f7e050be30d8065ee8841b dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-esBq0c2t.js'] hub=http://127.0.0.1:52382 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-xpho8st6/.local/share/holdspeak/holdspeak.db engine=real
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/20260924T071241Z-case.closure.chain.s5_next_day_brief_has_it-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/20260924T071241Z-case.closure.chain.s5_next_day_brief_has_it-astra-393/after.png']
NOTE: predicate: 'Review decision: Keep summary retrieval on the local desk' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 12, 'y': 401, 'w': 369, 'h': 114}
```

### Captured run — 2026-09-24T07:13:37Z

- **Command:** `bash -c set -o pipefail; uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.closure.chain.s5_next_day_brief_has_it --brain astra --viewport 1440 --engine real --no-build --out pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/ 2>&1 | tee docs/internal/philo/phase-4/rows/rig-1440-seam.log`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 549696da704d91e91d5f6fd0038ae74ea765caca

```text
PASS: live
BRAIN: astra
SOURCE: 566495b076f8db7387f7e050be30d8065ee8841b dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-esBq0c2t.js'] hub=http://127.0.0.1:52487 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-gyxk9t3e/.local/share/holdspeak/holdspeak.db engine=real
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/20260924T071337Z-case.closure.chain.s5_next_day_brief_has_it-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/20260924T071337Z-case.closure.chain.s5_next_day_brief_has_it-astra-1440/after.png']
NOTE: predicate: 'Review decision: Keep summary retrieval on the local desk' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 256, 'y': 359, 'w': 928, 'h': 44}
```

### Captured run — 2026-09-24T07:14:42Z

- **Command:** `bash -c set -o pipefail; uv run --no-sync python docs/internal/philo/phase-4/rows/run_breakage_case.py 393 2>&1 | tee docs/internal/philo/phase-4/rows/rig-breakage-393.log`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 549696da704d91e91d5f6fd0038ae74ea765caca

```text
BREAKAGE_WINDOW TZ=Etc/GMT+11 local=2026-09-23T20:14:43.000669 after_close=True
PASS: live
BRAIN: astra
SOURCE: 566495b076f8db7387f7e050be30d8065ee8841b dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-esBq0c2t.js'] hub=http://127.0.0.1:52617 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-kaf34pkn/.local/share/holdspeak/holdspeak.db engine=real
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/20260924T071443Z-case.closure.chain.s5_next_day_brief_with_breakage-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/20260924T071443Z-case.closure.chain.s5_next_day_brief_with_breakage-astra-393/after.png']
NOTE: predicate: 'Review decision: Keep summary retrieval on the local desk' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 12, 'y': 401, 'w': 369, 'h': 114}
```

### Captured run — 2026-09-24T07:16:00Z

- **Command:** `bash -c set -o pipefail; uv run --no-sync python docs/internal/philo/phase-4/rows/run_breakage_case.py 1440 2>&1 | tee docs/internal/philo/phase-4/rows/rig-breakage-1440.log`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 549696da704d91e91d5f6fd0038ae74ea765caca

```text
BREAKAGE_WINDOW TZ=Etc/GMT+11 local=2026-09-23T20:16:00.193864 after_close=True
PASS: live
BRAIN: astra
SOURCE: 566495b076f8db7387f7e050be30d8065ee8841b dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-esBq0c2t.js'] hub=http://127.0.0.1:52730 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-dx5ul1y7/.local/share/holdspeak/holdspeak.db engine=real
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/20260924T071600Z-case.closure.chain.s5_next_day_brief_with_breakage-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/20260924T071600Z-case.closure.chain.s5_next_day_brief_with_breakage-astra-1440/after.png']
NOTE: predicate: 'Review decision: Keep summary retrieval on the local desk' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 256, 'y': 359, 'w': 928, 'h': 44}
```

### Captured run — 2026-09-24T07:17:15Z

- **Command:** `bash -c set -o pipefail; uv run --no-sync python docs/internal/philo/phase-4/rows/verify_closure.py pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/20260924T071241Z-case.closure.chain.s5_next_day_brief_has_it-astra-393/observation.json pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/20260924T071337Z-case.closure.chain.s5_next_day_brief_has_it-astra-1440/observation.json pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/20260924T071443Z-case.closure.chain.s5_next_day_brief_with_breakage-astra-393/observation.json pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/20260924T071600Z-case.closure.chain.s5_next_day_brief_with_breakage-astra-1440/observation.json 2>&1 | tee docs/internal/philo/phase-4/rows/closure-proof-seam.json`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 549696da704d91e91d5f6fd0038ae74ea765caca

```text
[
  {
    "run_id": "20260924T071241Z-case.closure.chain.s5_next_day_brief_has_it-astra-393",
    "viewport": 393,
    "verdict": "PASS",
    "first_brief": {
      "id": "brief-1a98ed480f8641948c6c72a6777ffa48",
      "generated_at": "2026-09-24T01:13:14.178453",
      "items": 3,
      "shelf": {}
    },
    "new_brief": {
      "id": "brief-baa294e3441a4c48ab498eb423f5b4b1",
      "generated_at": "2026-09-25T01:13:16.422596"
    },
    "decision": {
      "position": 1,
      "text": "Review decision: Keep summary retrieval on the local desk",
      "created_at": "2026-09-24T07:13:14Z",
      "rect": {
        "x": 12,
        "y": 401,
        "w": 369,
        "h": 114
      },
      "in_viewport": true,
      "all_owned": true
    },
    "old_brief_rows_and_triage_unchanged": true,
    "summary_receipt_and_identity_retained_after_restart": true,
    "breakage_rows": 0,
    "breakage_proof": null,
    "arrival_clearance": {
      "chair": {
        "x": 0,
        "y": 54,
        "w": 393,
        "h": 746
      },
      "capture_bar": {
        "x": 12,
        "y": 573,
        "w": 369,
        "h": 138
      },
      "scroll_top": 252,
      "scroll_padding_bottom": "138px",
      "end_margin_bottom": "138px"
    },
    "initial_feedback_s": 0.937,
    "terminal_reading": "'Review decision: Keep summary retrieval on the local desk' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 12, 'y': 401, 'w': 369, 'h': 114}"
  },
  {
    "run_id": "20260924T071337Z-case.closure.chain.s5_next_day_brief_has_it-astra-1440",
    "viewport": 1440,
    "verdict": "PASS",
    "first_brief": {
      "id": "brief-33e32ccfc8c248128093fa78a702c982",
      "generated_at": "2026-09-24T01:14:05.770615",
      "items": 3,
      "shelf": {}
    },
    "new_brief": {
      "id": "brief-cb8ebd5d0dab447db28ed1edf8582bbc",
      "generated_at": "2026-09-25T01:14:07.824775"
    },
    "decision": {
      "position": 1,
      "text": "Review decision: Keep summary retrieval on the local desk",
      "created_at": "2026-09-24T07:14:05Z",
      "rect": {
        "x": 256,
        "y": 359,
        "w": 928,
        "h": 44
      },
      "in_viewport": true,
      "all_owned": true
    },
    "old_brief_rows_and_triage_unchanged": true,
    "summary_receipt_and_identity_retained_after_restart": true,
    "breakage_rows": 0,
    "breakage_proof": null,
    "arrival_clearance": {
      "chair": {
        "x": 240,
        "y": 54,
        "w": 960,
        "h": 794
      },
      "capture_bar": {
        "x": 256,
        "y": 813,
        "w": 928,
        "h": 74
      },
      "scroll_top": 0,
      "scroll_padding_bottom": "auto",
      "end_margin_bottom": "0px"
    },
    "initial_feedback_s": 0.943,
    "terminal_reading": "'Review decision: Keep summary retrieval on the local desk' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 256, 'y': 359, 'w': 928, 'h': 44}"
  },
  {
    "run_id": "20260924T071443Z-case.closure.chain.s5_next_day_brief_with_breakage-astra-393",
    "viewport": 393,
    "verdict": "PASS",
    "first_brief": {
      "id": "brief-365ed5c5c40e41699108c7c3520fec53",
      "generated_at": "2026-09-23T20:15:11.662802",
      "items": 5,
      "shelf": {}
    },
    "new_brief": {
      "id": "brief-d304d3fc4bb449feb80753e37bddc1f3",
      "generated_at": "2026-09-24T20:15:13.907839"
    },
    "decision": {
      "position": 1,
      "text": "Review decision: Keep summary retrieval on the local desk",
      "created_at": "2026-09-24T07:15:11Z",
      "rect": {
        "x": 12,
        "y": 401,
        "w": 369,
        "h": 114
      },
      "in_viewport": true,
      "all_owned": true
    },
    "old_brief_rows_and_triage_unchanged": true,
    "summary_receipt_and_identity_retained_after_restart": true,
    "breakage_rows": 1,
    "breakage_proof": {
      "source_ref": "pipeline-event:34364731-0ec6-4a0a-a96f-ef61a6823e4c",
      "day_one_id": "brief-break-pipeline-brief-365ed5c5c40e41699108c7c3520fec53-34364731-0ec6-4a0a-a96f-ef61a6823e4c",
      "day_two_id": "brief-break-pipeline-brief-d304d3fc4bb449feb80753e37bddc1f3-34364731-0ec6-4a0a-a96f-ef61a6823e4c",
      "process_timezone": "Etc/GMT+11"
    },
    "arrival_clearance": {
      "chair": {
        "x": 0,
        "y": 54,
        "w": 393,
        "h": 746
      },
      "capture_bar": {
        "x": 12,
        "y": 573,
        "w": 369,
        "h": 138
      },
      "scroll_top": 372,
      "scroll_padding_bottom": "138px",
      "end_margin_bottom": "138px"
    },
    "initial_feedback_s": 0.941,
    "terminal_reading": "'Review decision: Keep summary retrieval on the local desk' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 12, 'y': 401, 'w': 369, 'h': 114}"
  },
  {
    "run_id": "20260924T071600Z-case.closure.chain.s5_next_day_brief_with_breakage-astra-1440",
    "viewport": 1440,
    "verdict": "PASS",
    "first_brief": {
      "id": "brief-4c290f3ee7914654836a39df024e8cce",
      "generated_at": "2026-09-23T20:16:29.013697",
      "items": 4,
      "shelf": {}
    },
    "new_brief": {
      "id": "brief-8a608e171ffd4a88bc5b1f0b48611b14",
      "generated_at": "2026-09-24T20:16:31.047421"
    },
    "decision": {
      "position": 1,
      "text": "Review decision: Keep summary retrieval on the local desk",
      "created_at": "2026-09-24T07:16:29Z",
      "rect": {
        "x": 256,
        "y": 359,
        "w": 928,
        "h": 44
      },
      "in_viewport": true,
      "all_owned": true
    },
    "old_brief_rows_and_triage_unchanged": true,
    "summary_receipt_and_identity_retained_after_restart": true,
    "breakage_rows": 1,
    "breakage_proof": {
      "source_ref": "pipeline-event:73136f1e-eed2-4160-926d-be9135ad01e4",
      "day_one_id": "brief-break-pipeline-brief-4c290f3ee7914654836a39df024e8cce-73136f1e-eed2-4160-926d-be9135ad01e4",
      "day_two_id": "brief-break-pipeline-brief-8a608e171ffd4a88bc5b1f0b48611b14-73136f1e-eed2-4160-926d-be9135ad01e4",
      "process_timezone": "Etc/GMT+11"
    },
    "arrival_clearance": {
      "chair": {
        "x": 240,
        "y": 54,
        "w": 960,
        "h": 794
      },
      "capture_bar": {
        "x": 256,
        "y": 843,
        "w": 928,
        "h": 74
      },
      "scroll_top": 0,
      "scroll_padding_bottom": "auto",
      "end_margin_bottom": "0px"
    },
    "initial_feedback_s": 0.932,
    "terminal_reading": "'Review decision: Keep summary retrieval on the local desk' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 256, 'y': 359, 'w': 928, 'h': 44}"
  }
]
```

### Captured run — 2026-09-24T07:17:16Z

- **Command:** `bash -c set -o pipefail; uv run --no-sync pytest -q tests/unit/test_philo4_02_decision_rows.py tests/unit/test_philo4_02_readable_rows.py tests/unit/test_philo4_03_breakage_ids.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo4_01_atlas_contracts.py 2>&1 | tee docs/internal/philo/phase-4/rows/green-python-seam.log`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 549696da704d91e91d5f6fd0038ae74ea765caca

```text
...............F........................................................ [ 78%]
....................                                                     [100%]
=================================== FAILURES ===================================
__________ test_atlas_validates_against_its_schema[atlas-phase3.json] __________

every_atlas = {'atlas_version': 'phase3-closure', 'cases': [{'applicability': 'applicable', 'completion_bound_s': 60, 'edge_ids': ['...k/db/intel.py:1215-1243 selects the claimable queued rows)', 'status': 'available', ...}], 'council_readings': [], ...}
schema = {'$defs': {'case': {'additionalProperties': False, 'allOf': [{'if': {'properties': {...}, 'required': [...]}, 'then': ...raph/atlas.schema.json', '$schema': 'https://json-schema.org/draft/2020-12/schema', 'additionalProperties': False, ...}

    def test_atlas_validates_against_its_schema(every_atlas: dict, schema: dict) -> None:
        errors = sorted(
            Draft202012Validator(schema).iter_errors(every_atlas),
            key=lambda e: list(e.absolute_path),
        )
>       assert not errors, "\n".join(
            f"{'/'.join(str(p) for p in e.absolute_path)}: {e.message}" for e in errors[:20]
        )
E       AssertionError: cases/14/setup/24: {'kind': 'api', 'method': 'GET', 'path': '/api/decisions/philo402-deliberately-absent', 'expect_status': 404, 'adapter': 'http-route', 'why': 'the real DecisionLifecycleService observer records this failed read before day-one Generate; no brief row is triaged'} is not valid under any of the given schemas
E       assert not [<ValidationError: "{'kind': 'api', 'method': 'GET', 'path': '/api/decisions/philo402-deliberately-absent', 'expect_st...ords this failed read before day-one Generate; no brief row is triaged'} is not valid under any of the given schemas">]

tests/unit/test_philo_graph_atlas.py:148: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas-phase3.json]
1 failed, 91 passed in 4.08s
```

### Captured run — 2026-09-24T07:18:06Z

- **Command:** `bash -c set -o pipefail; uv run --no-sync pytest -q tests/unit/test_philo4_02_decision_rows.py tests/unit/test_philo4_02_readable_rows.py tests/unit/test_philo4_03_breakage_ids.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo4_01_atlas_contracts.py 2>&1 | tee docs/internal/philo/phase-4/rows/green-python-final.log`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 549696da704d91e91d5f6fd0038ae74ea765caca

```text
........................................................................ [ 78%]
....................                                                     [100%]
92 passed in 3.90s
```

### Captured run — 2026-09-24T07:20:48Z

- **Command:** `bash -c set -o pipefail; cd web && npx vitest run src/desk/chair --maxWorkers=2 2>&1 | tee ../docs/internal/philo/phase-4/rows/green-rendered-final.log`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 549696da704d91e91d5f6fd0038ae74ea765caca

```text

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-4-02/web


 Test Files  14 passed (14)
      Tests  81 passed (81)
   Start at  01:20:49
   Duration  5.31s (transform 629ms, setup 567ms, import 2.41s, tests 4.12s, environment 2.39s)

npm notice
npm notice New minor version of npm available! 11.6.2 -> 11.20.0
npm notice Changelog: https://github.com/npm/cli/releases/tag/v11.20.0
npm notice To update run: npm install -g npm@11.20.0
npm notice
```

### Captured run — 2026-09-24T07:22:55Z

- **Command:** `bash -c set -o pipefail; uv run --no-sync pytest -q -s tests/e2e/test_philo4_02_generated_clearance.py 2>&1 | tee docs/internal/philo/phase-4/rows/red-clearance-final.log`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 549696da704d91e91d5f6fd0038ae74ea765caca

```text
{
  "boundary": "browser API fixture; real built Chair and Generate",
  "before": {
    "hit_test": {
      "viewport": {
        "width": 393,
        "height": 852
      },
      "rect": {
        "x": 12,
        "y": 478,
        "w": 369,
        "h": 93
      },
      "in_viewport": true,
      "samples": [
        {
          "x": 14,
          "y": 480,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 14,
          "y": 525,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 14,
          "y": 569,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 197,
          "y": 480,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 197,
          "y": 525,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 197,
          "y": 569,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 379,
          "y": 480,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 379,
          "y": 525,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 379,
          "y": 569,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        }
      ],
      "all_owned": true
    },
    "clearance": {
      "chair": {
        "x": 0,
        "y": 54,
        "w": 393,
        "h": 746
      },
      "capture_bar": {
        "x": 12,
        "y": 573,
        "w": 369,
        "h": 138
      },
      "scroll_top": 238,
      "scroll_padding_bottom": "138px",
      "end_margin_bottom": "138px"
    }
  },
  "after": {
    "hit_test": {
      "viewport": {
        "width": 393,
        "height": 852
      },
      "rect": {
        "x": 12,
        "y": 478,
        "w": 369,
        "h": 135
      },
      "in_viewport": true,
      "samples": [
        {
          "x": 14,
          "y": 480,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 14,
          "y": 546,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 14,
          "y": 611,
          "owned": false,
          "owner": "div#desk-next > div.chair > footer.arrival-capture-bar"
        },
        {
          "x": 197,
          "y": 480,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 197,
          "y": 546,
          "owned": true,
          "owner": "div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-primary"
        },
        {
          "x": 197,
          "y": 611,
          "owned": false,
          "owner": "div#desk-next > div.chair > footer.arrival-capture-bar > button.btn.btn--ghost"
        },
        {
          "x": 379,
          "y": 480,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 379,
          "y": 546,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 379,
          "y": 611,
          "owned": false,
          "owner": "div#desk-next > div.chair > footer.arrival-capture-bar"
        }
      ],
      "all_owned": false
    },
    "clearance": {
      "chair": {
        "x": 0,
        "y": 54,
        "w": 393,
        "h": 746
      },
      "capture_bar": {
        "x": 12,
        "y": 573,
        "w": 369,
        "h": 138
      },
      "scroll_top": 238,
      "scroll_padding_bottom": "138px",
      "end_margin_bottom": "138px"
    }
  }
}
F
=================================== FAILURES ===================================
______ test_generate_replacement_row_is_owned_above_the_real_capture_bar _______

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-484/test_generate_replacement_row_0')

    def test_generate_replacement_row_is_owned_above_the_real_capture_bar(
        tmp_path: Path,
    ) -> None:
        initial = _brief(
            "brief-clearance-before",
            text="Old short waiting row",
            decision=False,
        )
        generated = _brief(
            "brief-clearance-after",
            text=(
                "Review decision: Keep the generated decision readable after the "
                "capture bar wraps at the owner phone width"
            ),
            decision=True,
        )
        needs = _needs_you()
        hub = Hub(tmp_path / "home", token=TOKEN).start()
        try:
            from playwright.sync_api import sync_playwright
    
            browser_cache = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
            if not browser_cache:
                browser_cache = str(Path(pwd.getpwuid(os.getuid()).pw_dir) / "Library/Caches/ms-playwright")
                os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browser_cache
            with sync_playwright() as play:
                browser = play.chromium.launch(headless=True)
                page = browser.new_page(viewport={"width": 393, "height": 852})
                page.emulate_media(reduced_motion="reduce")
                calls = {"generate": 0}
    
                def route_payload(route: Any) -> None:
                    path = route.request.url.split("?", 1)[0].rsplit(hub.url, 1)[-1]
                    if path == "/api/brief/latest":
                        _fulfill(route, initial)
                    elif path == "/api/brief/generate":
                        calls["generate"] += 1
                        _fulfill(route, generated)
                    elif path == "/api/desk/needs-you":
                        _fulfill(route, needs)
                    elif path == "/api/door":
                        _fulfill(route, {"board": {}, "counts": {}, "upcoming": [], "calendar_configured": False})
                    elif path == "/api/inference/assignments":
                        _fulfill(route, {"schema": "InferenceAssignmentSummary@1", "rows": [], "task_overrides": [], "issue_count": 0})
                    else:
                        route.fallback()
    
                page.route("**/api/**", route_payload)
                page.goto(f"{hub.url}/?token={TOKEN}", wait_until="load")
                continue_later = page.get_by_role("button", name="Continue later", exact=True)
                try:
                    continue_later.click(timeout=10_000)
                except Exception:  # returning desk: the first-use gate is absent
                    pass
                page.get_by_test_id("arrival-capture-bar").wait_for(timeout=10_000)
                page.get_by_test_id("arrival-brief-row").wait_for()
                generate = page.get_by_test_id("arrival-brief-generate")
                generate.wait_for()
    
                before = _hit_snapshot(page)
                before_bar = page.get_by_test_id("arrival-capture-bar").bounding_box()
                assert before_bar is not None
                # Setup may leave the real Chair at a different scroll position.
                # Place the existing short row two pixels above the measured bar;
                # this is setup positioning, before Generate, never a post-click
                # scroll or a synthetic DOM row.
                page.evaluate(
                    """() => {
                      const chair = document.querySelector('[data-testid=chair]');
                      const row = document.querySelector('[data-testid=arrival-brief-row]');
                      const bar = document.querySelector('[data-testid=arrival-capture-bar]');
                      if (!chair || !row || !bar) throw new Error('clearance setup nodes missing');
                      const rowRect = row.getBoundingClientRect();
                      const barRect = bar.getBoundingClientRect();
                      chair.scrollTop += rowRect.bottom - barRect.top + 2;
                    }"""
                )
                before = _hit_snapshot(page)
                before_bar = page.get_by_test_id("arrival-capture-bar").bounding_box()
                assert before_bar is not None
                before_rect = before["hit_test"]["rect"]
                assert before_rect["y"] + before_rect["h"] <= before_bar["y"] - 1, before
                generate_box = generate.bounding_box()
                assert generate_box is not None and generate_box["y"] >= 0 and generate_box["y"] + generate_box["height"] <= 852, generate_box
    
                generate.click()
                page.get_by_text("Review decision: Keep the generated decision readable after the capture bar wraps at the owner phone width", exact=True).wait_for()
                page.wait_for_timeout(100)
                after = _hit_snapshot(page)
                after_bar = page.get_by_test_id("arrival-capture-bar").bounding_box()
                assert after_bar is not None
                assert calls["generate"] == 1
                assert after["text"] == generated["sections"]["decisions"][0]["text"] + "\nAck\nDefer"
                after_rect = after["hit_test"]["rect"]
                print(json.dumps({
                    "boundary": "browser API fixture; real built Chair and Generate",
                    "before": {"hit_test": before["hit_test"], "clearance": before["arrival_clearance"]},
                    "after": {"hit_test": after["hit_test"], "clearance": after["arrival_clearance"]},
                }, indent=2))
                # Project the replacement's real rendered height at the old row's
                # position. It must cross the real bar; the final observed row may
                # be higher because the product's success seam clears it.
                assert before_rect["y"] + after_rect["h"] > before_bar["y"], {
                    "before": before,
                    "after": after,
                }
                assert after_rect["w"] > 0 and after_rect["h"] > 0, after
                assert after["hit_test"]["in_viewport"] is True, after
>               assert after["hit_test"]["all_owned"] is True, after
E               AssertionError: {'arrival_clearance': {'capture_bar': {'h': 138, 'w': 369, 'x': 12, 'y': 573}, 'chair': {'h': 746, 'w': 393, 'x': 0, '...ALK
E                 Write a thought
E                 Record meeting
E                 Schedule
E                 ◈
E                 3
E                 ◎
E                 ▤
E                 ⧉
E                 ◌
E                 Hide the menus
E                 ▧
E                 Places', 'field_value': None, ...}
E               assert False is True

tests/e2e/test_philo4_02_generated_clearance.py:229: AssertionError
=========================== short test summary info ============================
FAILED tests/e2e/test_philo4_02_generated_clearance.py::test_generate_replacement_row_is_owned_above_the_real_capture_bar
1 failed in 5.68s
```

### Captured run — 2026-09-24T07:23:49Z

- **Command:** `bash -c set -o pipefail; cd .tmp/philo402-main && uv run --no-sync pytest -q -s tests/e2e/test_philo4_02_generated_clearance.py 2>&1 | tee ../../docs/internal/philo/phase-4/rows/red-clearance-main.log`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 549696da704d91e91d5f6fd0038ae74ea765caca

```text
[glass_infra] web bundle rebuilt in 4.8s
{
  "boundary": "browser API fixture; real built Chair and Generate",
  "before": {
    "hit_test": {
      "viewport": {
        "width": 393,
        "height": 852
      },
      "rect": {
        "x": 12,
        "y": 478,
        "w": 369,
        "h": 93
      },
      "in_viewport": true,
      "samples": [
        {
          "x": 14,
          "y": 480,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 14,
          "y": 525,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 14,
          "y": 569,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 197,
          "y": 480,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 197,
          "y": 525,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 197,
          "y": 569,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 379,
          "y": 480,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 379,
          "y": 525,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 379,
          "y": 569,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        }
      ],
      "all_owned": true
    },
    "clearance": null
  },
  "after": {
    "hit_test": {
      "viewport": {
        "width": 393,
        "height": 852
      },
      "rect": {
        "x": 12,
        "y": 478,
        "w": 369,
        "h": 135
      },
      "in_viewport": true,
      "samples": [
        {
          "x": 14,
          "y": 480,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 14,
          "y": 546,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 14,
          "y": 611,
          "owned": false,
          "owner": "div#desk-next > div.chair > footer.arrival-capture-bar"
        },
        {
          "x": 197,
          "y": 480,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 197,
          "y": 546,
          "owned": true,
          "owner": "div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-primary"
        },
        {
          "x": 197,
          "y": 611,
          "owned": false,
          "owner": "div#desk-next > div.chair > footer.arrival-capture-bar > button.btn.btn--ghost"
        },
        {
          "x": 379,
          "y": 480,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 379,
          "y": 546,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 379,
          "y": 611,
          "owned": false,
          "owner": "div#desk-next > div.chair > footer.arrival-capture-bar"
        }
      ],
      "all_owned": false
    },
    "clearance": null
  }
}
F
=================================== FAILURES ===================================
______ test_generate_replacement_row_is_owned_above_the_real_capture_bar _______

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-485/test_generate_replacement_row_0')

    def test_generate_replacement_row_is_owned_above_the_real_capture_bar(
        tmp_path: Path,
    ) -> None:
        initial = _brief(
            "brief-clearance-before",
            text="Old short waiting row",
            decision=False,
        )
        generated = _brief(
            "brief-clearance-after",
            text=(
                "Review decision: Keep the generated decision readable after the "
                "capture bar wraps at the owner phone width"
            ),
            decision=True,
        )
        needs = _needs_you()
        hub = Hub(tmp_path / "home", token=TOKEN).start()
        try:
            from playwright.sync_api import sync_playwright
    
            browser_cache = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
            if not browser_cache:
                browser_cache = str(Path(pwd.getpwuid(os.getuid()).pw_dir) / "Library/Caches/ms-playwright")
                os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browser_cache
            with sync_playwright() as play:
                browser = play.chromium.launch(headless=True)
                page = browser.new_page(viewport={"width": 393, "height": 852})
                page.emulate_media(reduced_motion="reduce")
                calls = {"generate": 0}
    
                def route_payload(route: Any) -> None:
                    path = route.request.url.split("?", 1)[0].rsplit(hub.url, 1)[-1]
                    if path == "/api/brief/latest":
                        _fulfill(route, initial)
                    elif path == "/api/brief/generate":
                        calls["generate"] += 1
                        _fulfill(route, generated)
                    elif path == "/api/desk/needs-you":
                        _fulfill(route, needs)
                    elif path == "/api/door":
                        _fulfill(route, {"board": {}, "counts": {}, "upcoming": [], "calendar_configured": False})
                    elif path == "/api/inference/assignments":
                        _fulfill(route, {"schema": "InferenceAssignmentSummary@1", "rows": [], "task_overrides": [], "issue_count": 0})
                    else:
                        route.fallback()
    
                page.route("**/api/**", route_payload)
                page.goto(f"{hub.url}/?token={TOKEN}", wait_until="load")
                continue_later = page.get_by_role("button", name="Continue later", exact=True)
                try:
                    continue_later.click(timeout=10_000)
                except Exception:  # returning desk: the first-use gate is absent
                    pass
                page.get_by_test_id("arrival-capture-bar").wait_for(timeout=10_000)
                page.get_by_test_id("arrival-brief-row").wait_for()
                generate = page.get_by_test_id("arrival-brief-generate")
                generate.wait_for()
    
                before = _hit_snapshot(page)
                before_bar = page.get_by_test_id("arrival-capture-bar").bounding_box()
                assert before_bar is not None
                # Setup may leave the real Chair at a different scroll position.
                # Place the existing short row two pixels above the measured bar;
                # this is setup positioning, before Generate, never a post-click
                # scroll or a synthetic DOM row.
                page.evaluate(
                    """() => {
                      const chair = document.querySelector('[data-testid=chair]');
                      const row = document.querySelector('[data-testid=arrival-brief-row]');
                      const bar = document.querySelector('[data-testid=arrival-capture-bar]');
                      if (!chair || !row || !bar) throw new Error('clearance setup nodes missing');
                      const rowRect = row.getBoundingClientRect();
                      const barRect = bar.getBoundingClientRect();
                      chair.scrollTop += rowRect.bottom - barRect.top + 2;
                    }"""
                )
                before = _hit_snapshot(page)
                before_bar = page.get_by_test_id("arrival-capture-bar").bounding_box()
                assert before_bar is not None
                before_rect = before["hit_test"]["rect"]
                assert before_rect["y"] + before_rect["h"] <= before_bar["y"] - 1, before
                generate_box = generate.bounding_box()
                assert generate_box is not None and generate_box["y"] >= 0 and generate_box["y"] + generate_box["height"] <= 852, generate_box
    
                generate.click()
                page.get_by_text("Review decision: Keep the generated decision readable after the capture bar wraps at the owner phone width", exact=True).wait_for()
                page.wait_for_timeout(100)
                after = _hit_snapshot(page)
                after_bar = page.get_by_test_id("arrival-capture-bar").bounding_box()
                assert after_bar is not None
                assert calls["generate"] == 1
                assert after["text"] == generated["sections"]["decisions"][0]["text"] + "\nAck\nDefer"
                after_rect = after["hit_test"]["rect"]
                print(json.dumps({
                    "boundary": "browser API fixture; real built Chair and Generate",
                    "before": {"hit_test": before["hit_test"], "clearance": before.get("arrival_clearance")},
                    "after": {"hit_test": after["hit_test"], "clearance": after.get("arrival_clearance")},
                }, indent=2))
                # Project the replacement's real rendered height at the old row's
                # position. It must cross the real bar; the final observed row may
                # be higher because the product's success seam clears it.
                assert before_rect["y"] + after_rect["h"] > before_bar["y"], {
                    "before": before,
                    "after": after,
                }
                assert after_rect["w"] > 0 and after_rect["h"] > 0, after
                assert after["hit_test"]["in_viewport"] is True, after
>               assert after["hit_test"]["all_owned"] is True, after
E               AssertionError: {'attrs': {'class': 'surface-ledger-line', 'data-has-trailing': 'true', 'data-testid': 'arrival-brief-row', 'role': 'b...ght
E                 Record meeting
E                 Schedule
E                 ◈
E                 3
E                 ◎
E                 ▤
E                 ⧉
E                 ◌
E                 Hide the menus
E                 ▧
E                 Places', 'field_value': None, 'focus': 'body', ...}
E               assert False is True

tests/e2e/test_philo4_02_generated_clearance.py:229: AssertionError
=========================== short test summary info ============================
FAILED tests/e2e/test_philo4_02_generated_clearance.py::test_generate_replacement_row_is_owned_above_the_real_capture_bar
1 failed in 18.05s
```

### Captured run — 2026-09-24T07:24:26Z

- **Command:** `bash -c set -o pipefail; uv run --no-sync pytest --collect-only -q tests/e2e/test_philo4_02_generated_clearance.py 2>&1 | tee docs/internal/philo/phase-4/rows/collect-clearance.log && uv run --no-sync pytest -q -s tests/e2e/test_philo4_02_generated_clearance.py 2>&1 | tee docs/internal/philo/phase-4/rows/green-clearance.log`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 549696da704d91e91d5f6fd0038ae74ea765caca

```text
tests/e2e/test_philo4_02_generated_clearance.py::test_generate_replacement_row_is_owned_above_the_real_capture_bar

1 test collected in 0.03s
[glass_infra] web bundle rebuilt in 4.5s
{
  "boundary": "browser API fixture; real built Chair and Generate",
  "before": {
    "hit_test": {
      "viewport": {
        "width": 393,
        "height": 852
      },
      "rect": {
        "x": 12,
        "y": 478,
        "w": 369,
        "h": 93
      },
      "in_viewport": true,
      "samples": [
        {
          "x": 14,
          "y": 480,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 14,
          "y": 525,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 14,
          "y": 569,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 197,
          "y": 480,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 197,
          "y": 525,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 197,
          "y": 569,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 379,
          "y": 480,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 379,
          "y": 525,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 379,
          "y": 569,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        }
      ],
      "all_owned": true
    },
    "clearance": {
      "chair": {
        "x": 0,
        "y": 54,
        "w": 393,
        "h": 746
      },
      "capture_bar": {
        "x": 12,
        "y": 573,
        "w": 369,
        "h": 138
      },
      "scroll_top": 238,
      "scroll_padding_bottom": "227px",
      "end_margin_bottom": "138px"
    }
  },
  "after": {
    "hit_test": {
      "viewport": {
        "width": 393,
        "height": 852
      },
      "rect": {
        "x": 12,
        "y": 438,
        "w": 369,
        "h": 135
      },
      "in_viewport": true,
      "samples": [
        {
          "x": 14,
          "y": 440,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 14,
          "y": 506,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 14,
          "y": 571,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 197,
          "y": 440,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 197,
          "y": 506,
          "owned": true,
          "owner": "div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line > span.surface-ledger-primary"
        },
        {
          "x": 197,
          "y": 571,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 379,
          "y": 440,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 379,
          "y": 506,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        },
        {
          "x": 379,
          "y": 571,
          "owned": true,
          "owner": "div.chair > div > section.surface-section > div.surface-ledger > li.surface-ledger-row > div.surface-ledger-line"
        }
      ],
      "all_owned": true
    },
    "clearance": {
      "chair": {
        "x": 0,
        "y": 54,
        "w": 393,
        "h": 746
      },
      "capture_bar": {
        "x": 12,
        "y": 573,
        "w": 369,
        "h": 138
      },
      "scroll_top": 278,
      "scroll_padding_bottom": "227px",
      "end_margin_bottom": "138px"
    }
  }
}
.
1 passed in 10.23s
```

### Captured run — 2026-09-24T07:25:14Z

- **Command:** `bash -c set -o pipefail; uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.closure.chain.s5_next_day_brief_has_it --brain astra --viewport 393 --engine real --no-build --out pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/ 2>&1 | tee docs/internal/philo/phase-4/rows/rig-393-final.log`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 549696da704d91e91d5f6fd0038ae74ea765caca

```text
PASS: live
BRAIN: astra
SOURCE: 566495b076f8db7387f7e050be30d8065ee8841b dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-Y37FyLq1.js'] hub=http://127.0.0.1:53099 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-5vptmjpa/.local/share/holdspeak/holdspeak.db engine=real
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/20260924T072514Z-case.closure.chain.s5_next_day_brief_has_it-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/20260924T072514Z-case.closure.chain.s5_next_day_brief_has_it-astra-393/after.png']
NOTE: predicate: 'Review decision: Keep summary retrieval on the local desk' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 12, 'y': 356, 'w': 369, 'h': 114}
```

### Captured run — 2026-09-24T07:26:14Z

- **Command:** `bash -c set -o pipefail; uv run --no-sync python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.closure.chain.s5_next_day_brief_has_it --brain astra --viewport 1440 --engine real --no-build --out pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/ 2>&1 | tee docs/internal/philo/phase-4/rows/rig-1440-final.log`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 549696da704d91e91d5f6fd0038ae74ea765caca

```text
PASS: live
BRAIN: astra
SOURCE: 566495b076f8db7387f7e050be30d8065ee8841b dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-Y37FyLq1.js'] hub=http://127.0.0.1:53209 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-tg0_w5uk/.local/share/holdspeak/holdspeak.db engine=real
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/20260924T072614Z-case.closure.chain.s5_next_day_brief_has_it-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/20260924T072614Z-case.closure.chain.s5_next_day_brief_has_it-astra-1440/after.png']
NOTE: predicate: 'Review decision: Keep summary retrieval on the local desk' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 256, 'y': 359, 'w': 928, 'h': 44}
```

### Captured run — 2026-09-24T07:27:22Z

- **Command:** `bash -c set -o pipefail; uv run --no-sync python docs/internal/philo/phase-4/rows/run_breakage_case.py 393 2>&1 | tee docs/internal/philo/phase-4/rows/rig-breakage-393-final.log`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 549696da704d91e91d5f6fd0038ae74ea765caca

```text
BREAKAGE_WINDOW TZ=Etc/GMT+11 local=2026-09-23T20:27:22.674738 after_close=True
PASS: live
BRAIN: astra
SOURCE: 566495b076f8db7387f7e050be30d8065ee8841b dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-Y37FyLq1.js'] hub=http://127.0.0.1:53316 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-3h5milzx/.local/share/holdspeak/holdspeak.db engine=real
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/20260924T072722Z-case.closure.chain.s5_next_day_brief_with_breakage-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/20260924T072722Z-case.closure.chain.s5_next_day_brief_with_breakage-astra-393/after.png']
NOTE: predicate: 'Review decision: Keep summary retrieval on the local desk' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 12, 'y': 356, 'w': 369, 'h': 114}
```

### Captured run — 2026-09-24T07:28:14Z

- **Command:** `bash -c set -o pipefail; uv run --no-sync python docs/internal/philo/phase-4/rows/run_breakage_case.py 1440 2>&1 | tee docs/internal/philo/phase-4/rows/rig-breakage-1440-final.log`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 549696da704d91e91d5f6fd0038ae74ea765caca

```text
BREAKAGE_WINDOW TZ=Etc/GMT+11 local=2026-09-23T20:28:14.373111 after_close=True
PASS: live
BRAIN: astra
SOURCE: 566495b076f8db7387f7e050be30d8065ee8841b dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-Y37FyLq1.js'] hub=http://127.0.0.1:53427 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-3ld0im09/.local/share/holdspeak/holdspeak.db engine=real
JOB: j10
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/20260924T072814Z-case.closure.chain.s5_next_day_brief_with_breakage-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/20260924T072814Z-case.closure.chain.s5_next_day_brief_with_breakage-astra-1440/after.png']
NOTE: predicate: 'Review decision: Keep summary retrieval on the local desk' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 256, 'y': 404, 'w': 928, 'h': 44}
```

### Captured run — 2026-09-24T07:29:32Z

- **Command:** `bash -c set -o pipefail; uv run --no-sync python docs/internal/philo/phase-4/rows/verify_closure.py pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/20260924T072614Z-case.closure.chain.s5_next_day_brief_has_it-astra-1440/observation.json pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/20260924T072514Z-case.closure.chain.s5_next_day_brief_has_it-astra-393/observation.json pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/20260924T072814Z-case.closure.chain.s5_next_day_brief_with_breakage-astra-1440/observation.json pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/20260924T072722Z-case.closure.chain.s5_next_day_brief_with_breakage-astra-393/observation.json 2>&1 | tee docs/internal/philo/phase-4/rows/closure-proof.json`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 549696da704d91e91d5f6fd0038ae74ea765caca

```text
[
  {
    "run_id": "20260924T072614Z-case.closure.chain.s5_next_day_brief_has_it-astra-1440",
    "viewport": 1440,
    "verdict": "PASS",
    "first_brief": {
      "id": "brief-2e40a2cd92f94442995a65a8e6f53dab",
      "generated_at": "2026-09-24T01:26:44.421123",
      "items": 3,
      "shelf": {}
    },
    "new_brief": {
      "id": "brief-fdfa8486f80e496e857b4fd271c89ca0",
      "generated_at": "2026-09-25T01:26:46.453430"
    },
    "decision": {
      "position": 1,
      "text": "Review decision: Keep summary retrieval on the local desk",
      "created_at": "2026-09-24T07:26:44Z",
      "rect": {
        "x": 256,
        "y": 359,
        "w": 928,
        "h": 44
      },
      "in_viewport": true,
      "all_owned": true
    },
    "old_brief_rows_and_triage_unchanged": true,
    "summary_receipt_and_identity_retained_after_restart": true,
    "breakage_rows": 0,
    "breakage_proof": null,
    "arrival_clearance": {
      "chair": {
        "x": 240,
        "y": 54,
        "w": 960,
        "h": 794
      },
      "capture_bar": {
        "x": 256,
        "y": 813,
        "w": 928,
        "h": 74
      },
      "scroll_top": 0,
      "scroll_padding_bottom": "auto",
      "end_margin_bottom": "0px"
    },
    "initial_feedback_s": 0.937,
    "terminal_reading": "'Review decision: Keep summary retrieval on the local desk' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 256, 'y': 359, 'w': 928, 'h': 44}"
  },
  {
    "run_id": "20260924T072514Z-case.closure.chain.s5_next_day_brief_has_it-astra-393",
    "viewport": 393,
    "verdict": "PASS",
    "first_brief": {
      "id": "brief-fda6f8beba7d487598e82a12ee4f97e9",
      "generated_at": "2026-09-24T01:25:44.083456",
      "items": 4,
      "shelf": {}
    },
    "new_brief": {
      "id": "brief-9ac61fa65b91416192f7dc0ce2341b3b",
      "generated_at": "2026-09-25T01:25:46.842293"
    },
    "decision": {
      "position": 1,
      "text": "Review decision: Keep summary retrieval on the local desk",
      "created_at": "2026-09-24T07:25:44Z",
      "rect": {
        "x": 12,
        "y": 356,
        "w": 369,
        "h": 114
      },
      "in_viewport": true,
      "all_owned": true
    },
    "old_brief_rows_and_triage_unchanged": true,
    "summary_receipt_and_identity_retained_after_restart": true,
    "breakage_rows": 0,
    "breakage_proof": null,
    "arrival_clearance": {
      "chair": {
        "x": 0,
        "y": 54,
        "w": 393,
        "h": 746
      },
      "capture_bar": {
        "x": 12,
        "y": 573,
        "w": 369,
        "h": 138
      },
      "scroll_top": 417,
      "scroll_padding_bottom": "227px",
      "end_margin_bottom": "138px"
    },
    "initial_feedback_s": 0.934,
    "terminal_reading": "'Review decision: Keep summary retrieval on the local desk' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 12, 'y': 356, 'w': 369, 'h': 114}"
  },
  {
    "run_id": "20260924T072814Z-case.closure.chain.s5_next_day_brief_with_breakage-astra-1440",
    "viewport": 1440,
    "verdict": "PASS",
    "first_brief": {
      "id": "brief-02a9983f65684502b757a5d3150d452c",
      "generated_at": "2026-09-23T20:28:43.769923",
      "items": 5,
      "shelf": {}
    },
    "new_brief": {
      "id": "brief-532f80b9696a49acb2a2fdb45139e636",
      "generated_at": "2026-09-24T20:28:45.820253"
    },
    "decision": {
      "position": 1,
      "text": "Review decision: Keep summary retrieval on the local desk",
      "created_at": "2026-09-24T07:28:43Z",
      "rect": {
        "x": 256,
        "y": 404,
        "w": 928,
        "h": 44
      },
      "in_viewport": true,
      "all_owned": true
    },
    "old_brief_rows_and_triage_unchanged": true,
    "summary_receipt_and_identity_retained_after_restart": true,
    "breakage_rows": 1,
    "breakage_proof": {
      "source_ref": "pipeline-event:66de0ed3-55ca-46f8-adce-2047e48fb93f",
      "day_one_id": "brief-break-pipeline-brief-02a9983f65684502b757a5d3150d452c-66de0ed3-55ca-46f8-adce-2047e48fb93f",
      "day_two_id": "brief-break-pipeline-brief-532f80b9696a49acb2a2fdb45139e636-66de0ed3-55ca-46f8-adce-2047e48fb93f",
      "process_timezone": "Etc/GMT+11"
    },
    "arrival_clearance": {
      "chair": {
        "x": 240,
        "y": 54,
        "w": 960,
        "h": 794
      },
      "capture_bar": {
        "x": 256,
        "y": 888,
        "w": 928,
        "h": 74
      },
      "scroll_top": 0,
      "scroll_padding_bottom": "auto",
      "end_margin_bottom": "0px"
    },
    "initial_feedback_s": 0.936,
    "terminal_reading": "'Review decision: Keep summary retrieval on the local desk' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 256, 'y': 404, 'w': 928, 'h': 44}"
  },
  {
    "run_id": "20260924T072722Z-case.closure.chain.s5_next_day_brief_with_breakage-astra-393",
    "viewport": 393,
    "verdict": "PASS",
    "first_brief": {
      "id": "brief-8f8a48f29dc343d78601652192edd9ee",
      "generated_at": "2026-09-23T20:27:54.618743",
      "items": 4,
      "shelf": {}
    },
    "new_brief": {
      "id": "brief-aea12b5190c741e18ca341a1102aa35a",
      "generated_at": "2026-09-24T20:27:57.078526"
    },
    "decision": {
      "position": 1,
      "text": "Review decision: Keep summary retrieval on the local desk",
      "created_at": "2026-09-24T07:27:54Z",
      "rect": {
        "x": 12,
        "y": 356,
        "w": 369,
        "h": 114
      },
      "in_viewport": true,
      "all_owned": true
    },
    "old_brief_rows_and_triage_unchanged": true,
    "summary_receipt_and_identity_retained_after_restart": true,
    "breakage_rows": 1,
    "breakage_proof": {
      "source_ref": "pipeline-event:f657cab6-addb-4c1c-bd37-d560a887615d",
      "day_one_id": "brief-break-pipeline-brief-8f8a48f29dc343d78601652192edd9ee-f657cab6-addb-4c1c-bd37-d560a887615d",
      "day_two_id": "brief-break-pipeline-brief-aea12b5190c741e18ca341a1102aa35a-f657cab6-addb-4c1c-bd37-d560a887615d",
      "process_timezone": "Etc/GMT+11"
    },
    "arrival_clearance": {
      "chair": {
        "x": 0,
        "y": 54,
        "w": 393,
        "h": 746
      },
      "capture_bar": {
        "x": 12,
        "y": 573,
        "w": 369,
        "h": 138
      },
      "scroll_top": 297,
      "scroll_padding_bottom": "227px",
      "end_margin_bottom": "138px"
    },
    "initial_feedback_s": 0.942,
    "terminal_reading": "'Review decision: Keep summary retrieval on the local desk' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 12, 'y': 356, 'w': 369, 'h': 114}"
  }
]
```

### Captured run — 2026-09-24T07:31:43Z

- **Command:** `bash -c set -o pipefail; { python3 scripts/philo_graph_reference.py --check && git diff --check && if git status --short | grep "^ M" | grep pm/roadmap/holdspeak/; then exit 1; else printf "PASS: no modified evidence paths under pm/roadmap/holdspeak/\n"; fi; } 2>&1 | tee docs/internal/philo/phase-4/rows/final-integrity.log`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 549696da704d91e91d5f6fd0038ae74ea765caca

```text
note: subtype conflict edge.cli.hub_restart: astra=process.restart; muaddib=cli
note: subtype conflict edge.face.arrival_load: astra=lifecycle.mount; muaddib=navigation.load
note: subtype conflict edge.face.thought_keep: astra=pointer.blur; muaddib=pointer.click
note: subtype conflict edge.route.brief_item_shelf: astra=ui; muaddib=http
note: subtype conflict edge.route.brief_latest: astra=ui; muaddib=http
note: subtype conflict edge.route.heartbeat_run_now: astra=ui; muaddib=http
note: subtype conflict edge.route.inference_assignments_set: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_delete: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_unbind: astra=ui; muaddib=http
note: subtype conflict edge.route.projection_presentation: astra=ui; muaddib=http
note: subtype conflict edge.route.projections_list: astra=ui; muaddib=http
note: subtype conflict edge.timer.heartbeat_sweep: astra=ui; muaddib=timer
note: subtype conflict iface.face.arrival: astra=face.section; muaddib=face.window
note: subtype conflict iface.face.first_words: astra=face.card; muaddib=face.panel
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
PASS: no modified evidence paths under pm/roadmap/holdspeak/
```

### Captured run — 2026-09-24T07:36:00Z

- **Command:** `bash -c set -o pipefail; { python3 scripts/philo_repository_census.py && python3 scripts/philo_repository_census.py --check; } 2>&1 | tee docs/internal/philo/phase-4/rows/census-pinned.log`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 549696da704d91e91d5f6fd0038ae74ea765caca

```text
Repository census: 5 outputs written.
Repository census: 5 outputs verified.
```

### Captured run — 2026-09-24T07:37:17Z

- **Command:** `bash -c set -o pipefail; { python3 scripts/philo_boundary_census.py && python3 scripts/philo_boundary_census.py --check && python3 scripts/philo_graph_reference.py --check; } 2>&1 | tee docs/internal/philo/phase-4/rows/final-census.log`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 549696da704d91e91d5f6fd0038ae74ea765caca

```text
Boundary candidate census generated
Boundary candidate census checked
note: subtype conflict edge.cli.hub_restart: astra=process.restart; muaddib=cli
note: subtype conflict edge.face.arrival_load: astra=lifecycle.mount; muaddib=navigation.load
note: subtype conflict edge.face.thought_keep: astra=pointer.blur; muaddib=pointer.click
note: subtype conflict edge.route.brief_item_shelf: astra=ui; muaddib=http
note: subtype conflict edge.route.brief_latest: astra=ui; muaddib=http
note: subtype conflict edge.route.heartbeat_run_now: astra=ui; muaddib=http
note: subtype conflict edge.route.inference_assignments_set: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_delete: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_unbind: astra=ui; muaddib=http
note: subtype conflict edge.route.projection_presentation: astra=ui; muaddib=http
note: subtype conflict edge.route.projections_list: astra=ui; muaddib=http
note: subtype conflict edge.timer.heartbeat_sweep: astra=ui; muaddib=timer
note: subtype conflict iface.face.arrival: astra=face.section; muaddib=face.window
note: subtype conflict iface.face.first_words: astra=face.card; muaddib=face.panel
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
```

### Captured run — 2026-09-24T07:41:21Z

- **Command:** `bash -c set -o pipefail; { uv run --no-sync python scripts/check_docs.py docs/internal/philo/phase-4/rows/README.md docs/internal/philo/phase-4/rows/lane-report.md pm/roadmap/holdspeak-philo/README.md pm/roadmap/holdspeak-philo/phase-4-the-morning/current-phase-status.md pm/roadmap/holdspeak-philo/phase-4-the-morning/story-02-decision-in-the-visible-rows.md pm/roadmap/holdspeak-philo/phase-4-the-morning/checks/rows-built-muaddib.md && python3 scripts/philo_graph_reference.py --check && python3 scripts/philo_boundary_census.py --check && .githooks/dw check holdspeak-philo && git diff --check && if git status --short | grep "^ M" | grep pm/roadmap/holdspeak/; then exit 1; else printf "PASS: no modified evidence paths under pm/roadmap/holdspeak/\n"; fi; } 2>&1 | tee docs/internal/philo/phase-4/rows/ship-checks.log`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 549696da704d91e91d5f6fd0038ae74ea765caca

```text
Documentation navigation: 6 files checked; local targets and Markdown headings resolve.
note: subtype conflict edge.cli.hub_restart: astra=process.restart; muaddib=cli
note: subtype conflict edge.face.arrival_load: astra=lifecycle.mount; muaddib=navigation.load
note: subtype conflict edge.face.thought_keep: astra=pointer.blur; muaddib=pointer.click
note: subtype conflict edge.route.brief_item_shelf: astra=ui; muaddib=http
note: subtype conflict edge.route.brief_latest: astra=ui; muaddib=http
note: subtype conflict edge.route.heartbeat_run_now: astra=ui; muaddib=http
note: subtype conflict edge.route.inference_assignments_set: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_delete: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_unbind: astra=ui; muaddib=http
note: subtype conflict edge.route.projection_presentation: astra=ui; muaddib=http
note: subtype conflict edge.route.projections_list: astra=ui; muaddib=http
note: subtype conflict edge.timer.heartbeat_sweep: astra=ui; muaddib=timer
note: subtype conflict iface.face.arrival: astra=face.section; muaddib=face.window
note: subtype conflict iface.face.first_words: astra=face.card; muaddib=face.panel
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
Boundary candidate census checked
dw check: ok
PASS: no modified evidence paths under pm/roadmap/holdspeak/
```
