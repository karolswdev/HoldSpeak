# Evidence — HS-52-06: the Voice Commands guide

Write-once record of the dedicated docs story. The feature is documented honestly,
in product-tense, and the doc obeys the Phase-51 roadmap-vocabulary guard.

## What shipped

- **`docs/VOICE_COMMANDS.md`** — the user guide: what voice commands are, a quickstart
  (add, test, save, turn on), how the deterministic whole-utterance match works, the
  four action kinds (open URL / launch app / shell / type text) in a table with
  examples, an honest "running shell commands" section (it runs real code, no
  confirmation, because you configured it; each command is limited to its own action),
  the Test affordance, the off-by-default master switch, the limitations, and a
  troubleshooting table.
- **`docs/README.md`** — linked under "Dictate", with a one-line value prop; the index
  stays a map.

## Honest, grounded, product-tense

Every claim is grounded in the shipped board (HS-52-05) and dispatch (HS-52-04): the
deterministic match, "you own the risk" with no per-fire prompt, the per-macro bound,
the off-by-default switch, the Test behaviour per kind. The guide does not oversell
that this runs local code; the shell section is plain about it.

## Voice + guards

- The `humanizer` skill was run over the guide. The audit was clean except one
  tailing-negation fragment ("never invent one"), rewritten into a real clause ("It
  cannot invent one."). No em or en dashes, no promotional language, sentence-case
  headings.
- Product-tense, no roadmap vocabulary: the **Phase-51 guard now scans this Phase-52
  doc and passes**. `Phase 52` / `HS-52-xx` do not appear in it.

## Tests

```
uv run pytest -q -k "doc_drift or doc_guard or doc" --ignore=tests/e2e/test_metal.py
-> 75 passed, 2 skipped   (the roadmap-vocabulary guard + the dangling-link + image-ref
   guards all scan docs/VOICE_COMMANDS.md and pass)

# manual confirmation:
grep -i '\bHS-[0-9]{2}|\bphase[ -][0-9]+\b|PMO|the current roadmap|closeout' docs/VOICE_COMMANDS.md
-> (no output: clean)
```

`npm run build` n/a (docs only); 0 `_built/` tracked.

## Not done here (by design)

- The closeout (dogfood proving the feature end to end, final-summary, PR, merge) is
  HS-52-07.
