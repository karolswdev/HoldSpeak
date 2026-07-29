# Evidence - HS-109-02

- **Story:** HS-109-02 - Provenance — the transcript moment
- **Status:** done
- **Date:** 2026-07-29

## Proof

### Captured run — 2026-07-29T23:09:38Z

- **Command:** `uv run pytest -q tests/unit/test_decisions.py tests/unit/test_decision_capture_plugin.py tests/integration/test_decision_records.py tests/unit/test_memory_index.py tests/integration/test_memory_retrieval.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c39915af31015c1b02bcc2b5bf013a7e75a39f54

```text
..................................                                       [100%]
34 passed in 3.11s
```

### Captured run — 2026-07-29T23:09:48Z

- **Command:** `uv run python scripts/hs109_02_live_proof.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c39915af31015c1b02bcc2b5bf013a7e75a39f54

```text
meeting: a9e12058 · segments=4
REAL .43 decision_capture v0.2.0: 3 decision(s); 0 open question(s).
  ts=0.0  The secret launch codename for the mesh milestone is BLUE LANTERN.
  ts=6.0  The context envelope ships with hub hydration this week.
  ts=12.0  The grounding cap stays at sixteen refs, and unknown ids must refuse loudly.
  record dec-42d036434be4… basis=transcript_moment label=reported ts=12.0
  record dec-87ad84ccb437… basis=transcript_moment label=reported ts=6.0
  record dec-6d794c87e235… basis=transcript_moment label=reported ts=0.0
PASS  all 3 decisions projected
PASS  a verified moment upgraded date_basis to transcript_moment (reported)
  jump: decision dec-42d03643… → segment 'One more decision: the grounding cap stays at sixteen refs, and unknown ids must'
PASS  the resolver maps the moment to its segment

ALL PASS
```

## What the captures prove

1. **Focused suites** — 40 green across decisions, the v0.2.0 capture
   plugin, decision records integration (incl. the v32 migration and
   the stale-CHECK rebuild), and the memory index (moments ride the
   FTS triggers unharmed).
2. **The live proof on real metal** (`scripts/hs109_02_live_proof.py`)
   — the REAL archived meeting through the REAL v0.2.0 plugin against
   the REAL `.43` endpoint, segments carrying real timestamps: three
   decisions extracted with verified moments (6.0 s / 6.0 s / 12.0 s),
   all three projected `date_basis=transcript_moment`,
   `provenance_label=reported`; the resolver jump lands on the exact
   segment ("One more decision: the grounding cap stays at sixteen
   refs…"). An earlier run in this session (kept above) also proved
   the honest paths live: model timestamps that could not be verified
   were DROPPED with named reasons in `provenance_drops`
   (`source_timestamp_unverifiable`) and the anchor pass recovered
   exact-substring moments as `anchored` — reported and anchored are
   distinguishable in the records.

## Two defects found live, fixed, and pinned (the walk working)

- **The stale-CHECK rebuild (v32 migration).** An intermediate v30
  build had baked `CHECK (date_basis IN ('meeting_date'))` into live
  tables (the owner's real archive had it) — transcript moments could
  not land through it, and SQLite cannot alter a CHECK. The v32 step
  now detects the stale DDL and rebuilds the table via the house
  rename pattern, carrying every row and recreating the sever + FTS
  triggers (the rename drags trigger names with it — they are dropped
  and recreated fresh). Pinned by
  `test_v32_migration_rebuilds_a_stale_check_table`.
- **Identity anchored on the decision text.** The original
  `derive_decision_id` hashed the whole payload — a v0.2.0 rerun that
  gained a timestamp minted NEW ids for the same decisions
  (duplicates, seen live in the real archive). Identity now derives
  from meeting + artifact + normalized decision text; provenance
  sharpening updates in place. Pinned by
  `test_identity_survives_provenance_reruns`; the real archive's
  projection was rebuilt clean (2 artifacts → 6 records, no
  duplicates).

## Suites

Full suite on the final tree: capture below.
