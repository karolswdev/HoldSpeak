# Evidence - HS-201-12

- **Story:** HS-201-12 - Write a thought is one clean note
- **Status:** done
- **Date:** 2026-09-20

## Proof

### Captured run — 2026-09-20T15:50:48Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.qM8mqtrBYO PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q tests/e2e/test_hs201_12_thought_note_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3ed82e0c114ee71faef57b54ff1a545f1e603368

```text
..                                                                       [100%]
2 passed in 8.66s
```

### Captured run — 2026-09-20T16:17:20Z

- **Command:** `bash -c cd web && npx tsc --noEmit && echo TYPECHECK-CLEAN`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3ed82e0c114ee71faef57b54ff1a545f1e603368

```text
TYPECHECK-CLEAN
```

### Captured run — 2026-09-20T16:17:33Z

- **Command:** `bash -c cd web && npx vitest run src/desk/thought-workspace/`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3ed82e0c114ee71faef57b54ff1a545f1e603368

```text

 RUN  v4.1.9 /Users/karol/dev/tools/wt-201-thought/web


 Test Files  3 passed (3)
      Tests  25 passed (25)
   Start at  10:17:34
   Duration  2.02s (transform 565ms, setup 300ms, import 1.02s, tests 1.38s, environment 900ms)
```

### Captured run — 2026-09-20T16:17:36Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.kGTvDzZ9M6 PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q tests/e2e/test_hs201_12_thought_note_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3ed82e0c114ee71faef57b54ff1a545f1e603368

```text
....                                                                     [100%]
4 passed in 29.75s
```

### Captured run — 2026-09-20T16:18:17Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.05uV228VDG PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q tests/e2e/test_hs141_thought_workbench_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3ed82e0c114ee71faef57b54ff1a545f1e603368

```text
..                                                                       [100%]
2 passed in 16.39s
```

### Captured run — 2026-09-20T16:18:35Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.iH7w7NmYvD uv run pytest -q tests/unit/test_ux_canon_ratchet.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3ed82e0c114ee71faef57b54ff1a545f1e603368

```text
....                                                                     [100%]
4 passed in 0.62s
```

### Captured run — 2026-09-20T16:18:36Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.0133pXsIXZ npm_config_cache=/Users/karol/.npm uv run python scripts/check_web_baseline.py --run`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3ed82e0c114ee71faef57b54ff1a545f1e603368

```text
Running vitest...

=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 2643 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```

## What the proof shows (HS-201-12, lane B)

The window is one column of four bands.

| Band | Species | Source |
|---|---|---|
| 1 Title | `EditInPlace` (multiline, its own mic), wraps presented AND editing | `web/src/desk/thought-workspace/ThoughtDocumentPane.tsx:41`; `thought-workspace.css:59` |
| 2 Note | `DeskEditor` (sanctioned import) with `showToolbar={false}`; the mic lives INSIDE the field and writes at the cursor | `ThoughtDocumentPane.tsx:50,58,63` |
| 3 One question | one row until Ask; the question as body text, the answer `PadGadget` (`micLabel`), one verb `Add to note` | `ThoughtWorkspaceWindow.tsx:373-398` |
| 4 Foot | `SurfaceFooter` — `READS · …` / `KEPT` / `Change` + the one filled primary `Finish` | `ThoughtWorkspaceWindow.tsx:410-426` |

Removed from THIS window (parked, not deleted): the formatting rail
(`DeskEditor` keeps it for every other host), the orphan title mic, the tag
row and `Info` (both live on in `desk/pullouts/NotePullout.tsx`), the
Note/Interview tab nav, `Filed`/`Saved`, the duplicate `Attached …`
receipt, the inserted-marker chips, and the chained turn
(`answer_and_continue`, still served and still driven by the Note pullout).
The synthesis draft is NOT parked — it renders in band 3's shape
(`ThoughtWorkspaceWindow.tsx:385`).

Red-then-green on the empty-heading fence, against `HEAD`'s own sources
restored into the tree for the run (`git show HEAD:…`, then restored):

```text
 × never renders a heading over an empty question
AssertionError: expected [ <h2></h2> ] to have a length of +0 but got 1
      Tests  1 failed | 18 skipped (19)
```

Shots (isolated HOME, no microphone; the note seeded through the API as the
owner's own: `assets/story-12-shots/`): `before-{1440,393}`,
`after-{1440,393}` (band 3 folded), `after-ask-{1440,393}`,
`after-add-{1440,393}` (the appended answer revealed in the note),
`after-change-{1440,393}` (the Reads line as the ONE context receipt),
`no-engine-{1440,393}`.

Two defects the shots caught, that every unit test passed: the reads well
drew a nameless checkbox square (fixed — `CheckGadget variant="token"`
draws its own name, `ThoughtReadsWell.tsx:103`), and at 393 a real context
name pushed `KEPT` off the glass (fixed — the foot stacks under
`@media (max-width: 720px)` through the footer's sanctioned `className`
hook, `thought-workspace.css:310`; the library's own narrow rule rides
`@container surface`, which this window's container does not answer).
Both are now fenced in the rig.

### Captured run — 2026-09-20T16:25:41Z

- **Command:** `bash -c cd web && npx tsc --noEmit && npx vitest run src/desk/thought-workspace/ 2>&1 | tail -6`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3ed82e0c114ee71faef57b54ff1a545f1e603368

```text

 Test Files  3 passed (3)
      Tests  25 passed (25)
   Start at  10:25:51
   Duration  2.05s (transform 520ms, setup 314ms, import 969ms, tests 1.40s, environment 979ms)
```

### Captured run — 2026-09-20T16:25:53Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.iDpuXl2VrO PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q tests/e2e/test_hs201_12_thought_note_glass.py tests/e2e/test_hs141_thought_workbench_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3ed82e0c114ee71faef57b54ff1a545f1e603368

```text
......                                                                   [100%]
6 passed in 40.19s
```

### Captured run — 2026-09-20T16:26:35Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.A84FwaitT4 uv run pytest -q tests/unit/test_ux_canon_ratchet.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3ed82e0c114ee71faef57b54ff1a545f1e603368

```text
....                                                                     [100%]
4 passed in 0.65s
```

### Captured run — 2026-09-20T16:26:36Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.PPUJsWOJL0 npm_config_cache=/Users/karol/.npm uv run python scripts/check_web_baseline.py --run`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3ed82e0c114ee71faef57b54ff1a545f1e603368

```text
Running vitest...

=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 2643 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```
