# Evidence - HS-200-44

- **Story:** HS-200-44 - Make the release guards see what they claim to guard
- **Status:** done
- **Date:** 2026-09-17

## Proof

### Captured run — 2026-09-17T23:44:20Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.KW456WXkRH uv run pytest -q -p no:cacheprovider -rf tests/unit/test_ux_canon_scan.py tests/unit/test_ux_canon_ratchet.py tests/unit/test_phase200_canon_guard.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9e9a569a495160b549eb847717a10caa342071f9

```text
...................................................                      [100%]
51 passed in 2.94s
```

### Captured run — 2026-09-17T23:44:23Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.WSXszaxigl uv run python scripts/ux_canon_scan.py --root .`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9e9a569a495160b549eb847717a10caa342071f9

```text
Scanned 233 files, found 324 violations across 228 faces.
  (nothing written: pass --write-census DIR, --json/--md/--ranking, or --write-ceiling)

Totals per rule:
  A1: 175
  A3-prose: 48
  B: 32
  A8: 25
  emoji: 21
  raw-ids: 17
  C: 4
  A3-sentence: 2

Top 10 faces:
  WorkbenchWindow                 tuesday=3  debt= 75  score= 225  loudest=A1
  ProjectRoomCore                 tuesday=7  debt= 21  score= 147  loudest=A3-prose
  ThreadPullout                   tuesday=6  debt= 19  score= 114  loudest=A1
  PeopleCore                      tuesday=6  debt= 12  score=  72  loudest=raw-ids
  DeskToolInspector               tuesday=1  debt= 49  score=  49  loudest=A3-prose
  ReviewPosture                   tuesday=4  debt= 11  score=  44  loudest=A3-prose
  StewardPosture                  tuesday=4  debt= 10  score=  40  loudest=A1
  SystemShade                     tuesday=5  debt=  7  score=  35  loudest=A3-prose
  DeskEditor                      tuesday=1  debt= 33  score=  33  loudest=A1
  SettingsCore                    tuesday=7  debt=  4  score=  28  loudest=A8
```

## What the guard saw before, and sees now (2026-09-17)

| Rule | HEAD scanner | Fixed scanner | Ceiling written |
|---|---|---|---|
| A1 raw `<button` | 4 | **175** | 175 |
| A3-prose | 11 | 48 | 48 |
| A3-sentence | 1 | 2 | 2 |
| raw-ids | 16 | 17 | 17 |
| A8 / B / C / emoji | 25 / 32 / 4 / 21 | unchanged | unchanged |
| A4 / A9 / DS6 / mic | 0 | 0 | 0 |

Superset invariant held for every rule over the real tree: pre-fix hits ⊆ post-fix hits, nothing lost, nothing relaxed. Reconciliation with the doc-claims registry's independent count (203 over all of `web/src/**/*.tsx`): scanner scope 175 + 28 outside its scope (`design/AtmospherePreview.tsx` 6, `desk/chair/_parked/**` 17, five `*.test.tsx` 5) = 203 exactly, asserted by `test_scanner_a1_reconciles_with_the_doc_claims_registry`. The charter's 187 and the audit's figures were earlier measurements; today's truth is 175 / 203.

## Every rule audited for the line-shape blindness

Fixed to whole-file matching with line numbers from the match offset: A1, A3-sentence (text node; a node spanning lines is rejected when it carries code marks, because the first cut read `) : ( // comment` as prose), A3-prose (`<p>`/`<small>` with attributes on their own lines), A9 (bounded 200-char windows), raw-ids (per-line pass kept verbatim plus a fenced multi-line pass; the unfenced first cut crossed `Record<string, X[]>` for 843 false hits), DS6 (CSS and inline values wrapped over lines), C (font-size values). Not applicable and kept per line with the reason recorded in the scanner: A3-sentence prop literals, A3-prose className hints, A4, A8 (a whole-file rewrite crossed loop bodies and object literals for 109 non-counter hits; measured multi-line counter shapes in `web/src`: 0), B, raw-ids props, emoji. Mic was already whole-content.

## The fence fails against the pre-fix scanner (verbatim, `HS200_CANON_SCANNER=<git show HEAD:scripts/ux_canon_scan.py>`)

```
E   AssertionError: the scanner reports A1=4 but an independent whole-file count over the same scope finds 175: the guard does not see what it claims to guard
E   AssertionError: registry 203 != scanner 4 + 28 outside the scanner's scope (design/, _parked, *.test.tsx)
E   AssertionError: a plain scanner run changed the tree: git status --porcelain, pm/roadmap/holdspeak/phase-170-the-great-pass/assets/census/ranking.md, .../violations.json, .../violations.md
FAILED tests/unit/test_phase200_canon_guard.py::test_a1_counts_every_shape_and_not_the_decoy
FAILED tests/unit/test_phase200_canon_guard.py::test_a3_sentence_sees_a_wrapped_text_node
FAILED tests/unit/test_phase200_canon_guard.py::test_a3_prose_sees_a_paragraph_with_attributes_on_their_own_lines
FAILED tests/unit/test_phase200_canon_guard.py::test_raw_ids_sees_a_snake_case_text_node_on_its_own_line
FAILED tests/unit/test_phase200_canon_guard.py::test_raw_ids_sees_an_id_child_on_its_own_line
FAILED tests/unit/test_phase200_canon_guard.py::test_ds6_sees_a_css_declaration_wrapped_over_lines
FAILED tests/unit/test_phase200_canon_guard.py::test_ds6_sees_an_inline_style_wrapped_over_lines
FAILED tests/unit/test_phase200_canon_guard.py::test_scanner_a1_equals_an_independent_count_over_web_src
FAILED tests/unit/test_phase200_canon_guard.py::test_scanner_a1_reconciles_with_the_doc_claims_registry
FAILED tests/unit/test_phase200_canon_guard.py::test_a_plain_run_writes_nothing_under_the_repo
10 failed, 3 passed in 2.37s
```
(A9's fixture first passed pre-fix because its path carried `api` before `discover`; corrected to `/x/discover`, the pre-fix run fails it too: `assert [] == [1]`.)

## The tree stays clean

A plain `scripts/ux_canon_scan.py --root .` on HEAD rewrote three tracked census assets under `pm/roadmap/holdspeak/phase-170-the-great-pass/assets/census/`. Now it prints `(nothing written: pass --write-census DIR, --json/--md/--ranking, or --write-ceiling)`; the captured run above left `git status` unchanged. `--write-ceiling` refuses a rising ceiling without `--ceiling-reason` (exercised: exit 2, `ceiling would RISE for A1: 4 -> 175 ...`) and stamps date + reason into `tests/ux_canon_ceiling.json`. The phase-170 census assets were deliberately NOT regenerated (a closed phase's proof stays as it was).

## Orchestrator ruling

The 175 are debt, not regression; they accumulated while the guard was blind. No face was fixed here by charter. The doc-claims registry's UX-CANON row flips to `holds` (the sentence now states the measured ratchet) in the commit that stacks this on the shipped HS-200-45 tree, where the registry lives.

## Registry flip (on the shipped HS-200-45 tree)

The UX-CANON row moved from `known_false` to `holds`: its predicate reads the repo-wide A1 ceiling out of `tests/ux_canon_ceiling.json`, the number the document states, and the scanner's live count, and requires all three to agree with the count at or under the ceiling. Ratchet 5 → 4. `scripts/doc_claims.py --measure`: 0 drifted rows.
