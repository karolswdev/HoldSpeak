# Evidence — HS-59-04: Closeout: real-metal dogfood + final-summary + PR

**Date:** 2026-06-11
**Branch:** `phase-59-languages`

The full narrative lives in [`final-summary.md`](./final-summary.md) (this
same commit); this file records the story-level proof.

## 1. The real-metal dogfood

`dogfood_story04.py` — real model load (`small` on MLX via backend auto),
real German speech (`say -v Anna`), the real settings API:

- **Pinned language on real speech**: the 4.7-second German sentence
  transcribed near-verbatim with `language="de"` through the real
  Transcriber facade. Auto-detect was run too and also succeeded on this
  sentence — reported honestly (the docs claim the pin matters for SHORT
  utterances; this medium-length sentence shows auto at its best, and the
  pin costing nothing).
- **The dictionary through the real plumbing**: `PUT /api/settings` with
  `model.language="German"` (round-tripped normalized to `"de"`) and two
  symbol entries → `Config.load()` → the exact `TextProcessor`
  construction `web_runtime` performs → `"std double colon vector"` typed
  as `std::vector` and `"x arrow y"` as `x → y`.
- **Defaults byte-identical**: fresh config saves `language="auto"` +
  `spoken_symbols=[]`; the default processor equals the bare pre-phase
  processor on the golden cases.

```
RESULT: PASS   (transcript committed in final-summary.md)
```

## 2. Gates

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2683 passed, 17 skipped
$ (cd web && npm run build)   # clean, 13 pages
$ git ls-files holdspeak/static/_built/ | wc -l
0
```

BACKLOG: **K → shipped (CLOSED 4/4)**; **O** stays queued-next with its
conditions. Project README: phase CLOSED + index row. PR to `main` merged
on green CI (recorded in the project README's operating cadence).
