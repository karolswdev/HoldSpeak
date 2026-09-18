# Evidence - HS-200-13

- **Story:** HS-200-13 - Carry decisions and commitments into the next day
- **Status:** done
- **Date:** 2026-09-17

## Proof

### Captured run — 2026-09-18T04:36:11Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.2dIgRen4ZP uv run pytest -q -p no:cacheprovider tests/unit/test_phase200_continuity.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** da102cd00ce723d62a45152348665af9ddebd57b

```text
............                                                             [100%]
12 passed in 7.36s
```

### Captured run — 2026-09-18T04:36:54Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.jqXz3pHZc6 PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q -p no:cacheprovider -s tests/e2e/test_hs200_continuity_glass.py tests/e2e/test_hs526_desk_memory_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** da102cd00ce723d62a45152348665af9ddebd57b

```text
[hs200-13] recall minute @1440: 3.5 s (target 60 s)
.[hs200-13] recall minute @393: 3.5 s (target 60 s)
..[hs526] results@1440 type steps [10, 11, 12, 13, 26]
[hs526] /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/18afc54e-71d7-45d4-bcef-8b0a4ace77cd/scratchpad/shots526/desk-memory-results-1440.png
.[hs526] results@393 type steps [10, 11, 12, 13, 26]
[hs526] /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/18afc54e-71d7-45d4-bcef-8b0a4ace77cd/scratchpad/shots526/desk-memory-results-393.png
.[hs526] /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/18afc54e-71d7-45d4-bcef-8b0a4ace77cd/scratchpad/shots526/desk-memory-empty-1440.png
.[hs526] /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/18afc54e-71d7-45d4-bcef-8b0a4ace77cd/scratchpad/shots526/desk-memory-empty-393.png
.
7 passed in 39.21s
```

## Deviations from the boards, on canon

- `OWED` rows carry `Name an owner` / `Set a date` / `Mark done` where board `P5Recall` draws `Complete`. Ruled by the brief (AC3: one lawful next action) and kept by counsel: the verb is named for the act the receipt records (`commitment.completed`), and it is only offered once owner and date are known (AC4).
- `Open — the decision` is withheld (no decision-record face exists to open; the Project button and `Open source` are the two real destinations, UX-CANON A.11). The footer's `Unfinished` / `Repairs` wings are withheld on this window for the same reason.
- The display count reads `5 remembered` on the seeded desk: the two seeded meetings match the phrase and are drawn under `MEETINGS 2`; the board's `3` has no meeting rows behind it.
- Two current decisions matching one phrase are ordered newest decided first and the first is the accented card (`docs/RELATIONSHIP_AWARE_MEMORY.md`, "Recall on the Desk memory face").


## What was built

Recall on Desk memory: the current decision first, accented, with its rationale, its source span (`MTG 09-07 · 11:31 · Open source`), its Project and `Carry into brief`; superseded records dimmed under it with `SUPERSEDED BY DEC 09-07`; a disputed record typed and never current; `OWED` commitments with typed unknowns and one lawful next action each (`Name an owner`, `Set a date`, `Mark done`). Commitments are real attention items on the arrival (the producer HS-200-15 built against synthetic rows now exists), with the owner and date wells unfolding in place under the row. Completion is an explicit act only: `Mark done` and `Dismiss` close with a kernel receipt inside the write transaction; naming an owner, setting a date, linking a PR or an artifact never flips status (fenced through every path counsel could find, including MCP). The carry mark (`preparation_carries`) is one per current record and resolves across a supersession at read time; HS-200-11's manifest builder consumes it as `CARRIED FORWARD n`. The last-known observation is durable (`needs_you_last_known`), pruned when a successful read no longer names a source, bounded to a 14-day replay, and one store per process through the composition root. The extractor's rationale now reaches the confirmed record (HS-200-12's confirm wrote an empty one).

## The measured minute

Beat 6 from the arrival (open Desk memory, search the phrase, land on the current decision with the superseded one visible, press `Carry into brief`): 3.5 s at 1440, 3.6 s at 393, against the 60 s target (`assets/story-13-shots/recall-minute.json`).

## Counsel-on-built: RATIFY-WITH-CONDITIONS, all paid

Four P1s: the API surface was not regenerated; a carry followed by a supersession produced two marks for one current record and drew the successor as not carried; `due`/`delegate` were accepted on a completed commitment and `done` re-receipted; the durable last-known store was never pruned (fifty stale sources replayed on a project-list failure) and only one of three callers used it. P2s paid: `reopen` receipts; `carry`/`dispute`/`supersede` require the DECIDE right and refuse by name; a carry on a superseded or disputed record is refused at the service; the decision title wraps at 393; the arrival's owner and date verbs unfold in place instead of detouring to Desk memory. Counsel's completion-path audit stands in the report: every path that closes a commitment is an explicit verb with a receipt.

## Deviations from the boards, on canon

`Mark done` rather than the board's `Complete`: the receipt names the act. The card's `Open` and the footer's `Unfinished`/`Repairs` wings are withheld: no decision-record face exists to open and no such wings are built on this window; a verb that leads nowhere is a lie (A.11). The owed row draws typed unknowns rather than the board's `DUE TODAY` because the seeded commitment has them. ASCII-only search and a forged supersession cycle are parked in the BACKLOG.
