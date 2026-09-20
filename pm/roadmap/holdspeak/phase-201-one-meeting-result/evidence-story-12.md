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
| 3 One question | one row until Ask; the question as body text, the answer `PadGadget` (`micLabel`), one verb `Add to note` | `ThoughtWorkspaceWindow.tsx:433-458` |
| 4 Foot | `SurfaceFooter` — `READS · …` / `KEPT` / `Change` + the one filled primary `Finish` | `ThoughtWorkspaceWindow.tsx:470-485` |

Removed from THIS window. **Corrected by counsel on built (finding 3): the
first version of this line said "parked, not deleted … live on in the Note
pullout", and that was false** — `desk/components/Pullout.tsx:123` routes a
thought-owned note to THIS window, so the legacy pullout's copies have no
route from an owned note. They are deliberate removals, ledgered (a) with
their reason in the story's Scope: the formatting rail (`DeskEditor` keeps
it for every other host), the orphan title mic, the tag row, `Info` / the
original-capture disclosure (the raw capture stays in custody on the hub
and this window never fetches it — fenced in
`tests/e2e/test_hs141_thought_workbench_glass.py`), the default-context
picker, the Note/Interview tab nav, `Filed`/`Saved`, the duplicate
`Attached …` receipt and the inserted-marker chips. The chained turn
(`answer_and_continue`, `desk/thoughts.ts:423`) is still served and still
tested, but has no UI caller in the product today. The synthesis draft is
NOT parked — it renders in band 3's shape
(`ThoughtWorkspaceWindow.tsx:445`) and is APPENDED, never accepted
(`ThoughtWorkspaceWindow.tsx:231`).

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

## Counsel fix round (Astra DO-NOT-RATIFY on PR #592, 2026-09-20)

All seven findings paid. The two behavioural ones are proved **red first on
a real isolated hub**, not on mocks.

| # | Finding | Fix | Proof |
|---|---|---|---|
| 1 (b) | `Add to note` on a draft sent `accept`, and the hub REPLACED title, body and tags | the draft is appended through the sole writer; `accept` is never called; the durable edit supersedes the review itself, so the band folds | `ThoughtWorkspaceWindow.tsx:231`; rig `test_thought_note_draft_is_appended_never_replaced` |
| 2 (b) | Finish with an unadded answer: `/answer` 200 then `/complete` 409 `workspace_cursor_conflict` | the projection is re-read after the answer lands; completion uses THAT thought and cursor | `ThoughtWorkspaceWindow.tsx:263-277`; rig leg "Finish with an UNADDED answer" |
| 3 | six candidates, no search; false "parked in the pullout" claim | the well searches the real listing (debounced, mic on the field); the removals are re-ledgered (a) above and in the story's Scope | `ThoughtReadsWell.tsx:61-89`; rig long-context leg types into `Find a note` |
| 4 | "NO ENGINE YET" covered a busy coordinator; `Try again` was dead under a conflict | three truthful states (`ENGINE BUSY` · `ENGINE NOT REACHABLE` · `NO ENGINE YET`); a conflict carries `Reload`, which re-seats the note through the writer | `ThoughtWorkspaceWindow.tsx:340-356` (the three states), `:373-393` + `:477` (Reload); vitest "offers Reload — not a dead Try again" |
| 5 | a long context name pushed Finish outside the window; the open well was 832px inside 393 | the READS token is the only slot that shrinks (full text in `title`), KEPT keeps a floor, the well and its tokens truncate; the narrow rules moved to `@container surface` on the window's own container (UX-CANON D) | `thought-workspace.css:22` (`container-name: surface`), `:316-334` (the foot), `:370-397` (the container query); rig `test_thought_note_long_context_and_open_well_never_clip` |
| 6 | two lying doubles | the Finish test now asserts the cursor the answer advanced; the draft test asserts the real save payload (body appended, title untouched) and that `actOnReview` is never called; the behaviour itself is proved on the hub | `ThoughtWorkspaceWindow.test.tsx:196-228`, `:230-259` |
| 7 | Web Quality red on `z-index: 1`; doc drift unclassified | the ladder token replaces the literal; the API-reference drift was **mine** (the new rig registers as a caller of 20 routes) and is regenerated | `thought-workspace.css:114` (`--desk-z-local`); `docs/generated/api-reference.json` |

Red first on the real hub (the fix reverted in the tree, the rig unchanged):

```text
# finding 1 — the owner's words were deleted by `accept`
>               assert OWNER_WORDS in kept["working_note"]["body_markdown"]
E               assert 'OWNER WORDS THAT MUST SURVIVE.' in 'The team disagrees about the freeze date.'
1 failed, 7 deselected in 10.44s

# finding 2 — Finish never completes (the 409 keeps it working)
E   playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 20000ms exceeded.
E     - waiting for get_by_role("region", name="Thought").get_by_role("button", name="Resume") to be visible
1 failed, 3 deselected in 32.19s
```

And red first in vitest for findings 2 and 4 (same reverts):

```text
× adds a typed answer, then keeps against the cursor that answer advanced
AssertionError: expected { hub_id: 'hub-1', …(3) } to deeply equal { hub_id: 'hub-1', …(3) }
-   "aggregate_revision": 4,   "continuity_revision": 6,
+   "aggregate_revision": 3,   "continuity_revision": 4,
× offers Reload — not a dead Try again — when the note changed elsewhere
```

