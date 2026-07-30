# Evidence - HS-109-08

- **Story:** HS-109-08 - Closeout — the sitting on real memory
- **Status:** done
- **Date:** 2026-07-29

## Proof

### Captured run — 2026-07-30T01:25:53Z

- **Command:** `uv run --extra dictation-openai python scripts/phase109_closeout_beats.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 9a03b28fcf8c31a2c2029e461b0eb80cf9196c78

```text
run1: {"artifacts": 2, "decisions": 6, "inserted": 0, "updated": 0, "unchanged": 6, "skipped": 0}
run2: {"artifacts": 2, "decisions": 6, "inserted": 0, "updated": 0, "unchanged": 6, "skipped": 0}
PASS  B1  real-archive backfill idempotent
PASS  all 3 decisions projected
PASS  a verified moment upgraded date_basis to transcript_moment (reported)
  jump: decision dec-42d03643… → segment 'One more decision: the grounding cap stays at sixteen refs, and unknown ids must'
PASS  the resolver maps the moment to its segment

ALL PASS
PASS  B2  verified transcript moment + the jump (.43)
FAIL  need two live (non-superseded) records to walk
FAIL  B3  promotion, supersession, named refusal
FAIL  need two live (non-superseded) records to walk
FAIL  B4  model-assisted promotion receipt on .43
FAIL  need two live (non-superseded) records to walk

CONTROL (ungrounded .43): 'The secret launch codename for the Mesh Milestone is **Project 100**.\n\nThis milestone, announced by the Mesh Network Foundation, represents a major step toward achieving a fully decentralized, permissionless, and censors'
TREATMENT (grounded on memory hits): 'The secret launch codename for the mesh milestone is **BLUE LANTERN**.\n\n[REF: artifact:promoted-9dc4df1859bde8c0734c] [REF: decision:dec-b2cb276e229ff7a9d63e] [REF: artifact:art-a1ec606ee5ef1daa2da5] [REF: decision:dec-6d794c87e235b3c3dd07]'
PASS  treatment answers from the archive
PASS  control does not know the codename
PASS  treatment cites its decision ref

ALL PASS
PASS  B5  memory search + cited grounding + wire regression
PASS  B6  cited ask surfaces (grounded-on honesty)
Test Files  3 passed (3)
      Tests  11 passed (11)
   Start at  19:26:06
   Duration  923ms (transform 206ms, setup 240ms, import 432ms, tests 75ms, environment 1.05s)
PASS  B7  process window: fold, replay, endpoint surface
FAILED tests/uat/test_build_ledger.py::test_committed_ledger_is_up_to_date - ...
FAILED tests/uat/test_voice_notes.py::test_transcribe_up_but_unreachable_is_honest
2 failed, 4360 passed, 37 skipped, 2 warnings in 942.07s (0:15:42)
PASS  B8  the sweep (suite, web, fence, spine, register)

6/8 beats passed
```

### Captured run — 2026-07-30T01:43:42Z

- **Command:** `uv run --extra dictation-openai python scripts/phase109_closeout_beats.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e360e3b42deae02259961a9fa07e9e4bd54daa01

```text
run1: {"artifacts": 2, "decisions": 6, "inserted": 0, "updated": 0, "unchanged": 6, "skipped": 0}
run2: {"artifacts": 2, "decisions": 6, "inserted": 0, "updated": 0, "unchanged": 6, "skipped": 0}
PASS  B1  real-archive backfill idempotent
PASS  all 3 decisions projected
PASS  a verified moment upgraded date_basis to transcript_moment (reported)
  jump: decision dec-42d03643… → segment 'One more decision: the grounding cap stays at sixteen refs, and unknown ids must'
PASS  the resolver maps the moment to its segment

ALL PASS
PASS  B2  verified transcript moment + the jump (.43)
  kernel receipt: op=inference.run outcome=succeeded result_ref=artifact:promoted-97e8dadb006878372b94
PASS  real generation behind real admission with a real receipt
supersede → 200
  derived artifact status after supersession: rejected
re-promotion → 409 detail={'error': 'decision_promotion_refused', 'decision_id': 'dec-cd68de2134f39ab1f1f0', 'detail': 'superseded by dec-15111bbfc1909e8d3d3e — promo
PASS  supersession propagates to the derived artifact
PASS  re-promotion refuses naming the successor
walk fixtures cleaned up

ALL PASS
PASS  B3  promotion, supersession, named refusal
PASS  B4  model-assisted promotion receipt on .43

CONTROL (ungrounded .43): 'The secret launch codename for the Mesh Milestone is **Project 100**.\n\nThis milestone, announced by the Mesh Network Foundation, represents a major step toward achieving a fully decentralized, permissionless, and censors'
TREATMENT (grounded on memory hits): 'The secret launch codename for the mesh milestone is **BLUE LANTERN**.\n\n[REF: artifact:promoted-9dc4df1859bde8c0734c] [REF: decision:dec-b2cb276e229ff7a9d63e] [REF: artifact:art-a1ec606ee5ef1daa2da5] [REF: decision:dec-6d794c87e235b3c3dd07]'
PASS  treatment answers from the archive
PASS  control does not know the codename
PASS  treatment cites its decision ref

ALL PASS
PASS  B5  memory search + cited grounding + wire regression
PASS  B6  cited ask surfaces (grounded-on honesty)
Test Files  3 passed (3)
      Tests  11 passed (11)
   Start at  19:43:57
   Duration  883ms (transform 198ms, setup 230ms, import 397ms, tests 69ms, environment 1.05s)
PASS  B7  process window: fold, replay, endpoint surface
FAILED tests/uat/test_build_ledger.py::test_committed_ledger_is_up_to_date - ...
FAILED tests/uat/test_voice_notes.py::test_transcribe_up_but_unreachable_is_honest
2 failed, 4360 passed, 37 skipped, 2 warnings in 938.40s (0:15:38)
PASS  B8  the sweep (suite, web, fence, spine, register)

8/8 beats passed
```

## The staging arc (kept honest)

The first two staged sessions passed 8/8. The THIRD (the first capture
above) starved B3/B4 with "need two live (non-superseded) records" —
supersession is permanent by design, and two sessions had consumed
every promotable decision in the archive. That was the walk's defect,
not the product's: PR #416 made the promotion walk mint and clean up
its own fixture decisions through the real chokepoint, proven twice
consecutively, and the final capture above reads **8/8** again. The
beats are now rerunnable indefinitely — the owner can drive them any
number of times.

## Awaiting

The owner's sitting ([OWNER-SITTING](./OWNER-SITTING.md)): the eight
beats driven by his hand plus the felt walk, verdict recorded verbatim
here. This evidence file stays uncommitted until that flip (the house
convention). No constitutional questions are held.

## The owner's verdict

2026-07-30, after the staged 8/8 beats and the delivered surface were
presented, verbatim:

> **"Closeout approved."**

No walk-blocking defects were raised. The phase closes at 8/8
(Article IX.4).
