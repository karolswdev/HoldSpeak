# Evidence — HS-51-03: Lock it, the roadmap-vocabulary doc-drift guard

Write-once record of the guard that keeps the HS-51-02 scrub from rotting. The next
phase that writes a user-facing doc and pastes "see Phase 52 ..." now goes red.

## What shipped

Three tests added to `tests/unit/test_doc_drift_guard.py` (alongside the existing
stub/link/image guards), plus the `_ROADMAP_VOCAB` pattern and a `_user_facing_docs()`
scope helper:

- **`test_no_user_facing_doc_leaks_roadmap_vocabulary`** scans the user-facing docs
  for `_ROADMAP_VOCAB` and fails with a `path:line` list of offenders.
- **`test_roadmap_vocab_guard_scans_real_user_facing_docs`** is the non-vacuity
  sanity check: the set contains the real guides and `len > 5`, and the internal
  corpus is provably out (`docs/internal/DOCS_STYLE.md` is not in the set; no scanned
  file lives under `internal/`, `evidence/`, or `assets/`).
- **`test_roadmap_vocab_pattern_is_narrow_enough_to_keep_spec_names`** pins the
  pattern: it must match real leaks (`Phase 15`, `phase-37`, `HS-25-03`, `closeout`,
  ...) and must never match the kept spec names (`MIR-01`, `DIR-01`, `WFS-01`) or
  bare-`phase` usages (`a phased rollout`, `the actuator phase of the pipeline`).

## The pattern and the scope

```python
_ROADMAP_VOCAB = re.compile(
    r"\bHS-\d{2}(?:-\d+)?\b"      # HS-25, HS-17-05
    r"|\bphase[ -]\d+\b"          # Phase 15, phase-37, phase 9
    r"|\bPMO\b"
    r"|the current roadmap"
    r"|\bcloseout\b",
    re.IGNORECASE,                # lowercase "phase 15" leaks were real
)

def _user_facing_docs():
    # root README + NON-recursive docs/*.md, so internal/evidence/assets are excluded
    return [_REPO / "README.md", *sorted((_REPO / "docs").glob("*.md"))]
```

Two design points that matter:

- **Case-insensitive on purpose.** HS-51-02 found lowercase-only leaks (`phase-14`,
  `phase 15`) that a case-sensitive guard would have let through. The pattern uses
  `re.IGNORECASE`.
- **Narrower scope than the existing `_live_docs()`.** `_live_docs()` includes
  `docs/internal/` (its own sanity test asserts `PLAN_ARCHITECT_PLUGIN_SYSTEM.md` is
  in it). Reusing it here would be a permanent red, because the internal corpus keeps
  phase/story vocabulary by design. `_user_facing_docs()` is a non-recursive
  `docs/*.md` glob plus the root README, so only the user/operator-facing surface is
  scanned.

## Honest limitation (carried from the inventory)

The regex catches numbered/tagged leaks. Bare process-speak with no number
("a separate phase") is not matched, by design (a bare `\bphase\b` pattern would
false-positive on "a phased rollout" and "the actuator phase of the pipeline", both
asserted as non-matches). That class is handled by the human scrub and the codified
`DOCS_STYLE.md` rule (HS-51-04), with this guard as the backstop for the high-signal
tags.

## Tests run

```
uv run pytest -q tests/unit/test_doc_drift_guard.py
-> 8 passed   (5 existing + 3 new)
```

End-to-end proof the guard is not vacuous (not just the pattern unit test): planted
`...this lands in phase 99.` into `docs/USER_GUIDE.md`, ran the scanning guard:

```
FAILED test_no_user_facing_doc_leaks_roadmap_vocabulary
  docs/USER_GUIDE.md:443: Planted leak for guard proof: this lands in phase 99.
```

Reverted the plant (`git checkout -- docs/USER_GUIDE.md`); the guard is green again
and `USER_GUIDE.md` shows no diff. 0 `_built/` tracked.

## Not done here (by design)

- The author-facing rule in `DOCS_STYLE.md` is HS-51-04.
- The phase dogfood (formalizing this plant/revert proof) is HS-51-05.