New shots at both widths: `after-draft-{1440,393}` (the draft in band 3's
shape), `after-draft-added-{1440,393}` (the note keeps the owner's words and
the draft is revealed), `long-context-open-well-{1440,393}` (the OPEN well
with a long context name: READS truncates, KEPT keeps its width, Change and
Finish stay inside the window). Every earlier shot was re-taken on the fixed
build.

### Captured run — 2026-09-20T16:58:45Z

- **Command:** `bash -c cd web && npm run check 2>&1 | grep -E 'token gate|architecture guard|Test Files|  Tests |bundle gate|built in' | tail -8`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ea01c7d21709005e1e4a944f08728fa13b95976f

```text
token gate: clean (11 allow-listed exceptions, all in use)
React architecture guard passed (792 source files; zero framework residue).
 Test Files  279 passed (279)
      Tests  2645 passed (2645)
✓ built in 4.56s
bundle gate passed (Desk JS 1306225 B; Desk CSS 315404 B; source maps 0)
```

### Captured run — 2026-09-20T17:00:29Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.1BydI4HGWY PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q tests/e2e/test_hs201_12_thought_note_glass.py tests/e2e/test_hs141_thought_workbench_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ea01c7d21709005e1e4a944f08728fa13b95976f

```text
..........                                                               [100%]
10 passed in 59.90s
```

### Captured run — 2026-09-20T17:01:31Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.psEjhrpHP4 uv run pytest -q tests/unit/test_ux_canon_ratchet.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ea01c7d21709005e1e4a944f08728fa13b95976f

```text
....                                                                     [100%]
4 passed in 0.66s
```

### Captured run — 2026-09-20T17:01:38Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.tmTaUUDqsZ uv run bash -c set -e; python -m unittest discover -s tests/unit -p test_docs_navigation.py 2>&1 | tail -1; for c in "scripts/check_docs.py" "scripts/philo_repository_census.py --check" "scripts/philo_api_reference.py --check" "scripts/philo_boundary_census.py --check" "scripts/philo_doctor_reference.py --check" "scripts/philo_config_reference.py --check" "scripts/validate_architecture.py" "scripts/generate_capability_docs.py --check" "scripts/check_doc_coverage.py --check"; do python $c | tail -1; done; echo DOCS-CI-GREEN`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ea01c7d21709005e1e4a944f08728fa13b95976f

```text
OK
Documentation navigation: 70 files checked; local targets and Markdown headings resolve.
Repository census: 5 outputs verified.
API reference checked
Boundary candidate census checked
Doctor reference: 41 check functions
Configuration declaration reference is current
Architecture metadata validation passed.
Architecture documentation checked (10 outputs).
Documentation coverage checked.
DOCS-CI-GREEN
```

### Captured run — 2026-09-20T17:01:58Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.7pHPqoeFTg npm_config_cache=/Users/karol/.npm uv run python scripts/check_web_baseline.py --run`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ea01c7d21709005e1e4a944f08728fa13b95976f

```text
Running vitest...

=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 2645 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```

### Captured run — 2026-09-20T17:03:47Z

- **Command:** `bash -c cd web && npx tsc --noEmit && npx vitest run src/desk/thought-workspace/ 2>&1 | tail -5`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ea01c7d21709005e1e4a944f08728fa13b95976f

```text
 Test Files  3 passed (3)
      Tests  27 passed (27)
   Start at  11:03:56
   Duration  2.57s (transform 568ms, setup 309ms, import 1.01s, tests 1.91s, environment 982ms)
```

### Captured run — 2026-09-20T17:03:59Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.QDnvEyRnQu PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q tests/e2e/test_hs201_12_thought_note_glass.py tests/e2e/test_hs141_thought_workbench_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ea01c7d21709005e1e4a944f08728fa13b95976f

```text
..........                                                               [100%]
10 passed in 59.31s
```

### Captured run — 2026-09-20T17:04:59Z

- **Command:** `bash -c cd web && npm run check 2>&1 | grep -E 'token gate|architecture guard|Test Files|  Tests |bundle gate' | tail -6`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ea01c7d21709005e1e4a944f08728fa13b95976f

```text
token gate: clean (11 allow-listed exceptions, all in use)
React architecture guard passed (792 source files; zero framework residue).
 Test Files  279 passed (279)
      Tests  2645 passed (2645)
bundle gate passed (Desk JS 1306225 B; Desk CSS 315399 B; source maps 0)
```

### Captured run — 2026-09-20T17:06:12Z

- **Command:** `bash -c cd web && npm run check 2>&1 | grep -E 'token gate|architecture guard|Test Files|  Tests |bundle gate' | tail -6`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ea01c7d21709005e1e4a944f08728fa13b95976f

```text
token gate: clean (11 allow-listed exceptions, all in use)
React architecture guard passed (792 source files; zero framework residue).
 Test Files  279 passed (279)
      Tests  2645 passed (2645)
bundle gate passed (Desk JS 1306225 B; Desk CSS 315399 B; source maps 0)
```
