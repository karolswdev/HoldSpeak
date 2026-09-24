# Check — Muad'Dib, 2026-09-24, counsel on built: PHILO-4-04 (PR #627 @ 643363d9)

Written by Muad'Dib's Opus 5.5 counsel worker (read-only; the rendered red reproduced on a `git archive origin/main` copy with a real `npm ci --ignore-scripts`, no symlink; three wrong-fix mutations killed by the fences; no rig run — the two retained runs read). C1 paid by Muad'Dib in this commit.

VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:
1. Built what was ratified: the line draws only in the quiet branch after `<BriefDate>` and before `briefKept`/`generateStatus` (`ChairHome.tsx:1389-1413`), a `span.surface-receipt-line` `data-testid="arrival-brief-handled"` (`:1397-1404`); n counts `briefItems` (decisions, changed, broke, waiting — THIS WEEK outside, `:869-879`) with shelf state exactly `acknowledged`/`deferred` (`:892-894`; the only two states, `monday_brief_service.py:86`); needs `briefItems.length > 0` and every item shelved (`:895-898`) — empty shows nothing, a hidden unshelved raw-id row blocks the line, a partially triaged brief never reaches the quiet branch; the product diff is +21 lines in `ChairHome.tsx` only; no raw `<button>`, no new control, no string beyond `ALL ${n} HANDLED`; `git diff origin/main..HEAD -- holdspeak` is 0 lines; in both retained runs `/api/brief/latest` before/after the Defer keeps headline `2 decisions waiting.`, `generated_at`, `decisions: 2` — only the shelf changes.
2. Fences real, red reproduced: archive of `6cfc64e0` + the branch test (sha256-identical to Astra's `baseline-integrity.json`): `Tests 5 failed | 3 passed (8)`, the same five cases as `rendered-red-origin-main-20260924T0818Z.txt:1081`; with the branch `ChairHome.tsx`: `8 passed`; three wrong fixes (no length guard; visible rows only; any-row-shelved) each fail a named case; "no `BRIEF · 0`" at `:163,:249`; "historical counts unchanged" at `:165-166` (weak — the mock) and for real in `test_philo4_04_headline_storage.py:225-236` (generate → shelve → same-day generate → fresh `get_latest`); atlas-contract tests `2 failed` on the archive; greens in the worktree: Python `90 passed`, vitest 6 files `36 passed`.
3. The atlas case (`atlas-phase3.json:+1771-1903`): decisions seeded via `POST /api/decisions` (material, not triage); Generate, Ack and the Defer trigger are face clicks, row-scoped by `:has-text`; the contract test asserts no setup step touches `/brief/items/` (`test_philo4_04_atlas_contracts.py:84-88`); the trigger captured `POST /api/brief/items/…/shelf 200`; predicate `readable_text "ALL 2 HANDLED"`, rects 1440 (256,364,928,18) / 393 (12,371,369,18), every hit sample owned by `span.surface-receipt-line`, no console errors, settled 1.08 s; a `protocol_field /headline == {first_headline}` check after the Ack; atlas sha `35a2ed96…` equals the committed file; shots opened (order: headline → date → `ALL 2 HANDLED` → `Brief ready · 2 items`); all four checks exit 0 (`philo_graph_reference --check` 14 old notes, `philo_api_reference --check`, `philo_boundary_census --check`, `dw check`); the "scanner guard" fix (A8 per-line regex, `ux_canon_scan.py:664-669`) puts the ternary on one line — real code; `scripts` and `tests/ux_canon_ceiling.json` unchanged; the other drift fixes are line anchors and candidate lists, no assertion.
4. Evidence law: no ` M`; no `pm/roadmap/holdspeak/` asset in the diff; the worktree clean after all runs.
5. Scope: product/test changes only in files the story names; the canvas assets reach main through this PR (the ratification merged only the notes); four rig runs committed, the earlier pair (`141351Z`, `141445Z`, before the guard fix) kept and disclosed; a `final-summary.md` draft is included and says it is not a phase merge.
6. Merge sanity: `merge-base --is-ancestor origin/main HEAD` exit 0 (origin/main `6cfc64e0`).
7. Tenet 4 debt: the producer is unchanged (lawful); the headline SENTENCE itself was not on any ledger — C1.

CONDITIONS (paid):
- C1. The "Out" ledger in the phase status names the producer's headline sentence (`_compose`, `monday_brief_service.py:346-389`) as Tenet 4 wording debt and the count mismatch the owner will see.

MISSED (ranked by owner cost):
1. The face shows the contradiction on purpose: `2 decisions waiting.` directly above `ALL 2 HANDLED`; with a THIS WEEK item the counts differ. Ratified; the design owns it; C1 records it.
2. The rendered "not rewritten" assertion checks the test's own mock (`:165-166`); the real protection is the Python read-back plus the rig API reads.
3. A hidden unshelved raw-id row blocks `ALL n HANDLED` with no line and nothing telling him why (pre-existing; correct under the spec).
4. Board 9 (same-day success) is proven only because the producer returns the same brief id on a same-day Generate; untested on the rig if that changes.

TUESDAY: Yes, in part. After the last Ack or Defer, `ALL n HANDLED` appears under the date and he can tell the morning is done; the saved sentence above it still reads as current, and only the GENERATED timestamp says those counts are old.

UNKNOWN: the bundle `index-yOpsX1bz.js` is not tied to `643363d9` (runs recorded `dirty: true` at `e4cf7d08`; the atlas sha matches); the 393 `before.png` and the earlier pair not opened; the Python storage fence run from the worktree venv with `PYTHONPATH=<archive>` (the Python product has no diff); CI on #627 not read.
