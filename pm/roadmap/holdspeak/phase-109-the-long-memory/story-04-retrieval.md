# HS-109-04 - Long-horizon retrieval — the memory index

- **Project:** holdspeak
- **Phase:** 109
- **Status:** done
- **Depends on:** HS-109-01
- **Unblocks:** HS-109-05
- **Owner:** unassigned

## The thesis (the bar)

The only FTS index in the product is `segments_fts`
(`db/core.py:301-325`) — transcripts. Decisions, artifacts, and notes
are invisible to search. And project grounding is not retrieval: it
takes the newest sixteen resources ordered by modification time
(`grounding.py:24-27`, `relationships.py:235-241`) and concatenates
them into one container block. On a two-year archive that silently
becomes "recent stuff," which is precisely the failure mode of a
memory that claims "years later."

The bar: **one memory index over decisions, artifacts, and notes;
ranked, cited retrieval; and grounding that selects by relevance
with per-source citations — with every miss visible.** FTS5 +
ranking first; vectors only if real queries prove FTS insufficient
(chartered decision).

## Problem

"What did we decide about the retry policy?" has no query the system
can run. And "ask this project" degrades with archive size instead of
improving — the opposite of memory.

## Recipe

1. **The index.** FTS5 tables (additive migration + triggers, the
   `segments_fts` pattern) over decision text/rationale, artifact
   title/markdown, and note title/body. Rebuildable by one command;
   backfilled at migration; counts printed.
2. **The query.** One repository search across the three kinds:
   ranked (bm25 to start), filterable by kind, project, and time
   range, each hit carrying its source ref (`decision:<id>`,
   `artifact:<id>`, `note:<id>`) and a snippet. A route exposes it;
   reads owe principal + read authority only.
3. **Grounding grows citations.** Project hydration
   (`grounding.py:124-223`) selects members by query relevance when
   the ask has a query (falling back to recency when it does not),
   and returns per-source blocks with refs instead of one
   concatenated blob, so the model's answer can cite and 05 can
   render the citations. Caps stay (bounded context is honest);
   what changed is SELECTION and ATTRIBUTION.
4. **The overflow is named.** When more matched than fit, the
   hydration result says how many were left out (Article VI). No
   silent truncation.
5. **Fix the search wire defect.** `HistoryCore` sends `q`; the
   meetings route reads `search` (`web/routes/meetings/crud.py:24-33`
   vs `HistoryCore.tsx:688-695`) — meeting archive search is likely
   dead on the wire today. Fix param, add the regression test that
   would have caught it (route-level: a `q` request returns filtered
   results or 422, never silently unfiltered).
6. **Prove it on real metal.** A grounded ask against `.43` over the
   real archive: the answer cites sources, the cited decision opens,
   and a control-vs-treatment shows selection changed the answer
   (the house LLM-proof rule).

## Out of scope

- Vectors/embeddings (deferred by charter).
- New UI (05 renders search + citations).
- Indexing transcripts again (already done) or external corpora.
- Ranking tuning beyond bm25 + recency tiebreak — good defaults,
  measured honestly, no ML.

## Acceptance

- A text query over a seeded multi-year archive returns ranked hits
  across all three kinds with refs + snippets; time and project
  filters work; empty results are an honest zero.
- The index rebuild command is idempotent and its counts match the
  tables; triggers keep it fresh under create/update/tombstone
  (proven per kind).
- A grounded project ask carries per-source blocks; the hydration
  names how many matched but were left out; with no query the
  recency fallback is labeled as such.
- The `q`/`search` defect is fixed with a regression test; meeting
  search proven live from the window.
- Live `.43` evidence: cited answer, control-vs-treatment delta,
  latency printed.
- Full suite green; spine byte-unchanged.

## Test plan

- **Unit:** trigger freshness per kind; ranking determinism; filter
  math; overflow counting.
- **Integration:** cross-kind search route with principals; grounding
  selection relevance vs recency fallback; the wire regression test.
- **Live (evidence):** real archive query + grounded ask on `.43`
  with citations followed to their objects.

## Chef's notes

- Tombstoned notes and severed-source decisions must drop out of the
  index via triggers, not via query-time filters that will be
  forgotten once.
- bm25 across kinds needs per-kind normalization or artifacts (long)
  drown decisions (short). Rank within kind, interleave honestly, and
  say so in the code where the ranker lives.
- The grounded-ask evidence should reuse the Phase-53
  control-vs-treatment shape: same question, grounding on/off, model
  output demonstrably different, both runs receipted.
