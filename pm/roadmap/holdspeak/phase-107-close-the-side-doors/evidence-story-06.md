# Evidence - HS-107-06

- **Story:** HS-107-06 - Docs — the new number at the entry points
- **Status:** done
- **Date:** 2026-07-29

## Proof

### Captured run — 2026-07-29T07:56:35Z

- **Command:** `uv run pytest -q tests/unit/test_doc_drift_guard.py tests/unit/test_kernel_effect_fence.py tests/unit/test_product_language.py tests/unit/test_web_vocabulary_guard.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7650c01d327b56bcb3db5880e677ab8181fd28c

```text
........................................                                 [100%]
40 passed in 1.42s
```

### Captured run — 2026-07-29T07:56:37Z

- **Command:** `git diff --exit-code --stat -- holdspeak/kernel/effect_ledger.json holdspeak/kernel/broker.py holdspeak/kernel/admission.py holdspeak/kernel/journal.py holdspeak/kernel/model.py holdspeak/kernel/executor.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7650c01d327b56bcb3db5880e677ab8181fd28c

```text
(no output)
```

## What changed, and what deliberately did not

- **Counts:** both count-carrying entry points now state the audited
  truth — `docs/SECURITY.md:31-42` and
  `docs/internal/PLAN_KERNEL_OPERATION_BROKER.md:410-420` read
  **21 total / 3 covered / 18 debt** (5 mixed, 12 bypass, 1 dormant),
  with the corrected baseline (2 covered among 40) and the earned
  delta stated as **38 debt → 18 debt**. N10-N12 named as
  conservatively counted pending the owner's ruling.
- **The narrowing is UNCHANGED in strength** and still precedes every
  prevention claim (`docs/SECURITY.md:11-18`). The one added sentence
  (`:20-22`): "What changed is coverage, not containment: migrated
  routes in these families now admit and receipt, but raw primitives
  remain reachable in-process and RFC §5b confinement is still the
  threshold."
- **Drift guard:** `tests/unit/test_doc_drift_guard.py::
  test_effect_census_doc_counts_match_ledger_expected_block` parses
  the census out of both docs and asserts agreement with
  `effect_ledger.json`'s expected block — the numbers cannot drift
  apart silently again.
- **User pages byte-unchanged:** dictation's visible behaviour,
  wake, Cadence, and the egress badge's visible contract did not
  change; README.md and docs/USER_GUIDE.md gain nothing, and no
  kernel vocabulary reaches user surfaces (guards green).

## Claim-by-claim audit (HS-104-06 method)

Seventeen claims audited, each cited to the code line making it true;
four verdicts "corrected" (the census counts at both entry points,
the N10-N12 status phrasing, and the "law and test are the same
artifact" wording — replaced with the accurate "the fence derives its
counts from the checked-in ledger"), the rest "true". Highlights:
the cooperating-code narrowing is backed by
`connector_runtime.py:1-22`'s own self-description; each family's
admit-and-receipt claim cites its codec's submit/decide/receipt
lines; the raw-primitive reachability claim cites `typer.py:75-140`;
clause 6's continued force cites `CONSTITUTION.md:145-149` and the
ledger's `legal_effect`. Full table in the HS-107-06 implementation
report (agent session, 2026-07-29).

## Suite results (implementation session + this branch)

Doc/voice/vocabulary/link/count guards: 33 passed (session) and the
40-test capture above on this branch. Unit suite 3391 passed
(session; 2 optional-dep skips). Known UAT pair unchanged; no new
failures. Ledger and kernel spine byte-unchanged (captures above).
