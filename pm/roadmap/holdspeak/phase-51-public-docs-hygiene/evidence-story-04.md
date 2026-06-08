# Evidence — HS-51-04: Codify the rule in DOCS_STYLE.md

Write-once record of the author-facing rule. The scrub (HS-51-02) and the guard
(HS-51-03) make the clean state happen and stay; this story makes an author follow it
by intent, so they do not discover it only when the guard turns red.

## What shipped

A new section in `docs/internal/DOCS_STYLE.md`, placed right after "## Voice" (it is a
voice rule):

**"## Product-tense, not roadmap vocabulary (guard-enforced)"** stating:

- The principle: user-facing docs describe the product as it is, not the build
  history; a reader has never heard of a "phase".
- **Banned** in user-facing docs: phase tags (`Phase 14`, `phase-37`), story ids
  (`HS-17-05`, `HS-25-03`), process words (`PMO`, "closeout", "the current roadmap",
  "evidence snapshot"), and phase-relative tense, with a worked rewrite ("Phase 11
  shipped the connector contract" becomes "HoldSpeak's connector contract is ...").
- **Kept**: product nouns (`actuator`, `connector`, ...) and named architecture specs
  (`MIR-01`, `DIR-01`, `WFS-01`).
- **Exempt corpus**: `docs/internal/` (this guide included, which is why it can list
  the banned tokens), `docs/evidence/`, `docs/assets/`, `pm/roadmap/`.
- **Enforced**: names the guard (`test_no_user_facing_doc_leaks_roadmap_vocabulary` in
  `tests/unit/test_doc_drift_guard.py`), case-insensitive, and is honest that it
  catches numbered/tagged leaks while bare process-speak is on the author and reviewer.

The written rule is deliberately the same banned set, kept set, exempt corpus, and
guard reference as HS-51-03 enforces, so there is no daylight between the doc and the
test.

## Humanizer pass

The `humanizer` skill was invoked over the new section. Audit was clean: no em or en
dashes (periods, commas, colons, parentheses), no forced rule-of-three (the lists are
real enumerations of actual items), no inflation, no signposting. The bold lead-in
labels (`**Banned**`, `**Kept**`, `**Exempt corpus**`, `**Enforced**`) match the
established house style in the same file (`**Local-first.**`, the Voice bullets), so
they were kept. No fixes required.

## A scope check that matters

`DOCS_STYLE.md` now contains `Phase 14` and `HS-17-05` as examples. It lives in
`docs/internal/`, which `_user_facing_docs()` excludes, so the roadmap-vocabulary
guard does not flag it. Verified: the guard file is still 8 passed, and the in-scope
grep over `README.md` + `docs/*.md` is still empty (the examples are internal-only).

## Tests run

```
uv run pytest -q tests/unit/test_doc_drift_guard.py
-> 8 passed

# in-scope docs still clean (DOCS_STYLE's example tokens are internal, not scanned):
grep -rInE '\bHS-[0-9]{2}|\bphase[ -][0-9]+\b' README.md docs/*.md -i | grep -v 'docs/internal/'
-> (no output)
```

0 `_built/` tracked.

## Not done here (by design)

- The closeout dogfood + final-summary + PR is HS-51-05.
