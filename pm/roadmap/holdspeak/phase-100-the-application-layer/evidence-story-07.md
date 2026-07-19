# Evidence - HS-100-07

- **Story:** HS-100-07 - B3: Speak
- **Status:** done
- **Date:** 2026-07-19

## Proof

### Captured run — 2026-07-19T14:16:49Z

- **Command:** `sh -c HS_WALK_BASE=http://localhost:8792 HS_WALK_TOKEN=YZi6W-PzL8bfY4UbMgxThqUdUUKQcGj8 uv run python scripts/desk_gl_walk.py speakflow && uv run pytest -q tests/integration -k 'dictation or dry_run' 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 88f44a51a788cd7c829b319ecfc0cfef3382aabf

```text
speakflow: arrival -> correction in 4 interactions, 1 window, transcript 'Hello world, hello world, hello world, hello world.'
176 passed, 1 skipped, 557 deselected in 63.63s (0:01:03)
```

## Summary of proof

- **Speak is an application, not a cockpit.** DictationCore opens ON
  the loop: hero mic (hold-to-talk, accent-filled), utterance, run,
  Right/Wrong, the correction ritual in place. The nine tabs are gone:
  Journal and Blocks are WINGS in the window head (new wing kit:
  web/src/desk/surface/wings.tsx + a `wings` slot on DeskWindowFrame,
  published per-window via WingSlotContext); Readiness/Memory/
  Knowledge/Runtime/Hooks/Nudges stack behind the ONE gear door.
  Readiness on the face is one status line ("Pipeline live · types
  into … · budget" or an honest off-line with a Review verb) — the
  diagnostics wall lives behind the gear. Wire calls unchanged.
- **The app is named Speak** (registry title + room menu; the walk
  followed). The flow budget is PINNED as a walk leg (`speakflow`,
  captured above): arrival → correction ritual open in **4
  interactions, ONE window**, real voice through real Whisper on the
  production bundle, and `.desk-surface-body` may carry no tablist.
- **Live screenshots** at 1440 and 393 (+ the door and Journal wing):
  assets/hs-100-07-speak-*.png — walked by eye; refects applied
  (Speak title, filled mic, status anchored).
- Suites: vitest 294/294; dictation/dry-run integration 176 passed
  (four pins retargeted to the new shape with intent preserved);
  vocabulary guard green; token gate clean; dictation walk leg green
  end-to-end on the staged hub.
