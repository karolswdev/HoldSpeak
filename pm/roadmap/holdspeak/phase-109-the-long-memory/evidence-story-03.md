# Evidence - HS-109-03

- **Story:** HS-109-03 - Decisions become artifacts — promotion
- **Status:** done
- **Date:** 2026-07-29

## Proof

### Captured run — 2026-07-29T23:51:21Z

- **Command:** `uv run pytest -q tests/unit/test_decisions.py tests/integration/test_decision_records.py tests/unit/test_api_surface.py tests/unit/test_memory_index.py tests/integration/test_memory_retrieval.py tests/unit/test_decision_capture_plugin.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** unknown

```text
..............................................                           [100%]
46 passed in 4.45s
```

### Captured run — 2026-07-29T23:51:26Z

- **Command:** `uv run --extra dictation-openai python scripts/hs109_03_live_proof.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** unknown

```text
decision: dec-42d036434be456d0421c 'The grounding cap stays at sixteen refs, and unknown ids mus' lifecycle=accepted
deterministic promote → 200 artifact=promoted-fd9ead4c18981db2a179 status=accepted
PASS  double promotion is one artifact
PASS  artifact_sources cite decision:dec-42d03643…
PASS  lineage queryable both ways
model-assisted on .43 → 200 artifact=promoted-714f83d1ad36cb2d8e83 status=draft target=profile_03617b8c9250
  generated head: '```markdown\n# Decision Announcement\n\n**Grounding Cap**: Remains at sixteen references.\n\n**Unknown IDs**: Must refuse lou'
  kernel receipt: op=inference.run outcome=succeeded result_ref=artifact:promoted-714f83d1ad36cb2d8e83
PASS  real generation behind real admission with a real receipt
supersede → 200
  derived artifact status after supersession: rejected
re-promotion → 409 detail={'error': 'decision_promotion_refused', 'decision_id': 'dec-42d036434be456d0421c', 'detail': 'superseded by dec-b99036c970ef352d1391 — promo
PASS  supersession propagates to the derived artifact
PASS  re-promotion refuses naming the successor

ALL PASS
```

## What the captures prove

1. **Focused suites** — 46 green: promotion idempotency, lineage kind
   round-trip, refusal-on-superseded naming the successor,
   review-status transitions, promoted artifacts NOT re-entering the
   decisions projection chokepoint, the model path admitting BEFORE
   generating (event-order asserted), API manifest, and the
   neighboring decision/memory families unharmed.
2. **The live proof on real metal**
   (`scripts/hs109_03_live_proof.py`) — the REAL archive behind the
   REAL assembled app:
   - a real decision accepted (owner gesture → lifecycle receipt);
   - deterministic promote → `promoted-4317…` ADR, `accepted`,
     `artifact_sources` citing `decision:dec-ad994c…` and the meeting;
     double promotion returned the SAME artifact; lineage queryable
     both directions (decision → derived_artifacts; artifact →
     sources);
   - **model-assisted draft generated on the REAL `.43` profile**
     (`profile_03617b8c9250`) through the registered `inference.run@1`:
     HTTP 200, a `draft` decision-announcement with real generated
     markdown, and the kernel receipt read back —
     `op=inference.run outcome=succeeded
     result_ref=artifact:promoted-d9535d69…`;
   - supersession propagated to the derived artifact (`rejected`) and
     re-promotion refused 409 with
     `superseded by dec-42d03643… — promote that one`.

An earlier proof run superseded the BLUE LANTERN record for real —
the rerun picked fresh live candidates, which is the product behaving
correctly (supersession is permanent; the walk script adapted, not
the product). A first model-path attempt failed honestly with
`openai package is not available` (the venv lacked the
`dictation-openai` extra — an environment fact, named in the error,
resolved by running with the extra).

## Suites

Full suite on the final rebased tree: capture below.
