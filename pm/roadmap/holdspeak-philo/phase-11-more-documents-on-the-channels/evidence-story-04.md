# Evidence - PHILO-11-04

- **Story:** PHILO-11-04 - The SEND well as one library species
- **Status:** done
- **Date:** 2026-09-30

## Reading guide (Muad'Dib's Fedaykin lane, Opus 5.5)

Worktree `../wt-philo-11-04`, branch `feat/philo-11-04`, stacked on story 01 (`feat/philo-11-01` head `3552be416`, PR #707). Every pytest ran on an isolated HOME; no metal test; no owner desk.

| Criterion / gap | Proof below |
|---|---|
| G2 red before | 06:57:11 — the G2 case against the then-committed `SendWell.tsx` + `channels.ts` (copied from `HEAD` = the base at that moment). **Round two re-pins the script to the base `3552be416`** (Astra r1 F2: `HEAD` no longer selects it): 07:20:02, exit 1, `✗NO PREVIEWNO ANSWERRetry`. This is consumer proof; the producer fields are story 02's (contract recorded in its story file). |
| One species, a case per state for a non-update document (no destination, picked, SENT, POSTED no link, REFUSED incl. the size word, FAILED, UNKNOWN, PREPARED; no manual row) + the update's cases | 06:57:25 — 35 named cases pass (**corrected, Astra r1 F6:** `web/src/desk/surface/send/__tests__/SendWell.test.tsx` 14; `web/src/features/channels/__tests__/SendWell.test.tsx` 17 incl. G2 on the update; `resendProvider` 4). Round two: 37 (16 / 17 / 4) at 07:20:05. |
| Library fences (face words, surface orphans, the kit's container law, the UX-canon ratchet) | 06:58:14 (20 passed). **06:57:31 is REJECTED as proof and kept as a finding:** its red was the kit law "the surface kit never reads the viewport" (`tests/unit/test_native_surfaces_guard.py:86`) against the first G4 draft (a `@media (max-width: 420px)` rule in `surface.css`). Fixed in design, not by the fence: the well is itself a `surface` container (G4) and the chip-head rule is intrinsic. |
| Surface + channels + connections web units | 06:58:16 — 29 files, 354 tests pass. |
| Phase 10 update glass, 1440 and 393 (no visible change except the ratified look) | Round one 06:58:23 (superseded: its DELIVERY rows were in the new grammar, a visible deviation from E1a, Astra r1 F4); round two 07:20:26 below — `scripts/verify_philo11_update_glass.py --story 04` with `HOLDSPEAK_EVIDENCE_WRITE=1`: 4 passed (both fences at both widths). Shots: `assets/story-04-shots/`. |
| Actual atlas, both widths | **07:00:45–07:00:47 (six entries) are REJECTED**: a zsh loop did not split its arguments (`--case case.p10.send.sent 1440 --viewport  `); nothing ran. The real runs are 07:00:56 → 07:01:44: `case.p10.send.sent` and `case.p10.send.prepared` at 1440 and 393, `.sent.op` and `.prepared.op` at 1440 — six `VERDICT: pass terminal=settled`. Before/after shots and observations: `assets/story-04-walks/`. The walks ran on the bundle with the species (checked: `SendWell-*.css` carries `[data-send=well]{container:surface / inline-size}`). |
| Web baseline | 07:02:06 — 2,985 passed, 0 failed; `VERDICT: baseline-subset, zero branch-new`. Its five HEALED entries are the same five story 01 observed; not attributed here. |

After the proof above, the update's re-export of the species' pieces was removed (its tests import the species from `desk/surface/send`; no compat shim). The last two runs re-prove that tree: the surface + channels + connections + update web units (33 files, 443 tests) and the web baseline again (2,985 passed, zero branch-new).

Shots I looked at: `04-picked-folder-{1440,393}`, `26-prepared-{1440,393}`, `34-history-several-1440`, `34b-history-manual-393`, and the atlas `sent` 393 after-shot. The rows are in the one grammar (name on line 1, chips on line 2 under the name), the preview headings in the display face, SEND at 12 px.

### Round three (Astra built-check r2 DO-NOT-RATIFY, `checks/story-04-built-astra-r2.md`)

| Item | Proof |
|---|---|
| The receipt survives the click that leaves its row, update and non-update | 07:54:15 — four rendered-transition cases (species: FAILED then close, REFUSED then pick another row; update: the same two) run with `SendWell.tsx` and `features/channels` byte-equal to `f4127c441`: **4 failed** (the closed row kept `LAST SEND FAILED` only, or nothing for a refusal). After `ClosedReceipt`: 07:54:48, **41 passed** (species 18, update 19, provider 4). Glass 07:54:50: **4 passed** at 1440 and 393. Shots looked at: `17-failed-folder-393.png` (the open row: the Phase 10 look, the receipt under Send) and `28b-destination-latest-failed-1440.png` (the CLOSED Folder Ledger row: LAST SEND FAILED · NO PERMISSION · NOTHING SENT · THIS DEVICE). |
| The seat | Canvas A3, B2, A4c draw a destination's last result on the closed row's line 2 beside the egress; T1 draws the refusal in the open row. Phase 10 at `332d9158` kept only `LastChip` on a closed row. SENDS stays as drawn (sent and unknown rows). |
| Claims | G2: consumer behaviour only; the producer and route proof is story 02's. G4 and the chip head: implemented; the Chair and picker proof is story 05's. Neither is proven here. |
| Baseline | 07:57:21 — 2,991 passed, zero branch-new. |
| Not done | The merge with main after #707 (Muad'Dib's call); atlas walks not re-run by this lane (Astra re-ran all six on `f4127c441`, r2 F6). |


### Round two (Astra built-check r1 DO-NOT-RATIFY, `checks/story-04-built-astra-r1.md`; Muad'Dib's rulings)

| Item | Proof |
|---|---|
| 1. Reads and actions isolated by document identity | 07:16:52 — Astra's two probes as web-unit cases, run with `SendWell.tsx` and `features/channels` byte-equal to `13ec2a7b3` (the capture checks it): **2 failed** — Send on B submitted `chs_prepared_A`; a late A read drew B's history. After the fix (`useSends` keyed by `doc.ref`, obsolete answers dropped; `mergeKnown` admits only rows of `ref`; the preview keyed by `ref`): 07:19:59, **2 passed**. The update's `mergeKnown` case now expects another document's read rows to be dropped (that expectation encoded the bug). |
| 2. G2 pinned; the contract for story 02 | 07:20:02 red on the base (above). The contract is in `story-02-…md` (top-level integer `size`, `limit` beside `code` / `error_code`; `size` the final Slack text's characters; `limit` 39000) and design §5. The face reads the top level only: the case "no top-level size … no nested form" passes a nested `context` and shows no size. BACKLOG row: carry the unit for a byte-limited channel. |
| 3. G4 and the chip head | Implemented, not proven: the Chair and the meeting's picker are story 05's proof (both widths, pointer ownership, readable heads, ordinary scrolling). |
| 4. DELIVERY rows as ratified | The rows' cells are back to the Phase 10 fragments (`DeliveryHistory` byte-equal to base `3552be416`), and the species' look reaches only `[data-send="history"][data-species="send"]` (`SendHistory`), never the update's history. Glass 07:20:26: **4 passed** at 1440 and 393. Compared by eye against Phase 10: `phase-10-the-channels/assets/story-04-shots/34-history-several-1440.png` vs `assets/story-04-shots/34-history-several-1440.png`, and the 393 manual shot `34b-history-manual-393.png` in both: the DELIVERY head, the To field and Mark delivered, the SAVED / RESULT UNKNOWN / DELIVERED rows and their chip placement are the same; the only difference in frame is the SEND well's own row above (the ratified species look, E1a). BACKLOG row: unify DELIVERY rows on the owner's canvas. |
| 5. The kit CSS guard is recursive | 07:18:47 — `assets/story-04-logs/guard_nested_mutation.sh`: a viewport query appended to `send/send-well.css` → **1 failed** naming `send/send-well.css`; reverted → **5 passed**. (The `git diff --stat` line in that output is this round's own `data-species` edit to the file, not mutation residue: the script restores the pre-mutation copy.) Plus the fixture case `test_the_scan_reaches_nested_kit_css`. Library fences: 07:20:23, **21 passed**. |
| 6. Counts and T2 | Corrected above. T2 now presses Send again after PREVIEW CHANGED and asserts the digests sent were `dig1` then `dig2`, then SAVED. Round two web units: 07:20:05 **37 passed** (species 16, update 17, provider 4). |
| Baseline | 07:24:09 — 2,987 passed, 0 failed, zero branch-new. |

The six Phase 10 atlas walks (07:00:56–07:01:44) were not re-run in round two; the glass fences re-ran on the round-two tree.


## Proof

### Captured run — 2026-09-30T06:57:11Z

- **Command:** `bash pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-04-logs/g2_red_before.sh`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
When testing, code that causes React state updates should be wrapped into act(...):
act(() => {
  /* fire events that update state */
});
/* assert on the output */
This ensures that you're testing the behavior the user would see in the browser. Learn more at https://react.dev/link/wrap-tests-with-act
 ❯ src/features/g2redbefore/__tests__/g2.test.tsx (1 test | 1 failed) 79ms
   × G2 on HEAD: a preview refused by name shows its word and the size, never NO ANSWER 78ms
⎯⎯⎯⎯⎯⎯⎯ Failed Tests 1 ⎯⎯⎯⎯⎯⎯⎯
 FAIL  src/features/g2redbefore/__tests__/g2.test.tsx > G2 on HEAD: a preview refused by name shows its word and the size, never NO ANSWER
AssertionError: expected '✗NO PREVIEWNO ANSWERRetry' to contain 'TOO LARGE FOR SLACK'
Expected: "TOO LARGE FOR SLACK"
Received: "✗NO PREVIEWNO ANSWERRetry"
 ❯ src/features/g2redbefore/__tests__/g2.test.tsx:30:28
     28|   await new Promise((r) => setTimeout(r, 50));
     29|   const open = screen.getByTestId("send-open");
     30|   expect(open.textContent).toContain("TOO LARGE FOR SLACK");
       |                            ^
     31|   expect(open.textContent).toContain("41,099 / 39,000 CHARACTERS");
     32|   expect(open.textContent).not.toContain("NO ANSWER");
⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[1/1]⎯
 Test Files  1 failed (1)
      Tests  1 failed (1)
   Start at  00:57:11
   Duration  786ms (transform 300ms, setup 57ms, import 408ms, tests 79ms, environment 173ms)
```

### Captured run — 2026-09-30T06:57:18Z

- **Command:** `bash -c cd web && npx vitest run src/desk/surface/send src/features/channels src/desk/surface/__tests__ src/pages/cores/connections 2>&1 | grep -E "✓|×|Test Files|Tests |FAIL" ; exit ${PIPESTATUS[0]}`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
 Test Files  28 passed (28)
      Tests  314 passed (314)
```

### Captured run — 2026-09-30T06:57:25Z

- **Command:** `bash -c cd web && npx vitest run --reporter=verbose src/desk/surface/send src/features/channels 2>&1 | grep -E "✓|×|Test Files|Tests " ; exit ${PIPESTATUS[0]}`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
 ✓ src/features/channels/__tests__/SendWell.test.tsx > the SEND well > no destination: NO DESTINATION + Add destination, never a counter 18ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > the SEND well > a destinations read with no answer is named, never the empty state 5ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > the SEND well > A1: the pick opens the preview and Send in place; the folder keeps its case 13ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > the SEND well > Send settles SAVED + the exact path; a double click is one press 18ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > the SEND well > a refusal names its code and NOTHING SENT 13ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > the SEND well > G2: a preview refused by name shows its word and the size, never NO ANSWER (PHILO-11-04) 18ms
 ✓ src/desk/surface/send/__tests__/SendWell.test.tsx > the SEND well species on a brief (not an update) > no destination: NO DESTINATION + Add destination; no history head, no counter of zero 18ms
 ✓ src/desk/surface/send/__tests__/SendWell.test.tsx > the SEND well species on a brief (not an update) > picked: the preview of THIS document opens with Send; the row keeps the one grammar 16ms
 ✓ src/desk/surface/send/__tests__/SendWell.test.tsx > the SEND well species on a brief (not an update) > SENT: SAVED + the exact path; SENDS 1 from the ended sends; the wire carries document_ref 21ms
 ✓ src/desk/surface/send/__tests__/SendWell.test.tsx > the SEND well species on a brief (not an update) > POSTED: a Slack send shows POSTED and the channel, never a link 12ms
 ✓ src/desk/surface/send/__tests__/SendWell.test.tsx > the SEND well species on a brief (not an update) > REFUSED on Send: the refusal word and NOTHING SENT 12ms
 ✓ src/desk/surface/send/__tests__/SendWell.test.tsx > the SEND well species on a brief (not an update) > REFUSED preview over the Slack limit (G2, canvas T1): the named word and the size, never NO ANSWER, no Send 19ms
 ✓ src/features/channels/__tests__/resendProvider.test.tsx > the provider words > names the provider that accepted the email 1ms
 ✓ src/features/channels/__tests__/resendProvider.test.tsx > the provider words > shows the provider's host as the egress and its activity page as the far side 1ms
 ✓ src/features/channels/__tests__/resendProvider.test.tsx > the provider words > keeps each provider's key under its own name 0ms
 ✓ src/features/channels/__tests__/resendProvider.test.tsx > the Destination form > picks Resend: its key row, its key save, its egress, its save body 141ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > the SEND well > a lost answer keeps the key: Retry sends the SAME command_id 17ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > the SEND well > A3: prepared sends first, ONE open; an ended one stays as its result 9ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > the SEND well > a running send: SENDING on the row and its destination; Send not enabled 31ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > the SEND well > a draft has no SEND well (the posture renders the wells only when published) 0ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > latestFor: ONE source, by dispatch_seq (Codex Astra r1 F3 on #697) > an equal clock is ordered by the hub's dispatch sequence 0ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > mergeKnown: a stale or failed read never hides a returned result (r1 F1 on #697) > keeps the returned FAILED over a read that predates it, and a read never replaces an ended row with a running one 0ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > latestFor: ONE source, by dispatch_started_at > a newer failure beats an older success, whatever the preparation order 1ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > the one DELIVERY history (A2) > head DELIVERY N counts isDelivered rows; words per channel; manual kept 6ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > the one DELIVERY history (A2) > a history read with no answer is named with Retry 2ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > the one DELIVERY history (A2) > list chips: PREPARED ×K, RESULT UNKNOWN ×M, DELIVERY ×N; none at zero 3ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > the one DELIVERY history (A2) > no chip at zero 13ms
 ✓ src/desk/surface/send/__tests__/SendWell.test.tsx > the SEND well species on a brief (not an update) > a preview refusal with no size names its word only (no invented number) 8ms
 ✓ src/desk/surface/send/__tests__/SendWell.test.tsx > the SEND well species on a brief (not an update) > a preview with no answer at all stays NO PREVIEW · NO ANSWER with Retry 8ms
 ✓ src/desk/surface/send/__tests__/SendWell.test.tsx > the SEND well species on a brief (not an update) > FAILED: the latest send's failure word and NOTHING SENT; no SENDS head for a failure 10ms
 ✓ src/desk/surface/send/__tests__/SendWell.test.tsx > the SEND well species on a brief (not an update) > UNKNOWN: RESULT UNKNOWN on the row and in the history (SENDS, no counter of zero) 9ms
 ✓ src/desk/surface/send/__tests__/SendWell.test.tsx > the SEND well species on a brief (not an update) > PREPARED: first in SEND, the document's label, BY STEWARD, Send + Discard; the head chip counts it 7ms
 ✓ src/desk/surface/send/__tests__/SendWell.test.tsx > the SEND well species on a brief (not an update) > no PREPARED chip at zero 2ms
 ✓ src/desk/surface/send/__tests__/SendWell.test.tsx > the SEND well species on a brief (not an update) > two seats of one document share one pick (the Chair and Intelligence -> BRIEF) 11ms
 ✓ src/desk/surface/send/__tests__/SendWell.test.tsx > the SEND well species on a brief (not an update) > T2: PREVIEW CHANGED reads a fresh preview; he presses Send again 15ms
 Test Files  3 passed (3)
      Tests  35 passed (35)
```

### Captured run — 2026-09-30T06:57:31Z

- **Command:** `bash -c H=$(mktemp -d); trap "rm -rf $H" EXIT; HOME=$H uv run pytest -q -p no:cacheprovider tests/unit/test_philo10_face_words.py tests/unit/test_web_surface_orphans.py tests/unit/test_native_surfaces_guard.py tests/unit/test_ux_canon_ratchet.py 2>&1 | tail -15`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
>               assert not re.search(r"(min|max)-width", match.group(0)), (
                    f"{path.name}: viewport width media query in the surface "
                    "kit — use @container surface (DESIGN_SYSTEM.md rule 2)"
                )
E               AssertionError: surface.css: viewport width media query in the surface kit — use @container surface (DESIGN_SYSTEM.md rule 2)
E               assert not <re.Match object; span=(8, 17), match='max-width'>
E                +  where <re.Match object; span=(8, 17), match='max-width'> = <function search at 0x1085028e0>('(min|max)-width', '@media (max-width: 420px) ')
E                +    where <function search at 0x1085028e0> = re.search
E                +    and   '@media (max-width: 420px) ' = <built-in method group of re.Match object at 0x10c02ad40>(0)
E                +      where <built-in method group of re.Match object at 0x10c02ad40> = <re.Match object; span=(2851, 2877), match='@media (max-width: 420px) '>.group

tests/unit/test_native_surfaces_guard.py:92: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_native_surfaces_guard.py::test_kit_css_answers_to_the_window
1 failed, 19 passed in 1.48s
```

### Captured run — 2026-09-30T06:58:14Z

- **Command:** `bash -c H=$(mktemp -d); trap "rm -rf $H" EXIT; HOME=$H uv run pytest -q -p no:cacheprovider tests/unit/test_philo10_face_words.py tests/unit/test_web_surface_orphans.py tests/unit/test_native_surfaces_guard.py tests/unit/test_ux_canon_ratchet.py 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
....................                                                     [100%]
20 passed in 1.44s
```

### Captured run — 2026-09-30T06:58:16Z

- **Command:** `bash -c cd web && npx vitest run src/desk/surface src/features/channels src/pages/cores/connections 2>&1 | grep -E "Test Files|Tests |FAIL"; exit ${PIPESTATUS[0]}`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
 Test Files  29 passed (29)
      Tests  354 passed (354)
```

### Captured run — 2026-09-30T06:58:23Z

- **Command:** `env HOLDSPEAK_EVIDENCE_WRITE=1 uv run python scripts/verify_philo11_update_glass.py --story 04`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
....                                                                     [100%]
4 passed in 128.02s (0:02:08)
```

### Captured run — 2026-09-30T07:00:45Z

- **Command:** `bash -c PHILO_WALK_HOME=$(mktemp -d); trap 'rm -rf "$PHILO_WALK_HOME"' EXIT; env HOME="$PHILO_WALK_HOME" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase10.json --case case.p10.send.sent 1440 --brain muaddib --viewport  --engine none --out .tmp/graph-walk/philo11-04/sent 1440- 2>&1 | tail -8`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
usage: graph_walk.py run [-h] --atlas ATLAS --case CASE
                         --brain {muaddib,astra} --viewport {1440,393}
                         [--engine {real,replayed,none}] [--out OUT]
                         [--no-build] [--headless]
graph_walk.py run: error: argument --viewport: expected one argument
```

### Captured run — 2026-09-30T07:00:45Z

- **Command:** `bash -c PHILO_WALK_HOME=$(mktemp -d); trap 'rm -rf "$PHILO_WALK_HOME"' EXIT; env HOME="$PHILO_WALK_HOME" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase10.json --case case.p10.send.sent 393 --brain muaddib --viewport  --engine none --out .tmp/graph-walk/philo11-04/sent 393- 2>&1 | tail -8`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
usage: graph_walk.py run [-h] --atlas ATLAS --case CASE
                         --brain {muaddib,astra} --viewport {1440,393}
                         [--engine {real,replayed,none}] [--out OUT]
                         [--no-build] [--headless]
graph_walk.py run: error: argument --viewport: expected one argument
```

### Captured run — 2026-09-30T07:00:46Z

- **Command:** `bash -c PHILO_WALK_HOME=$(mktemp -d); trap 'rm -rf "$PHILO_WALK_HOME"' EXIT; env HOME="$PHILO_WALK_HOME" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase10.json --case case.p10.send.prepared 1440 --brain muaddib --viewport  --engine none --out .tmp/graph-walk/philo11-04/prepared 1440- 2>&1 | tail -8`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
usage: graph_walk.py run [-h] --atlas ATLAS --case CASE
                         --brain {muaddib,astra} --viewport {1440,393}
                         [--engine {real,replayed,none}] [--out OUT]
                         [--no-build] [--headless]
graph_walk.py run: error: argument --viewport: expected one argument
```

### Captured run — 2026-09-30T07:00:46Z

- **Command:** `bash -c PHILO_WALK_HOME=$(mktemp -d); trap 'rm -rf "$PHILO_WALK_HOME"' EXIT; env HOME="$PHILO_WALK_HOME" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase10.json --case case.p10.send.prepared 393 --brain muaddib --viewport  --engine none --out .tmp/graph-walk/philo11-04/prepared 393- 2>&1 | tail -8`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
usage: graph_walk.py run [-h] --atlas ATLAS --case CASE
                         --brain {muaddib,astra} --viewport {1440,393}
                         [--engine {real,replayed,none}] [--out OUT]
                         [--no-build] [--headless]
graph_walk.py run: error: argument --viewport: expected one argument
```

### Captured run — 2026-09-30T07:00:46Z

- **Command:** `bash -c PHILO_WALK_HOME=$(mktemp -d); trap 'rm -rf "$PHILO_WALK_HOME"' EXIT; env HOME="$PHILO_WALK_HOME" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase10.json --case case.p10.send.sent.op 1440 --brain muaddib --viewport  --engine none --out .tmp/graph-walk/philo11-04/sent.op 1440- 2>&1 | tail -8`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
usage: graph_walk.py run [-h] --atlas ATLAS --case CASE
                         --brain {muaddib,astra} --viewport {1440,393}
                         [--engine {real,replayed,none}] [--out OUT]
                         [--no-build] [--headless]
graph_walk.py run: error: argument --viewport: expected one argument
```

### Captured run — 2026-09-30T07:00:47Z

- **Command:** `bash -c PHILO_WALK_HOME=$(mktemp -d); trap 'rm -rf "$PHILO_WALK_HOME"' EXIT; env HOME="$PHILO_WALK_HOME" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase10.json --case case.p10.send.prepared.op 1440 --brain muaddib --viewport  --engine none --out .tmp/graph-walk/philo11-04/prepared.op 1440- 2>&1 | tail -8`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
usage: graph_walk.py run [-h] --atlas ATLAS --case CASE
                         --brain {muaddib,astra} --viewport {1440,393}
                         [--engine {real,replayed,none}] [--out OUT]
                         [--no-build] [--headless]
graph_walk.py run: error: argument --viewport: expected one argument
```

### Captured run — 2026-09-30T07:00:56Z

- **Command:** `bash -c set -o pipefail; PHILO_WALK_HOME=$(mktemp -d); trap 'rm -rf "$PHILO_WALK_HOME"' EXIT; env HOME="$PHILO_WALK_HOME" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase10.json --case case.p10.send.sent --brain muaddib --viewport 1440 --engine none --out .tmp/graph-walk/philo11-04/sent-1440 2>&1 | tail -8`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
BRAIN: muaddib
SOURCE: 3552be416c9d5d968adc162941f1f81a3c7c0b44 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase10.json
RUNTIME: build=['index-CdSWn1EQ.js'] hub=http://127.0.0.1:51463 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-isgbnfa2/.local/share/holdspeak/holdspeak.db engine=none
JOB: p10
VERDICT: pass terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo11-04/sent-1440/20260930T070057Z-case.p10.send.sent-muaddib-1440/before.png', '.tmp/graph-walk/philo11-04/sent-1440/20260930T070057Z-case.p10.send.sent-muaddib-1440/after.png']
NOTE: predicate: all_of: protocol_status: POST /api/channels/send answered 200, wanted 200 (body sha256 1cdb805060de); response body contains the declared admission facts | readable_text: 'SAVED' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 75, 'y': 396, 'w': 714, 'h': 50} | protocol_reads: GET /api/channels/sends?document_ref=project_update:pupd_35d625593b024c08a619bd62d0b69d1d answered 200 with 1 row(s) {'state': 'sent', 'destination_id': 'chd_a4f9b65684160dbfb35eedfa', 'channel': 'file'}; GET /api/projects/proj-5fe809622a2b/updates answered 200 with 1 row(s) {'id': 'pupd_35d625593b024c08a619bd62d0b69d1d', 'deliveries.0.channel': 'file', 'deliveries.0.outcome': 'sent'}
```

### Captured run — 2026-09-30T07:01:07Z

- **Command:** `bash -c set -o pipefail; PHILO_WALK_HOME=$(mktemp -d); trap 'rm -rf "$PHILO_WALK_HOME"' EXIT; env HOME="$PHILO_WALK_HOME" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase10.json --case case.p10.send.sent --brain muaddib --viewport 393 --engine none --out .tmp/graph-walk/philo11-04/sent-393 2>&1 | tail -8`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
BRAIN: muaddib
SOURCE: 3552be416c9d5d968adc162941f1f81a3c7c0b44 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase10.json
RUNTIME: build=['index-CdSWn1EQ.js'] hub=http://127.0.0.1:51502 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-ugk_3rex/.local/share/holdspeak/holdspeak.db engine=none
JOB: p10
VERDICT: pass terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo11-04/sent-393/20260930T070108Z-case.p10.send.sent-muaddib-393/before.png', '.tmp/graph-walk/philo11-04/sent-393/20260930T070108Z-case.p10.send.sent-muaddib-393/after.png']
NOTE: predicate: all_of: protocol_status: POST /api/channels/send answered 200, wanted 200 (body sha256 1e5b6c3c860c); response body contains the declared admission facts | readable_text: 'SAVED' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 51, 'y': 394, 'w': 307, 'h': 74} | protocol_reads: GET /api/channels/sends?document_ref=project_update:pupd_8cbf23630d6642d59125704ccf79b781 answered 200 with 1 row(s) {'state': 'sent', 'destination_id': 'chd_06f07fa0aa3b556ec5865bc0', 'channel': 'file'}; GET /api/projects/proj-7bf8ca5edce4/updates answered 200 with 1 row(s) {'id': 'pupd_8cbf23630d6642d59125704ccf79b781', 'deliveries.0.channel': 'file', 'deliveries.0.outcome': 'sent'}
```

### Captured run — 2026-09-30T07:01:18Z

- **Command:** `bash -c set -o pipefail; PHILO_WALK_HOME=$(mktemp -d); trap 'rm -rf "$PHILO_WALK_HOME"' EXIT; env HOME="$PHILO_WALK_HOME" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase10.json --case case.p10.send.prepared --brain muaddib --viewport 1440 --engine none --out .tmp/graph-walk/philo11-04/prepared-1440 2>&1 | tail -8`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
BRAIN: muaddib
SOURCE: 3552be416c9d5d968adc162941f1f81a3c7c0b44 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase10.json
RUNTIME: build=['index-CdSWn1EQ.js'] hub=http://127.0.0.1:51549 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-bjrq3u1e/.local/share/holdspeak/holdspeak.db engine=none
JOB: p10
VERDICT: pass terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo11-04/prepared-1440/20260930T070118Z-case.p10.send.prepared-muaddib-1440/before.png', '.tmp/graph-walk/philo11-04/prepared-1440/20260930T070118Z-case.p10.send.prepared-muaddib-1440/after.png']
NOTE: predicate: all_of: readable_text: 'PREPARED' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 39, 'y': 237, 'w': 770, 'h': 56} | readable_text: 'BY YOU' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 39, 'y': 237, 'w': 770, 'h': 56} | protocol_reads: GET /api/channels/sends?document_ref=project_update:pupd_6edcaf36556d4b7a85828704732b838c answered 200 with 1 row(s) {'id': 'chs_c8041f8e6c3d4d59237bfe68', 'state': 'prepared', 'prepared_by.kind': 'owner'}
```

### Captured run — 2026-09-30T07:01:27Z

- **Command:** `bash -c set -o pipefail; PHILO_WALK_HOME=$(mktemp -d); trap 'rm -rf "$PHILO_WALK_HOME"' EXIT; env HOME="$PHILO_WALK_HOME" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase10.json --case case.p10.send.prepared --brain muaddib --viewport 393 --engine none --out .tmp/graph-walk/philo11-04/prepared-393 2>&1 | tail -8`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
BRAIN: muaddib
SOURCE: 3552be416c9d5d968adc162941f1f81a3c7c0b44 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase10.json
RUNTIME: build=['index-CdSWn1EQ.js'] hub=http://127.0.0.1:51599 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-3442l6rj/.local/share/holdspeak/holdspeak.db engine=none
JOB: p10
VERDICT: pass terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo11-04/prepared-393/20260930T070127Z-case.p10.send.prepared-muaddib-393/before.png', '.tmp/graph-walk/philo11-04/prepared-393/20260930T070127Z-case.p10.send.prepared-muaddib-393/after.png']
NOTE: predicate: all_of: readable_text: 'PREPARED' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 283, 'w': 363, 'h': 78} | readable_text: 'BY YOU' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 283, 'w': 363, 'h': 78} | protocol_reads: GET /api/channels/sends?document_ref=project_update:pupd_36018a127458481eb57594abf55ca196 answered 200 with 1 row(s) {'id': 'chs_a6b65d5d5485cca217e239a3', 'state': 'prepared', 'prepared_by.kind': 'owner'}
```

### Captured run — 2026-09-30T07:01:38Z

- **Command:** `bash -c set -o pipefail; PHILO_WALK_HOME=$(mktemp -d); trap 'rm -rf "$PHILO_WALK_HOME"' EXIT; env HOME="$PHILO_WALK_HOME" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase10.json --case case.p10.send.sent.op --brain muaddib --viewport 1440 --engine none --out .tmp/graph-walk/philo11-04/sent.op-1440 2>&1 | tail -8`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
SOURCE: 3552be416c9d5d968adc162941f1f81a3c7c0b44 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase10.json
RUNTIME: build=['index-CdSWn1EQ.js'] hub=http://127.0.0.1:51640 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-o9a3m1n5/.local/share/holdspeak/holdspeak.db engine=none
JOB: p10
VERDICT: pass terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo11-04/sent.op-1440/20260930T070138Z-case.p10.send.sent.op-muaddib-1440/before.png', '.tmp/graph-walk/philo11-04/sent.op-1440/20260930T070138Z-case.p10.send.sent.op-muaddib-1440/after.png']
NOTE: placeholder(s) ['send_op'] are bound by the trigger's own `capture_as`; `expected` is resolved after it fires (fields naming them are not read before the trigger)
NOTE: predicate: all 12 facts hold: the trigger outcome holds; observe_at updates.0.deliveries holds; observe_at updates.0.deliveries.0.outcome holds; observe_at updates.0.deliveries.0.channel holds; observe_at updates.0.deliveries.0.operation_id holds; op read #0 (kernel.receipt.read) objects.0.operation.name holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.receipt.read) objects.0.receipt.state holds; op read #0 (kernel.receipt.read) objects.0.receipt.actor_kind holds; op read #1 (channel.sends) sends holds; op read #1 (channel.sends) sends.0.state holds; op read #1 (channel.sends) sends.0.proof.sha256 holds
```

### Captured run — 2026-09-30T07:01:44Z

- **Command:** `bash -c set -o pipefail; PHILO_WALK_HOME=$(mktemp -d); trap 'rm -rf "$PHILO_WALK_HOME"' EXIT; env HOME="$PHILO_WALK_HOME" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase10.json --case case.p10.send.prepared.op --brain muaddib --viewport 1440 --engine none --out .tmp/graph-walk/philo11-04/prepared.op-1440 2>&1 | tail -8`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
SOURCE: 3552be416c9d5d968adc162941f1f81a3c7c0b44 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase10.json
RUNTIME: build=['index-CdSWn1EQ.js'] hub=http://127.0.0.1:51691 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-11yxrp4q/.local/share/holdspeak/holdspeak.db engine=none
JOB: p10
VERDICT: pass terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo11-04/prepared.op-1440/20260930T070145Z-case.p10.send.prepared.op-muaddib-1440/before.png', '.tmp/graph-walk/philo11-04/prepared.op-1440/20260930T070145Z-case.p10.send.prepared.op-muaddib-1440/after.png']
NOTE: placeholder(s) ['prepare_op'] are bound by the trigger's own `capture_as`; `expected` is resolved after it fires (fields naming them are not read before the trigger)
NOTE: predicate: all 9 facts hold: observe_at sends holds; observe_at sends.0.state holds; observe_at sends.0.prepared_by.kind holds; observe_at sends.0.prepare_operation_id holds; op read #0 (kernel.receipt.read) objects.0.operation.name holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.receipt.read) objects.0.receipt.state holds; op read #0 (kernel.receipt.read) objects.0.receipt.actor_kind holds; op read #1 (project.list_updates) updates.0.deliveries holds
```

### Captured run — 2026-09-30T07:02:06Z

- **Command:** `bash -c set -o pipefail; uv run python scripts/check_web_baseline.py --run 2>&1 | tail -15`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
Running vitest...

=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 2985 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```

### Captured run — 2026-09-30T07:04:14Z

- **Command:** `bash -c cd web && npx vitest run src/desk/surface src/features/channels src/pages/cores/connections src/features/project-room/update 2>&1 | grep -E "Test Files|Tests |FAIL"; exit ${PIPESTATUS[0]}`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4f0756becea2fbb4497ed8d518f7c5443d74b040

```text
 Test Files  33 passed (33)
      Tests  443 passed (443)
```

### Captured run — 2026-09-30T07:04:18Z

- **Command:** `bash -c set -o pipefail; uv run python scripts/check_web_baseline.py --run 2>&1 | tail -4`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4f0756becea2fbb4497ed8d518f7c5443d74b040

```text

Suite totals: 2985 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```

### Captured run — 2026-09-30T07:16:52Z

- **Command:** `bash -c git diff --quiet 13ec2a7b3 -- web/src/desk/surface/send/SendWell.tsx web/src/features/channels && echo "IMPLEMENTATION = 13ec2a7b3 (SendWell.tsx, features/channels unchanged)"; cd web && npx vitest run src/desk/surface/send -t "document identity" 2>&1 | grep -E "✓|×|Tests |AssertionError"; exit ${PIPESTATUS[0]}`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** b133339c368e8159bd12b02a5f72d1c54e151a20

```text
IMPLEMENTATION = 13ec2a7b3 (SendWell.tsx, features/channels unchanged)
     × prepared A switched to B with B's read delayed: Send submits B's send_id or nothing 97ms
     × a late read for A never populates B's history 74ms
⎯⎯⎯⎯⎯⎯⎯ Failed Tests 2 ⎯⎯⎯⎯⎯⎯⎯
AssertionError: expected [ 'chs_prepared_A' ] to deeply equal []
AssertionError: expected <div data-send="history" …(1)>…(1)</div> to be null
      Tests  2 failed | 14 skipped (16)
```

### Captured run — 2026-09-30T07:18:47Z

- **Command:** `bash pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-04-logs/guard_nested_mutation.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b133339c368e8159bd12b02a5f72d1c54e151a20

```text
== mutated (expect FAIL)
E       AssertionError: ['send/send-well.css: @media (max-width: 420px)']: viewport width media query in the surface kit — use @container surface (DESIGN_SYSTEM.md rule 2)
E       assert not ['send/send-well.css: @media (max-width: 420px)']
1 failed, 4 passed in 0.43s
== reverted (expect pass)
 web/src/desk/surface/send/send-well.css | 30 +++++++++++++++---------------
 1 file changed, 15 insertions(+), 15 deletions(-)
5 passed in 0.40s
```

### Captured run — 2026-09-30T07:19:59Z

- **Command:** `bash -c cd web && npx vitest run src/desk/surface/send -t "document identity" 2>&1 | grep -E "✓|×|Tests "; exit ${PIPESTATUS[0]}`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b133339c368e8159bd12b02a5f72d1c54e151a20

```text
      Tests  2 passed | 14 skipped (16)
```

### Captured run — 2026-09-30T07:20:02Z

- **Command:** `bash pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-04-logs/g2_red_before.sh`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** b133339c368e8159bd12b02a5f72d1c54e151a20

```text
When testing, code that causes React state updates should be wrapped into act(...):
act(() => {
  /* fire events that update state */
});
/* assert on the output */
This ensures that you're testing the behavior the user would see in the browser. Learn more at https://react.dev/link/wrap-tests-with-act
 ❯ src/features/g2redbefore/__tests__/g2.test.tsx (1 test | 1 failed) 99ms
   × G2 on the baseline 3552be416: a preview refused by name shows its word and the size, never NO ANSWER 97ms
⎯⎯⎯⎯⎯⎯⎯ Failed Tests 1 ⎯⎯⎯⎯⎯⎯⎯
 FAIL  src/features/g2redbefore/__tests__/g2.test.tsx > G2 on the baseline 3552be416: a preview refused by name shows its word and the size, never NO ANSWER
AssertionError: expected '✗NO PREVIEWNO ANSWERRetry' to contain 'TOO LARGE FOR SLACK'
Expected: "TOO LARGE FOR SLACK"
Received: "✗NO PREVIEWNO ANSWERRetry"
 ❯ src/features/g2redbefore/__tests__/g2.test.tsx:30:28
     28|   await new Promise((r) => setTimeout(r, 50));
     29|   const open = screen.getByTestId("send-open");
     30|   expect(open.textContent).toContain("TOO LARGE FOR SLACK");
       |                            ^
     31|   expect(open.textContent).toContain("41,099 / 39,000 CHARACTERS");
     32|   expect(open.textContent).not.toContain("NO ANSWER");
⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[1/1]⎯
 Test Files  1 failed (1)
      Tests  1 failed (1)
   Start at  01:20:03
   Duration  1.55s (transform 794ms, setup 94ms, import 1.04s, tests 99ms, environment 219ms)
```

### Captured run — 2026-09-30T07:20:05Z

- **Command:** `bash -c cd web && npx vitest run --reporter=verbose src/desk/surface/send src/features/channels 2>&1 | grep -E "✓|×|Test Files|Tests "; exit ${PIPESTATUS[0]}`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b133339c368e8159bd12b02a5f72d1c54e151a20

```text
 ✓ src/desk/surface/send/__tests__/SendWell.test.tsx > the SEND well species on a brief (not an update) > no destination: NO DESTINATION + Add destination; no history head, no counter of zero 52ms
 ✓ src/desk/surface/send/__tests__/SendWell.test.tsx > the SEND well species on a brief (not an update) > picked: the preview of THIS document opens with Send; the row keeps the one grammar 35ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > the SEND well > no destination: NO DESTINATION + Add destination, never a counter 40ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > the SEND well > a destinations read with no answer is named, never the empty state 9ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > the SEND well > A1: the pick opens the preview and Send in place; the folder keeps its case 23ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > the SEND well > Send settles SAVED + the exact path; a double click is one press 31ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > the SEND well > a refusal names its code and NOTHING SENT 26ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > the SEND well > G2: a preview refused by name shows its word and the size, never NO ANSWER (PHILO-11-04) 22ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > the SEND well > a lost answer keeps the key: Retry sends the SAME command_id 34ms
 ✓ src/desk/surface/send/__tests__/SendWell.test.tsx > the SEND well species on a brief (not an update) > SENT: SAVED + the exact path; SENDS 1 from the ended sends; the wire carries document_ref 34ms
 ✓ src/desk/surface/send/__tests__/SendWell.test.tsx > the SEND well species on a brief (not an update) > POSTED: a Slack send shows POSTED and the channel, never a link 16ms
 ✓ src/desk/surface/send/__tests__/SendWell.test.tsx > the SEND well species on a brief (not an update) > REFUSED on Send: the refusal word and NOTHING SENT 23ms
 ✓ src/desk/surface/send/__tests__/SendWell.test.tsx > the SEND well species on a brief (not an update) > REFUSED preview over the Slack limit (G2, canvas T1): the named word and the size, never NO ANSWER, no Send 24ms
 ✓ src/desk/surface/send/__tests__/SendWell.test.tsx > the SEND well species on a brief (not an update) > a preview refusal with no top-level size names its word only (no invented number; no nested form) 12ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > the SEND well > A3: prepared sends first, ONE open; an ended one stays as its result 19ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > the SEND well > a running send: SENDING on the row and its destination; Send not enabled 45ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > the SEND well > a draft has no SEND well (the posture renders the wells only when published) 1ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > latestFor: ONE source, by dispatch_seq (Codex Astra r1 F3 on #697) > an equal clock is ordered by the hub's dispatch sequence 0ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > mergeKnown: a stale or failed read never hides a returned result (r1 F1 on #697) > keeps the returned FAILED over a read that predates it, and a read never replaces an ended row with a running one 0ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > latestFor: ONE source, by dispatch_started_at > a newer failure beats an older success, whatever the preparation order 1ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > the one DELIVERY history (A2) > head DELIVERY N counts isDelivered rows; words per channel; manual kept 5ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > the one DELIVERY history (A2) > a history read with no answer is named with Retry 1ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > the one DELIVERY history (A2) > list chips: PREPARED ×K, RESULT UNKNOWN ×M, DELIVERY ×N; none at zero 7ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > the one DELIVERY history (A2) > no chip at zero 15ms
 ✓ src/desk/surface/send/__tests__/SendWell.test.tsx > the SEND well species on a brief (not an update) > a preview with no answer at all stays NO PREVIEW · NO ANSWER with Retry 28ms
 ✓ src/desk/surface/send/__tests__/SendWell.test.tsx > the SEND well species on a brief (not an update) > FAILED: the latest send's failure word and NOTHING SENT; no SENDS head for a failure 24ms
 ✓ src/desk/surface/send/__tests__/SendWell.test.tsx > the SEND well species on a brief (not an update) > UNKNOWN: RESULT UNKNOWN on the row and in the history (SENDS, no counter of zero) 18ms
 ✓ src/desk/surface/send/__tests__/SendWell.test.tsx > the SEND well species on a brief (not an update) > PREPARED: first in SEND, the document's label, BY STEWARD, Send + Discard; the head chip counts it 18ms
 ✓ src/desk/surface/send/__tests__/SendWell.test.tsx > the SEND well species on a brief (not an update) > no PREPARED chip at zero 3ms
 ✓ src/desk/surface/send/__tests__/SendWell.test.tsx > the SEND well species on a brief (not an update) > two seats of one document share one pick (the Chair and Intelligence -> BRIEF) 19ms
 ✓ src/features/channels/__tests__/resendProvider.test.tsx > the provider words > names the provider that accepted the email 2ms
 ✓ src/features/channels/__tests__/resendProvider.test.tsx > the provider words > shows the provider's host as the egress and its activity page as the far side 1ms
 ✓ src/features/channels/__tests__/resendProvider.test.tsx > the provider words > keeps each provider's key under its own name 0ms
 ✓ src/features/channels/__tests__/resendProvider.test.tsx > the Destination form > picks Resend: its key row, its key save, its egress, its save body 388ms
 ✓ src/desk/surface/send/__tests__/SendWell.test.tsx > the SEND well species on a brief (not an update) > T2: PREVIEW CHANGED reads a fresh preview; Send again carries the NEW digest and settles 43ms
 ✓ src/desk/surface/send/__tests__/SendWell.test.tsx > document identity: a well that changes document never shows or sends the old one (Astra r1 F1) > prepared A switched to B with B's read delayed: Send submits B's send_id or nothing 55ms
 ✓ src/desk/surface/send/__tests__/SendWell.test.tsx > document identity: a well that changes document never shows or sends the old one (Astra r1 F1) > a late read for A never populates B's history 68ms
 Test Files  3 passed (3)
      Tests  37 passed (37)
```

### Captured run — 2026-09-30T07:20:23Z

- **Command:** `bash -c H=$(mktemp -d); trap "rm -rf $H" EXIT; HOME=$H uv run pytest -q -p no:cacheprovider tests/unit/test_philo10_face_words.py tests/unit/test_web_surface_orphans.py tests/unit/test_native_surfaces_guard.py tests/unit/test_ux_canon_ratchet.py 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b133339c368e8159bd12b02a5f72d1c54e151a20

```text
.....................                                                    [100%]
21 passed in 2.75s
```

### Captured run — 2026-09-30T07:20:26Z

- **Command:** `env HOLDSPEAK_EVIDENCE_WRITE=1 uv run python scripts/verify_philo11_update_glass.py --story 04`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b133339c368e8159bd12b02a5f72d1c54e151a20

```text
....                                                                     [100%]
4 passed in 201.98s (0:03:21)
```

### Captured run — 2026-09-30T07:24:09Z

- **Command:** `bash -c set -o pipefail; uv run python scripts/check_web_baseline.py --run 2>&1 | tail -4`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b133339c368e8159bd12b02a5f72d1c54e151a20

```text

Suite totals: 2987 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```

### Captured run — 2026-09-30T07:54:15Z

- **Command:** `bash -c git diff --quiet f4127c441 -- web/src/desk/surface/send/SendWell.tsx web/src/features/channels && echo "IMPLEMENTATION = f4127c441"; cd web && npx vitest run src/desk/surface/send src/features/channels -t "survives the click" 2>&1 | grep -E "✓|×|Tests |AssertionError"; exit ${PIPESTATUS[0]}`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 09a2cc2c3b7999c410144c3c6b82cd74b7fa4774

```text
     × FAILED, then the row is closed: the failure word, NOTHING SENT and the egress stay on the row 43ms
     × REFUSED, then another row is picked: the refusal word and NOTHING SENT stay on the first row 25ms
     × FAILED, then the row is closed: LAST SEND FAILED, its word and NOTHING SENT stay on the row 41ms
     × REFUSED, then another row is picked: the refusal stays on the first row 21ms
⎯⎯⎯⎯⎯⎯⎯ Failed Tests 4 ⎯⎯⎯⎯⎯⎯⎯
AssertionError: expected '○Folder PaymentsFILE~/Reports/Payment…' to contain 'NO PERMISSION'
AssertionError: expected '○Folder PaymentsFILE~/Reports/Payment…' to contain 'REFUSED'
AssertionError: expected '○Team folderFILE~/Reports/Team✗LAST S…' to contain 'NO PERMISSION'
AssertionError: expected '○Team folderFILE~/Reports/TeamTHIS DE…' to contain 'REFUSED'
      Tests  4 failed | 37 skipped (41)
```

### Captured run — 2026-09-30T07:54:48Z

- **Command:** `bash -c cd web && npx vitest run --reporter=verbose src/desk/surface/send src/features/channels 2>&1 | grep -E "survives|×|Test Files|Tests "; exit ${PIPESTATUS[0]}`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 09a2cc2c3b7999c410144c3c6b82cd74b7fa4774

```text
 ✓ src/features/channels/__tests__/SendWell.test.tsx > the update: the receipt survives the click that leaves the row (Astra r2 F1) > FAILED, then the row is closed: LAST SEND FAILED, its word and NOTHING SENT stay on the row 19ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > the update: the receipt survives the click that leaves the row (Astra r2 F1) > REFUSED, then another row is picked: the refusal stays on the first row 18ms
 ✓ src/features/channels/__tests__/SendWell.test.tsx > the one DELIVERY history (A2) > list chips: PREPARED ×K, RESULT UNKNOWN ×M, DELIVERY ×N; none at zero 3ms
 ✓ src/desk/surface/send/__tests__/SendWell.test.tsx > the receipt survives the click that leaves the row (Astra r2 F1) > FAILED, then the row is closed: the failure word, NOTHING SENT and the egress stay on the row 14ms
 ✓ src/desk/surface/send/__tests__/SendWell.test.tsx > the receipt survives the click that leaves the row (Astra r2 F1) > REFUSED, then another row is picked: the refusal word and NOTHING SENT stay on the first row 19ms
 Test Files  3 passed (3)
      Tests  41 passed (41)
```

### Captured run — 2026-09-30T07:54:50Z

- **Command:** `env HOLDSPEAK_EVIDENCE_WRITE=1 uv run python scripts/verify_philo11_update_glass.py --story 04`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 09a2cc2c3b7999c410144c3c6b82cd74b7fa4774

```text
....                                                                     [100%]
4 passed in 139.22s (0:02:19)
```

### Captured run — 2026-09-30T07:57:21Z

- **Command:** `bash -c set -o pipefail; uv run python scripts/check_web_baseline.py --run 2>&1 | tail -4`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 09a2cc2c3b7999c410144c3c6b82cd74b7fa4774

```text

Suite totals: 2991 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```
