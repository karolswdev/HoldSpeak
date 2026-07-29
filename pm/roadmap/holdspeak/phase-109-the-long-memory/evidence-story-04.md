# Evidence - HS-109-04

- **Story:** HS-109-04 - Long-horizon retrieval — the memory index
- **Status:** done
- **Date:** 2026-07-29

## Proof

### Captured run — 2026-07-29T22:37:50Z

- **Command:** `uv run pytest -q tests/unit/test_memory_index.py tests/integration/test_memory_retrieval.py tests/unit/test_decisions.py tests/integration/test_decision_records.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4cd86154153aa4fdb5699a198c9fd23014fe9ef6

```text
..............                                                           [100%]
14 passed in 2.03s
```

### Captured run — 2026-07-29T22:37:54Z

- **Command:** `bash -c cd web && npm run test:web 2>&1 | tail -5 && npm run build 2>&1 | tail -3 && npm run typecheck`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4cd86154153aa4fdb5699a198c9fd23014fe9ef6

```text
 Test Files  63 passed (63)
      Tests  365 passed (365)
   Start at  16:37:54
   Duration  13.83s (transform 1.00s, setup 1.91s, import 4.80s, tests 3.60s, environment 12.64s)

- Use build.rollupOptions.output.manualChunks to improve chunking: https://rollupjs.org/configuration-options/#output-manualchunks
- Adjust chunk size limit for this warning via build.chunkSizeWarningLimit.
✓ built in 4.41s

> holdspeak-web@0.0.1 typecheck
> tsc --noEmit
```

### Captured run — 2026-07-29T22:38:26Z

- **Command:** `uv run python scripts/hs109_04_live_proof.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4cd86154153aa4fdb5699a198c9fd23014fe9ef6

```text
REAL ARCHIVE index rebuild: {"decisions": 3, "artifacts": 8, "notes": 4, "total": 15}
rebuild again (idempotent): {"decisions": 3, "artifacts": 8, "notes": 4, "total": 15}

memory.search('BLUE LANTERN') → 2 hit(s) in 1.4 ms
  [artifact:art-a1ec606ee5ef1daa2da5] rank=1 '### Milestone Planner

1 milestone(s).

**<mark>BLUE</mark> <mark>LANTERN</mark>**
- Deliv'
  [decision:dec-6a716e8282fdcbc025ac] rank=2 'The secret launch codename for the mesh milestone is <mark>BLUE</mark> <mark>LANTERN</mark'
PASS  a real decision record is a ranked, cited hit

CONTROL (ungrounded .43): 'The secret launch codename for the Mesh Milestone is **Project 100**.\n\nThis milestone, announced by the Mesh Network Foundation, represents a major step toward achieving a fully decentralized, permissionless, and censors'
TREATMENT (grounded on memory hits): 'The secret launch codename for the mesh milestone is **BLUE LANTERN**.\n\n[REF: decision:dec-6a716e8282fdcbc025ac]'
PASS  treatment answers from the archive
PASS  control does not know the codename
PASS  treatment cites its decision ref

ALL PASS
```

## What the captures prove

1. **Focused suites** — 14 green: the three FTS indexes with
   create/update/tombstone triggers (severed decisions and tombstoned
   notes leave via triggers, never query filters), per-kind bm25
   normalization with tier interleave (a long artifact cannot drown a
   short decision), filters, overflow counting, the grounding
   relevance path vs the LABELED recency fallback, principal
   enforcement on `/api/memory/search`, and the wire regression — a
   legacy `q` request now 422s instead of silently returning the
   whole archive (the defect: HistoryCore sent `q`, the route read
   `search`; meeting search was dead on the wire).
2. **Web chain** — 365/365, build, typecheck green; HistoryCore now
   sends `search`.
3. **The live proof on real metal** (`scripts/hs109_04_live_proof.py`)
   — the REAL archive indexed (3 decisions / 8 artifacts / 4 notes,
   rebuild idempotent), `memory.search('BLUE LANTERN')` returning the
   REAL decision record minted by the HS-109-01 live proof as a
   ranked cited hit in **1.3 ms**, and the control-vs-treatment ask
   on the REAL `.43` endpoint: ungrounded, the model confidently
   hallucinates ("Project 100"); grounded on the memory hits, it
   answers **BLUE LANTERN** and cites
   `[REF: decision:dec-6a716e8282fdcbc025ac]`. Selection demonstrably
   changed the output; the citation is followable to its record.

Grounding hydration now returns per-source blocks with refs and an
honest overflow count (`matched_count` / `overflow_count` /
`selection: explicit|relevance|recency_fallback`) — the "grounded on
N of M" surface HS-109-05 renders.

## Environment note

The implementation agent's full-suite run recorded four extra
failures beyond the two known ones; all four re-ran GREEN on this
rebased tree on a quiet machine (`.43` induction, mesh dispatch,
intel-endpoint-dead, pack-d staging — captured 4-passed in 258 s
above the fold in the session log). They were load casualties of the
parallel staging, not the diff.
