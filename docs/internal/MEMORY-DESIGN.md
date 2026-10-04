# The memory design

Hindsight's ideas, built native in HoldSpeak.

- **Ruling (owner, 2026-10-03):** "I'd honestly go into building B. We need to be
  robust with this solution." B = the same ideas inside HoldSpeak's own database,
  engine router, egress badges and People custody. No second database. No
  Hindsight server.
- **Status:** build design. Slice 1 is in build (schema, sweep, chunk index,
  vector retriever, fusion, benchmark, the conductor, the `memory.embed` engine). Each slice in section 8 is one PR or two.
- **Source of ideas:** <https://github.com/vectorize-io/hindsight> (MIT), read at
  a shallow clone on 2026-10-03. Paper: arXiv 2512.12818 (linked from their
  `README.md:5`; not read for this design).
- **Paths:** `H/` = `hindsight-api-slim/hindsight_api/` in their repo. All other
  paths are ours.

---

## 0. The facts this design stands on

### 0.1 Our tree today

| Question | Fact | Where |
|---|---|---|
| What is "memory" today? | A read-only keyword search over 11 tables. Nothing writes "to memory". | `holdspeak/db/memory.py:20-32`, `:435` |
| Is there a time filter? | Yes: `time_from` / `time_to` are already search arguments. Nothing reads a time phrase out of the question. | `holdspeak/db/memory.py:441-442`, `holdspeak/services/memory_service.py:24-25` |
| Is there a relation walk? | Yes: one hop over real relationships (meeting provenance, decision lineage, thread refs). No LLM. | `holdspeak/db/memory.py:938` |
| Are there text embeddings? | No. The one `embedding` column is the speaker voice print. No embedding capability, no embedding dependency. | `holdspeak/db/schema.py:197`; `pyproject.toml:40-70` |
| How is a model call routed? | A capability id resolves through its assignment to a route plan; the first leg names a deployment revision; `InferenceRunner.invoke` runs it and writes the receipt. | `holdspeak/services/project_update_service.py:1045-1075`, `:1148`, `:1426-1432`; `holdspeak/services/inference_route_plan_service.py:209`; `holdspeak/kernel/inference_runner.py:152` |
| What is a capability? | A typed job: input modalities, output schema, allowed boundaries (`local`, `private_network`, `mesh`, `cloud`), retry policy. 41 are built in. A non-chat one exists already (`speech.transcribe`, `local` only). | `holdspeak/inference_capabilities.py:27`, `:379-402`, `:1031`, `:1063` |
| Where does the egress badge come from? | The receipt names `winning_boundary`. The web lamp maps a boundary to LOCAL / LAN / PAIRED / MESH / CLOUD / NO MODEL. | `holdspeak/services/inference_fallback_controller.py:1003`; `web/src/desk/inferenceEgress.ts:9-26`; Constitution Article III, `docs/internal/CONSTITUTION.md:85-91` |
| What is the background queue? | `intel_jobs`, one drainer thread started by the hub. It is keyed to a meeting (`meeting_id NOT NULL REFERENCES meetings`). It cannot hold a job about a note or a project. `plugin_run_jobs` is meeting-keyed too. | `holdspeak/db/schema.py:149-172`, `:328-342`; `holdspeak/db/intel.py:508`; `holdspeak/intel_queue_conductor.py:105`; `holdspeak/web_server.py:1397-1421` |
| How does the queue retry? | 30 s base, 900 s cap, 6 attempts. | `holdspeak/intel_queue.py:27-29` |
| What does People custody forbid? | People records live in a separate AES-GCM file. Policy allows local READ and WRITE only; INFERENCE and SEARCH_PERSIST are refused. | `holdspeak/people/store.py:1`, `:19`; `holdspeak/people/policy.py:13-23`, `:45-57` |
| What else is kept out of memory today? | Sensitive thread parts, drafts, parked meetings, notes promoted to context. | `holdspeak/db/memory.py:190-201`, `:833` |
| Is there a secret scrubber? | Yes, for send receipts: one regex (bearer, token=, GitHub, Slack, SendGrid, Atlassian). | `holdspeak/services/channel_contract.py:142-146` |
| How does the schema change? | Declarative, additive only. Edit `SCHEMA_SQL`; the reconcile creates missing tables and columns on open. Never DROP, never DELETE. | `holdspeak/db/reconcile.py:1-8`; `holdspeak/db/schema.py:7-11` |

### 0.2 Measured on this Mac (2026-10-03)

| Probe | Result |
|---|---|
| SQLite in our runtime (`uv run python`, CPython 3.14.2) | 3.50.4; FTS5 on |
| Loadable extensions | `enable_load_extension(True)` works in this build. `sqlite_vec` is not installed. |
| numpy (a core dependency, `pyproject.toml:43`) | 2.3.5 |
| Plain scan, 50,000 vectors × 384 float32 (77 MB): dot product + top 50 | 47 ms on the first run |
| Plain scan, 50,000 × 768 float32 (154 MB) | 8 ms (warm) |
| Plain scan, 10,000 × 384 | 6 ms |
| `llama-cpp-python` | 0.3.35 in the owner's venv; it is in the `meeting` and `dictation-llama` extras (`pyproject.toml:91-92`, `:110-111`), not in core |
| A seeded desk (`holdspeak seed`, throwaway HOME) | 226 tables; 10 notes; 0 meetings, 0 segments. The seed is a starter desk and says nothing about scale. |

**Scale, by reasoning (not measured):** a 45-minute meeting is about 6,500 words,
so about 35 chunks of 1,200 characters. Fifteen meetings a week give about 500
chunks a week, 25,000 a year. Notes, threads, decisions and updates add a few
thousand a year. So 10,000 to 50,000 chunks is four months to two years of one
user's desk. At 256 dimensions that is 10 to 51 MB of vectors. A plain scan is
fast enough; no vector index is needed.

### 0.3 How Hindsight does it (what we take)

| Idea | How they do it | Where |
|---|---|---|
| Fact extraction | One LLM call per chunk (3,000 chars). "Extract SIGNIFICANT facts… Be SELECTIVE." Each fact: what / when / where / who / why. Relative dates become absolute. | `H/config.py:1629`; `H/engine/retain/fact_extraction.py:1058-1101` |
| Time on a fact | `occurred_start` / `occurred_end` for events; `mentioned_at` = the document's date. | `H/engine/retain/fact_extraction.py:1102-1106`, `:2229-2233`, `:2329-2331` |
| Entity resolution | Score = 0.5 × name similarity + 0.3 × shared neighbours + 0.2 × closeness in time (7 days). Match at 0.6. A per-token guard keeps "John Smith" and "Jane Smith" apart. | `H/engine/memories/pg/entity_resolver.py:1309-1344`, `:82-85` |
| Idempotent retain | A document id upsert replaces the old document; only changed chunks are done again. | `H/engine/retain/fact_storage.py:204-208`; `H/engine/retain/orchestrator.py:1385-1390` |
| Four retrievers | Vector + BM25 in one query; link expansion over entity / semantic / causal links; a time retriever that parses the question's range. | `H/engine/memories/pg/recall.py:28-60`, `:376`, `:553`; `H/engine/memories/pg/link_expansion.py:114-124`; `H/engine/query_analyzer.py:402-424` |
| Fusion | Reciprocal rank fusion, `score = Σ 1/(k + rank)`, k = 60. | `H/engine/search/fusion.py:29-33` |
| Rerank | Cross-encoder `ms-marco-MiniLM-L-6-v2`, then boosts for recency, time match and proof count (0.2 / 0.2 / 0.1). | `H/config.py:1275`; `H/engine/search/reranking.py:35-37`, `:300-303` |
| Budget | `max_tokens` (default 4096) cuts the ranked list. | `H/engine/memory_engine.py:8636`, `:10141-10149` |
| Observations | A background job reads new facts, 8 per call. Output: `creates`, `updates`, `deletes`, each with a reason and source fact ids. Rules: prefer update over create; one facet per observation; keep history. The old text goes to a history table. | `H/engine/consolidation/prompts.py:38-56`, `:113-115`; `H/engine/consolidation/consolidator.py:2761`, `:2841-2847` |
| Mental models | A stored answer to a standing question. Stale when a memory in scope is newer than `last_memory_seen_at`. Refreshed after consolidation. | `H/alembic/versions/o1a2b3c4d5e6_oracle_baseline.py:239-268`; `H/engine/memory_engine.py:20043-20050`; `H/engine/consolidation/consolidator.py:2154-2184` |
| Reflect | Reads mental models first, then observations, then raw recall. Stops early when the models are fresh. | `H/engine/reflect/agent.py:1121-1133`, `:1468-1480` |
| Banks | A `bank_id` on every table. | `H/alembic/versions/o1a2b3c4d5e6_oracle_baseline.py:45-60` |
| Memory defense | Regex only, before extraction: API keys, tokens, DB URLs, PEM keys, JWT, card numbers (Luhn), SSN. Actions: allow / redact / block. | `H/extensions/memory_defense.py:24-52`, `:169-235`; `H/extensions/builtin/memory_defense_regex.py:25-54` |
| Defaults | Embedding `BAAI/bge-small-en-v1.5`, 384 dimensions. Vector index HNSW (Postgres). | `H/config.py:1212`, `:1271` |

---

## 1. Goals and non-goals

**Goal:** every process on the Desk can remember and can be remembered. A
question in different words finds the right source. A standing question has a
standing answer.

**Robust means, and each line is a test:**

1. **One database.** All memory tables are in the main SQLite file.
2. **Works with no engine.** With no embedding engine and no extraction engine,
   recall is today's keyword search plus the relation walk and the time filter.
   No face shows an error.
3. **Nothing leaves the device** unless the assigned engine is remote. Then the
   receipt names the boundary and the face shows the lamp.
4. **People content is never indexed in the clear.** Nothing from the People
   store becomes a chunk, a vector, a fact, an observation or a page.
5. **Every memory item points at its source.** A chunk, a fact, an observation
   and a page each carry refs the Desk opens.
6. **Rebuildable.** Memory is an index, not a second source of truth. Drop every
   `memory_*` row and one command builds it again from the source tables.
7. **A failed or half-done job never corrupts recall.** A job writes its results
   and its ledger stamp in one transaction. Recall reads committed rows only.

**Non-goals:** a general agent-memory product; many users or tenants; a second
store; an always-on LLM for recall (recall makes zero LLM calls); a new face
before the owner's canvas.

---

## 2. Data model

Eleven new tables, all `memory_*`, all added to `SCHEMA_SQL`
(`holdspeak/db/schema.py`). The reconcile creates them on open. No migration
code. Source tables do not change.

**Rule for derived rows:** the additive-only rule protects the schema and the
owner's data. Chunks, vectors and facts are derived, so a job may replace them.
Observations and pages are never replaced without a history row.

```sql
-- The ledger: one row per source object memory has seen.
memory_sources(
  source_ref TEXT PRIMARY KEY,      -- 'meeting:<id>', 'note:<id>', 'update:<id>' ...
  kind TEXT NOT NULL,
  title TEXT NOT NULL DEFAULT '',
  occurred_at TEXT,                 -- when the thing happened (meeting start, send time)
  content_sha TEXT NOT NULL,        -- hash of the admitted, redacted text
  chunker_version INTEGER NOT NULL,
  extracted_sha TEXT,               -- content_sha at the last good extraction
  extractor_version INTEGER,
  state TEXT NOT NULL DEFAULT 'live',   -- live | gone (source deleted, parked or made sensitive)
  updated_at TEXT NOT NULL
)

memory_chunks(
  id TEXT PRIMARY KEY,              -- '<source_ref>#<ordinal>'
  source_ref TEXT NOT NULL,
  ordinal INTEGER NOT NULL,
  anchor TEXT NOT NULL DEFAULT '',  -- where to open: segment id, message id, section
  text TEXT NOT NULL,               -- redacted
  occurred_at TEXT,
  content_sha TEXT NOT NULL
)
memory_chunks_fts  -- FTS5 over memory_chunks(text); keyword search for the new source kinds

-- One table of vectors for chunks, facts, observations and pages.
memory_embeddings(
  item_kind TEXT NOT NULL,          -- chunk | fact | observation | page
  item_id TEXT NOT NULL,
  model_id TEXT NOT NULL,           -- the deployment's model name + dimension
  dim INTEGER NOT NULL,
  vector BLOB NOT NULL,             -- float32, unit length
  content_sha TEXT NOT NULL,
  PRIMARY KEY (item_kind, item_id, model_id)
)

memory_entities(
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,               -- person | project | system | org | topic
  name TEXT NOT NULL,               -- as the plain source wrote it
  name_key TEXT NOT NULL,           -- lower case, folded
  aliases_json TEXT NOT NULL DEFAULT '[]',
  first_seen TEXT, last_seen TEXT,
  mention_count INTEGER NOT NULL DEFAULT 0
)

memory_facts(
  id TEXT PRIMARY KEY,
  source_ref TEXT NOT NULL,
  chunk_id TEXT NOT NULL,
  kind TEXT NOT NULL,               -- state | event
  text TEXT NOT NULL,               -- one full sentence, names resolved, dates absolute
  subject_entity_id TEXT,           -- an id, never a copied name
  predicate TEXT NOT NULL,          -- the "what"
  object_entity_id TEXT,
  object_text TEXT NOT NULL DEFAULT '',
  occurred_start TEXT, occurred_end TEXT,   -- when it happened
  mentioned_at TEXT,                -- when the source said it
  confidence REAL NOT NULL DEFAULT 0.5,
  extractor_version INTEGER NOT NULL,
  state TEXT NOT NULL DEFAULT 'live',       -- live | retired
  consolidated_at TEXT
)

-- Links: a fact to every entity it names.
memory_fact_entities(fact_id TEXT, entity_id TEXT, role TEXT,   -- subject | object | mention
                     PRIMARY KEY (fact_id, entity_id, role))

memory_observations(
  id TEXT PRIMARY KEY,
  scope_kind TEXT NOT NULL,         -- project | person | desk
  scope_id TEXT NOT NULL DEFAULT '',-- project id | memory_entities.id | ''
  text TEXT NOT NULL,               -- the belief, one facet
  state TEXT NOT NULL DEFAULT 'current',    -- current | superseded | disputed | retired
  superseded_by TEXT,
  proof_count INTEGER NOT NULL DEFAULT 0,
  first_seen TEXT, last_seen TEXT,
  boundary TEXT NOT NULL DEFAULT '',-- the egress boundary of the call that wrote it
  consolidator_version INTEGER NOT NULL,
  updated_at TEXT NOT NULL
)
memory_observation_evidence(observation_id TEXT, fact_id TEXT,
                            stance TEXT NOT NULL,   -- supports | contradicts
                            added_at TEXT NOT NULL,
                            PRIMARY KEY (observation_id, fact_id))
memory_observation_history(id INTEGER PRIMARY KEY AUTOINCREMENT, observation_id TEXT,
                           at TEXT, prior_text TEXT, prior_state TEXT,
                           reason TEXT, fact_ids_json TEXT)   -- append only

memory_pages(
  id TEXT PRIMARY KEY,
  scope_kind TEXT NOT NULL, scope_id TEXT NOT NULL DEFAULT '',
  slug TEXT NOT NULL,               -- 'open-risks', 'what-we-decided', 'what-i-owe'
  question TEXT NOT NULL,
  answer_md TEXT NOT NULL,
  sources_json TEXT NOT NULL,       -- refs the Desk opens
  built_at TEXT NOT NULL,
  last_memory_seen_at TEXT NOT NULL,
  boundary TEXT NOT NULL DEFAULT '',
  model TEXT NOT NULL DEFAULT '',
  writer_version INTEGER NOT NULL,
  UNIQUE (scope_kind, scope_id, slug)
)
memory_page_history(id INTEGER PRIMARY KEY AUTOINCREMENT, page_id TEXT, built_at TEXT,
                    answer_md TEXT, sources_json TEXT)   -- append only, last 20 kept in reads

memory_jobs(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT NOT NULL,               -- embed | extract | consolidate | page
  target TEXT NOT NULL,             -- a source_ref, or 'project:<id>', 'person:<entity id>', 'desk'
  input_sha TEXT NOT NULL,
  version INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'queued',    -- queued | running | done | failed
  attempts INTEGER NOT NULL DEFAULT 0,
  next_attempt_at TEXT,
  lease_expires_at REAL,
  last_error TEXT,
  boundary TEXT NOT NULL DEFAULT '',
  UNIQUE (kind, target, input_sha, version)
)
```

**Decisions in this model:**

- **No `project_id` on chunks or facts.** A meeting can be filed into a project
  later, and into more than one (`meeting_projects`, `schema.py:584`;
  `project_resources`, `:1635`). Project scope is computed at read time by the
  rule search uses today (`db/memory.py:1374`). Only observations and pages
  carry a scope, because they are written per scope.
- **A fact names entities by id.** The name is in `memory_entities` once. No
  People-store id is ever written to a memory table (section 5).
- **"Links" are `memory_fact_entities` plus the real relationships the walk
  already follows** (`db/memory.py:938`). No stored semantic or temporal links:
  the vector and time retrievers compute those at read time. Alternative:
  Hindsight's `memory_links` table (`o1a2b3c4d5e6_oracle_baseline.py:220-236`);
  not needed at one user's scale.
- **Vectors are plain BLOBs, searched with numpy.** One matrix per model, built
  lazily, held in the hub process, refreshed when the embed job commits.
  Alternative: `sqlite-vec`; it loads in this runtime but adds a native
  dependency for no gain under 200,000 vectors.

---

## 3. Pipelines

One new conductor, `holdspeak/memory_conductor.py`, drains `memory_jobs`. It
copies the intel drainer's shape: one thread, started and stopped by the hub
lifespan, only in the process that owns the database
(`intel_queue_conductor.py:105-135`), same retry numbers
(`intel_queue.py:27-29`). Its jobs show in the Queue frame
(`intel_queue.py:40`). Alternative: widen `intel_jobs`; refused, it is
meeting-keyed and carries the meeting lease machinery.

### 3.1 RETAIN

**Trigger: a sweep, not hooks.** The conductor sweeps each source kind and
compares `(ref, content hash)` with `memory_sources`. A new or changed source
gets jobs. A producer may call `wake()` after a write so the sweep runs at once;
that is speed, not correctness. A missed hook can never lose a memory.
**Built (2026-10-04):** one seam, not a hook per producer. Every write ends in
one `desk_changed` send (`RuntimeServices._send_desk_changed`,
`runtime/composition.py`); that send gives `memory_conductor.wake()` the kind
and id of each change.

- **OFF costs nothing.** While `memory.embed` is unassigned a wake reads no
  source (one row read of the assignment head).
- **ON: the pass reads only what changed.** The conductor waits 2 s after a
  wake (`WAKE_GAP_SECONDS`), then runs `sweep_refs` over the named sources
  and embeds their chunks. N edits cost N source reads, whatever the size of
  the desk. A change kind that memory does not hold gives no ref.
- **The full sweep stays on the slow timer** (120 s) and on a changed
  assignment. A wake never moves that timer. The full sweep is what keeps
  correctness: a kind with no ref, a missed wake, the keyword-table scrub.

| Source kind | Table | Wake after | Chunks | Facts |
|---|---|---|---|---|
| Meeting transcript | `segments` | `save_meeting` (`db/meetings.py:426`) | by speaker turns, anchor = segment id | yes |
| Meeting summary + topics | `intel_snapshots`, `topics` (`schema.py:137`, `:128`) | `_on_intel_complete` (`intel_queue.py:359`) | one per summary, one per topic | yes |
| Decision (meeting, record, desk) | `decisions`, `decision_records`, `desk_decisions` | create / update | one | yes |
| Action item, commitment | `action_items`, `decision_commitments` (`schema.py:239`) | create / status change | one | yes |
| Note, Thought working note | `notes` | create / update | by paragraph | yes |
| Thread message | `thread_message_parts` (not sensitive, not draft) | message saved | one per message | yes |
| Artifact | `artifacts` | create | by heading | yes |
| Published update | `project_updates` (`schema.py:4162`), status published only | publish | by section | yes |
| Send | `channel_sends`, `project_update_deliveries` (`schema.py:4235`, `:4191`) | receipt written | one: what, to which destination, when | no (it is already a fact: written direct) |
| Prep | `project_briefs` (`schema.py:4522`) | brief saved | by section | no |
| The Brief | `monday_briefs` + items (`schema.py:2479`) | brief built | one per item | no |
| Calendar event | `calendar_events` (`schema.py:3717`) | ingest | one: title, time, series | no (written direct as an event fact) |
| Dictation | `dictation_journal` (`schema.py:856`) | entry saved | one per entry | no |
| Steward run, Ask answer | `steward_runs`, `ask_results` (`schema.py:4294`, `:2274`) | run / answer saved | one | no |
| Project item, workbench item, cadence | as today | create / update | one | no |

**Built (2026-10-04, slice 2):** the readers are in `memory/retain.py`
(`SOURCE_READERS`), the rules in `memory/admission.py`.

- Meeting summary and topics: the `meeting` reader. The summary is one
  chunk (anchor `summary`), each topic is one chunk (anchor `topic:<id>`).
- Commitments: no kind of their own. Each commitment writes its
  `action_items` row (task, owner, due) in the same transaction, and the
  `action` kind holds that row.
- The Brief: `brief_item`, one per `monday_brief_items` row. A row for a 1:1
  commitment is left out whole (People custody).
- Dictation: `dictation`, one per journal entry. A dry run is left out.
- Steward run: `steward_run`, a finished run only. The text is the outcome,
  the reason, the proposals and the action count, not the JSON.
- Ask answer: `ask_answer`, a Room ask (`project_ask_tasks`, the only Ask
  that keeps its question) with its answer, until he discards it. Other Ask
  answers are unkept output; an answer he keeps is an artifact.
- None of the four new kinds has a Desk window that opens one record:
  each is in `NO_WINDOW_REF_KINDS`.
- Keyword search for the four kinds reads `memory_chunks_fts`. The sweep
  writes it, so it works with no engine. The wake reaches `ask_answer`
  (change kind `ask_task`) and `steward_run` (change kind `steward`, on
  stop). The other writers send no change that names the row; the slow
  sweep (120 s) finds those rows.

**Steps, each idempotent and resumable:**

1. **Admit.** One function, `memory_admits(kind, row)`, holds every exclusion
   rule in one place: sensitive parts, drafts, parked meetings, promoted notes,
   unpublished updates. The FTS rebuild uses the same function.
2. **Redact** secrets (section 5), then hash. Same hash as the ledger: stop.
3. **Chunk.** 1,200 characters, cut on a turn, paragraph or heading; a short
   row is one chunk with its title in front. Replace the source's chunks and
   stamp the ledger in one transaction. This step needs no model, so keyword
   search over a new source kind works at once.
4. **Embed** (job `embed`). Batches of 64 chunks through the embedding
   capability. Vectors land with the chunk's `content_sha`; a vector whose sha
   does not match its chunk is ignored by recall and done again.
5. **Extract** (job `extract`). One LLM call per chunk of the "yes" kinds.
   Output schema, closed: `facts[] {text, kind, subject, predicate, object,
   occurred_start, occurred_end, confidence, entities[] {name, kind}}`. The
   prompt takes Hindsight's rules: be selective, resolve "he/she/they" to a
   name, write absolute dates (`fact_extraction.py:1058-1101`). The job writes
   the facts, resolves entities, retires the source's old facts and stamps
   `extracted_sha` + `extractor_version` in one transaction.
6. **Resolve entities.** Hindsight's score, without Postgres: candidates by
   `name_key` prefix and token overlap in SQL, then 0.5 × name ratio + 0.3 ×
   shared neighbours + 0.2 × closeness in time, match at 0.6, with the
   per-token guard (`entity_resolver.py:1309-1344`, `:82-85`). Below 0.6: a new
   entity. Never merge two entities by LLM guess.

**Versions.** `CHUNKER_VERSION`, `EXTRACTOR_VERSION`, `CONSOLIDATOR_VERSION` and
`PAGE_WRITER_VERSION` are integers in code. A bump makes the sweep see every
source as changed for that step only. The old rows serve recall until the new
ones commit.

**Rebuild.** `holdspeak memory rebuild` (the command exists for FTS,
`main.py:530`) clears `memory_*` derived rows and lets the sweep run.
Observation and page history tables are kept.

### 3.2 RECALL

No LLM call. One function behind the existing `MemoryRepository.search`
signature (`db/memory.py:435`); the route, the MCP tool and the chat tool do not
change.

1. **Scope.** Project (the existing rule), kinds, `time_from` / `time_to`,
   `exclude_refs`. Each retriever applies the scope before it ranks, so nothing
   from outside a project is ever a candidate.
2. **Four retrievers**, top 50 each:
   - **Keyword:** today's search, unchanged, plus `memory_chunks_fts` for the
     new kinds.
   - **Vector:** embed the question once; cosine over the model's matrix
     (chunks, facts, observations). Skipped when no engine is assigned or the
     embed call fails.
   - **Relation:** today's one-hop walk, plus an entity walk: entities named in
     the question → their facts → the facts' sources. Skipped when there are no
     facts yet.
   - **Time:** a small parser reads a time phrase from the question ("last
     week", "in September", "since Monday", "yesterday"); rows inside the range
     rank by closeness to its middle (`H/…/recall.py:553`). No phrase: skipped.
     Alternative: the `dateparser` package (`query_analyzer.py:402-424`); a new
     dependency for about twelve patterns.
3. **Fuse.** Reciprocal rank fusion over the lists that ran,
   `score = Σ 1/(60 + rank)` (`H/engine/search/fusion.py:29-33`). Hits fuse per
   source ref; the best chunk gives the snippet and the anchor.
4. **Boost, no rerank model.** Multiply by a recency boost and a proof-count
   boost (Hindsight's 0.2 and 0.1, `reranking.py:35-37`). Alternative: a
   cross-encoder; not in the first six slices (section 9).
5. **Budget.** The caller gives `max_chars`; the ranked list is cut whole-item.
   Drafters keep the bounds of `memory_context` (8 excerpts, 5,200 characters;
   `services/memory_grounding.py`, PR #768).
6. **Result.** Each hit: the existing `kind:id` key, title, snippet, anchor,
   `occurred_at`, and `found_by` (which retrievers). Drafters get only refs the
   Desk opens (`DESK_REF_KINDS`, PR #768). Each new source kind in slice 2 adds
   its opener and its entry to that tuple, fenced by the same web test.

### 3.3 CONSOLIDATE

Job `consolidate`, one per scope with new facts, after extraction.

- Input: up to 8 facts with no `consolidated_at`, plus the observations recall
  finds for them **inside the same scope**.
- Output, closed schema: `creates[]`, `updates[]`, each with `reason` and
  `fact_ids`; an update names `relation`: `supports`, `refines`, `supersedes` or
  `contradicts`. There is **no delete verb**.
- Rules from Hindsight's prompt: prefer update over create; one facet per
  observation; keep history; do no arithmetic (`consolidation/prompts.py:38-56`).
- Effects, in one transaction:
  - `supports`: add evidence; `proof_count` + 1.
  - `refines`: prior text to history; new text; add evidence.
  - `supersedes`: the old observation becomes `superseded`, `superseded_by` the
    new one. It stays readable.
  - `contradicts` with no clear winner: both become `disputed`.
- The check before the write is code, not trust: every `fact_id` must be in the
  input; every fact must be in the scope. A bad output fails the job; nothing is
  written.
- States are the Desk memory card states the face draws today: CURRENT,
  SUPERSEDED, DISPUTED (`services/recall_service.py:15-16`, `:60`, `:227`).
- A retired fact drops out of evidence. An observation with no live evidence
  becomes `retired` and leaves recall. Its history stays.

### 3.4 PAGES

A page is a standing answer. It is read with **no model call**.

- **Fixed set to start** (no page editor): per project: *What did we decide*,
  *What is open and who owes it*, *Risks and disputes*, *What changed this
  week*. Per person (the entity, plain sources only): *What I owe them*, *What
  they owe me*, *What we last discussed*. Desk-wide: *What I owe*, *What changed
  this week*.
- **Stale** when a fact or observation in scope is newer than
  `last_memory_seen_at` (`H/engine/memory_engine.py:20043-20050`).
- **Rewrite** (job `page`) after consolidation in that scope, at most once per
  page per hour. Input: current and disputed observations + top recall for the
  question, in scope. Output: `answer_md` + the refs it used. A sentence whose
  ref is not in the input is cut by code. The old page goes to history.
- **Read:** `memory_pages.read(scope_kind, scope_id, slug)` returns the answer,
  sources, `built_at`, `stale`, `boundary`. No engine: the last page stays, with
  its age. No page yet: the reader gets nothing and works as it does today.

### 3.5 REFLECT

Ask is the reflect step. No new agent loop.

- `ask_service` and the chat turn read, in order: the scope's pages, then
  current observations, then fused recall (`H/engine/reflect/agent.py:1121-1133`).
  They go into the grounding block the turn already has
  (`grounding.py:149`, `:259`, `:517`).
- The chat tool `memory.search` (`services/thread_tools.py:144`) stays the one
  tool; it now returns fused hits. One new tool, `memory.page`, reads a page.
- Not taken: Hindsight's 10-step tool loop, dispositions and directives
  (`H/config.py:1896`; `H/engine/reflect/prompts.py:170-190`).

---

## 4. Engines

Four new capabilities in `builtin_capability_definitions`
(`inference_capabilities.py:1031`), all in the existing **Background** group, so
Settings shows them where the other background jobs are and one starter bundle
assigns them.

| Capability | Job | Output | Boundaries |
|---|---|---|---|
| `memory.embed` | text → vectors | `embedding` | all four; the default assignment is local |
| `memory.extract` | chunk → facts | structured | all four |
| `memory.consolidate` | facts → observation changes | structured | all four |
| `memory.page_write` | observations + recall → answer | structured | all four |

Reflect uses the existing `ask.answer` and `chat.turn`.

**Default embedding model:** `nomic-embed-text-v1.5`, GGUF `Q8_0`, **146 MB**
(`nomic-ai/nomic-embed-text-v1.5-GGUF`, file size read from Hugging Face on
2026-10-03). 768 dimensions, stored cut to **256** and made unit length (the
model is trained for that cut). Prefixes `search_document:` and `search_query:`.

- **How it runs:** in the hub process through `llama-cpp-python` in embedding
  mode. No server, no egress; boundary `local`, lamp LOCAL.
- **How the hub gets the model (owner ruling 2026-10-04: no signing):** the
  packaged catalogue is ed25519-signed and its key is not in the repository,
  so this one model class has its own local, unsigned source
  (`holdspeak/memory/local_model.py`). The hub adopts a copy on this device
  (`~/.local/share/holdspeak/models/embed/`, `~/.cache/holdspeak-models/embed/`,
  or `HOLDSPEAK_MEMORY_EMBED_MODEL`) or downloads the file from its public
  Hugging Face URL at a pinned revision. The pinned sha256 is the integrity
  check; no signature claim is made. A download continues a partial file. A
  file with a different hash is renamed `.invalid` and is never used. The
  signed catalogue is not changed.
- **The row says what the press does.** "On this device" is said only for a
  regular file whose sha256 is verified (hashed once, kept by path, size and
  modification time). A file with the right size and a different hash is
  shown as a download, and the press downloads.
- **No symbolic links.** The hub writes only into its own model directory.
  The directory, the `.part` file and the final file must not be links; the
  part file is opened with `O_NOFOLLOW` (and `O_EXCL` when new). A link in
  the directory stops the press before any request leaves. Only a regular
  file is adopted.
- **A download is egress and needs the press.** It starts only in
  `MeaningSearchService.turn_on` (`POST /api/memory/meaning-search/turn-on`),
  only when no copy with the pinned hash is on this device. Each download
  request is one `external.egress` operation with a receipt (connector
  `model-download`, destination `huggingface.co`, data class
  `model_file_request`), for the owner who pressed.
- **One step.** Turn on: get the file → make the profile → assign
  `memory.embed` → wake the conductor. Turn off: clear the assignment; keyword
  search continues. State (`GET /api/memory/meaning-search`): OFF, DOWNLOADING
  n%, INDEXING n of m (chunks with a current vector, from the index), ON. The
  download state is in the hub process: after a restart the state is OFF and
  the partial file stays for the next press.
- **The row.** Models (the Concierge window), THE SET: one row "Meaning
  search" after the capability groups (`MeaningSearchRow.tsx`). It composes
  the species of the other SET rows: the ledger row, the state chip (OFF,
  DOWNLOADING n%, INDEXING n OF m, ON), the egress chip (THIS DEVICE, or
  HUGGINGFACE.CO when the press downloads) and one library Button (Turn on /
  Turn off). No modal.
- **The `embedding` claim.** `memory.embed` requires the capability class
  `embedding`, so only a profile with that claim can be assigned to it. A
  profile with the claim serves no other capability (`embedding_model_only`),
  so the embedding model is not offered for chat. Not done: a product path to
  put the claim on a remote endpoint profile (a LAN or cloud `/v1/embeddings`).
- **How it is assigned:** the same assignment a chat capability has
  (`inference_assignment_service.py:382`). A remote OpenAI-compatible endpoint
  (`/v1/embeddings`; the owner's LAN llama.cpp, or a cloud key) is also a valid
  deployment. Then the receipt says `private_network` or `cloud`, and the lamp
  says LAN or CLOUD.
- **All calls go through `InferenceRunner.invoke`** (`inference_runner.py:152`)
  with a small embedding adapter. One invocation per batch of 64. That is the
  one path that gives the admission and the receipt.
- **None assigned:** no vectors. Recall runs keyword + relation + time. Chunks
  are still built. When an engine arrives, the sweep queues the backlog.
- **Model changed:** vectors are keyed by `model_id`. The new model's vectors
  are built in the background; recall uses the assigned model's vectors where
  they exist and keyword for the rest. Old vectors are removed when the new set
  is complete.
- Alternative default: `bge-small-en-v1.5` `Q8_0`, 37 MB, 384 dimensions,
  Hindsight's choice (`H/config.py:1212`); smaller, English only, 512 tokens.

**Extraction, consolidation, pages:** whatever chat-class engine the owner
assigned to the Background group. No engine: those jobs wait in `queued`; the
queue frame says so; recall still works on chunks.

---

## 5. Custody and safety

| Concern | Rule | How it is fenced |
|---|---|---|
| **People store** | Nothing from `people.v1.sqlite3` is admitted. No memory table holds a People id. A person in memory is an entity made from plain sources (a meeting, a decision, an action item). | `memory_admits` has no People kind. A test writes a People note with a unique word, runs the full pipeline, and finds the word in no `memory_*` row. |
| **Person scope** | "Memory about Dana" = the People service gives her names and aliases in memory at read time (it does this today, `people_service.py:1102`, `:1231`); recall maps them to entity ids. 1:1 notes are joined by the People service at read time (`people_service.py:376`), never written to memory. | Test: Prep shows the People note and the plain memory together; the database holds the note only in the People file. |
| **Sensitive threads, drafts, parked meetings, promoted notes** | Excluded by `memory_admits`, the same rule for FTS and chunks. A source that becomes sensitive or parked: ledger `state='gone'`, its chunks, vectors and facts removed in the same sweep. | Test per rule, through the real producers. |
| **Secrets ("memory defense")** | Redact before the hash, so before storage, embedding and extraction. One module, `holdspeak/memory/defense.py`: our `_SECRET` regex (`channel_contract.py:142-146`) plus Hindsight's set: PEM keys, JWT, database URLs with a password, card numbers with a Luhn check (`H/extensions/memory_defense.py:169-235`). Action: redact only. No block, no policy file, no webhook. | Test: a note with a token; the chunk, the FTS row and the prompt hold `[redacted]`. |
| **Project isolation** | Scope is applied inside each retriever, before fusion. Consolidation and pages run per scope and code checks every fact is in scope. A drafter that passes a project never gets a ref from outside it (the `memory_context` contract, PR #768). | Test: two projects, one unique word each; a draft for A never holds B's word, in recall, in an observation or in a page. |
| **Injected text** | A meeting transcript can say "ignore your instructions". Chunks go into prompts inside the marked `[MEMORY]` block as data, as today. Extraction output is a closed schema; code checks every ref. Hindsight has no detector either. We build none. | Schema validation on every job. |
| **Egress** | Every memory model call has a receipt with its boundary. Observations and pages keep the boundary of the call that wrote them. | Test: a remote assignment gives a non-local boundary on the page row. |
| **MCP** | `memory.search` keeps its name and its read right (`mcp/families/memory.py:15`). Two read tools are added: `memory.page` and `memory.observations`. No write tool: an outside agent adds memory by creating a note, as today. All three flow through `MemoryService` (one service layer). | The census tests classify the two new tools as evidence reads. |

---

## 6. How every process uses it

`ctx` = `memory_context(db, project_id=…, query=…)` (PR #768), which gets fused
recall in slice 1 with no change at the call site. `page` =
`memory_pages.read(…)`. Retain is always the sweep; no process calls a "write to
memory" function.

| Process | What it retains | What it recalls | API |
|---|---|---|---|
| Meeting summary | transcript; summary and topics (new) | earlier decisions and open items for the meeting's project, before it summarises | `ctx` in `meeting_intel_service` |
| Decisions | all three decision kinds; facts | "is there an earlier or conflicting decision?" at create time → a ref on the card | `search(kinds=decision…)`; later the project's *What did we decide* `page` |
| Action items, follow-through | action items, commitments | who else owes the same thing; the source meeting | `search`; *What is open* `page` |
| 1:1 Prep | the Prep brief (plain part) | the person's pages + recall by the person's entity; People notes joined at read time | `page(person)`, `ctx` |
| The Brief | brief items | *What changed this week* and *What I owe* pages | `page(desk)`, `page(project)` |
| Updates | published updates; sends | the last update's claims; what changed since | `ctx` (PR #768 does this), `page(project, what-changed)` |
| Dictation | journal entries (chunks only) | names and terms for the active project → spelling hints | `search(project, limit small)`; no LLM on the hot path |
| Thoughts | the working note | related notes, decisions, earlier thoughts while it develops | `ctx` in `refinement_thought_service` |
| Ask / chat | thread messages; Ask answers | pages → observations → fused recall | grounding; tools `memory.search`, `memory.page` |
| Steward | steward runs; workbench artifacts | the project's pages before it plans a step | `page(project)`, `ctx` |
| Palette (⌘K) | — | content search under the title matches | `GET /api/memory/search` (fused, no LLM) |
| Desk memory face | — | cards: observations (CURRENT / SUPERSEDED / DISPUTED) with evidence; OWED from the *What is open* page | `GET /api/memory/recall` (`recall_service`) |
| Send | sends and delivery receipts | "did I send this before, to whom?" | `search(kinds=send)` |
| Calendar | events | the meetings and decisions tied to a series | `search` with the time retriever |
| MCP | (via `desk.create`) | search, a page, observations | `memory.search`, `memory.page`, `memory.observations` |

---

## 7. Evaluation

**A fixed benchmark, in the tree:** `tests/memory_bench/`.

- **Corpus:** about 60 sources, made through the real producers on a throwaway
  hub: `save_meeting`, the intel completion path, `POST /api/decisions`,
  `POST /api/notes`, a published update, a send receipt, a calendar ingest. No
  hand-inserted rows. Two projects, so isolation is in the benchmark.
- **Questions:** 40, each with the refs that answer it:
  15 same-word, 15 paraphrase (no shared content word with the source: keyword
  search fails these by construction), 5 time ("what did we decide last week"),
  5 relation ("what does Dana owe on Atlas").
- **Measures:** recall@5, recall@10, MRR, per group. The file
  `tests/memory_bench/baseline.json` holds the numbers for today's keyword
  search; a slice's PR shows before and after.
- **FAST tier:** a deterministic stub engine that reads real-model vectors for
  the fixed corpus and questions from a checked-in fixture, keyed by text hash.
  A text with no fixture fails the test. So FAST measures real meaning with no
  model, in under 10 seconds. Extraction, consolidation and page jobs replay
  recorded real-model outputs the same way.
- **Nightly tier:** the same benchmark with the real model
  (`requires_llama_cpp`), plus a drift check: a fresh vector must be within
  cosine 0.98 of its fixture.
- **Gates:** same-word recall@5 never below baseline. Paraphrase recall@5 from
  the baseline (expected near zero; to be measured in slice 1) to at least 0.7.
  The targets are targets; no number here is measured yet.

---

## 8. Build slices

Each is one PR, in this order. Each acceptance test runs through real producers.

| # | Slice | Size | Files | Acceptance test |
|---|---|---|---|---|
| 1 | **Embeddings + chunk index + fused recall** behind `memory.search`. No face change. Ledger, chunks, vectors, jobs, the conductor (embed only), `memory.embed`, the embedding adapter, RRF, `defense.py`, the benchmark and its baseline. | **L** | `holdspeak/db/schema.py`, `holdspeak/db/memory.py`, new `holdspeak/db/memory_index.py`, new `holdspeak/memory/{chunker,defense,embedder,fusion,retain}.py`, new `holdspeak/memory_conductor.py`, `holdspeak/web_server.py`, `holdspeak/inference_capabilities.py`, `holdspeak/inference_setup_catalog.py`, `holdspeak/main.py`, `tests/memory_bench/` | Paraphrase recall@5 ≥ 0.7 with the fixture engine; same-word not below baseline; with no engine the result equals today's search hit for hit; a job killed mid-batch leaves recall equal to before; `memory rebuild` gives the same hits; the People and secret fences. |
| 2 | **Time phrase + new source kinds**: summary, topics, updates, sends, Prep, Brief items, calendar, dictation, steward runs, Ask answers. `memory_chunks_fts`. An opener and a `DESK_REF_KINDS` entry per kind that has a window. | **M** | new `holdspeak/memory/timeparse.py`, `holdspeak/memory/retain.py`, `holdspeak/db/memory.py`, `holdspeak/services/memory_grounding.py`, `web/src/desk/openObject.ts`, `web/src/desk/__tests__/memoryRefsOpen.test.ts` | The inventory's repro R2 turns green (a word only in the summary is found). "What did I send last week" returns the send. The five time questions pass. |
| 3 | **Retain: fact extraction on the queue.** `memory.extract`, facts, entities, entity resolution, the entity walk in the relation retriever. | **L** | new `holdspeak/memory/{extract,entities}.py`, `holdspeak/memory_conductor.py`, `holdspeak/db/memory_index.py`, `holdspeak/inference_capabilities.py`, `holdspeak/intel_queue.py` (queue frame) | The five relation questions pass. A second run over the same source makes no new rows. An extractor version bump replaces facts with no gap in recall. "John Smith" and "Jane Smith" stay two entities. No engine: jobs wait, recall unchanged. |
| 4 | **Consolidation into observations.** `memory.consolidate`, evidence, history, states. Read API only; no face. | **M** | new `holdspeak/memory/consolidate.py`, `holdspeak/db/memory_index.py`, `holdspeak/services/memory_service.py`, `holdspeak/mcp/families/memory.py` | Three meetings that say the same thing give one observation with `proof_count` 3. A later reversal gives SUPERSEDED with a history row, never an overwrite. A fact from project B is refused as evidence in project A. |
| 5 | **Pages + readers** (Prep, Brief, Room, Desk memory face). `memory.page_write`. **The faces need the owner's canvas first** (UX-CANON: design on the canvas before build). The page job, the API and the drafters' use need no canvas. | **L** | new `holdspeak/memory/pages.py`, `holdspeak/services/{recall_service,preparation_brief_service,monday_brief_service,meeting_intel_service,project_steward_service}.py`, `holdspeak/web/routes/memory.py`, `web/src/features/project-room/recall/RecallFace.tsx` (after the canvas) | A page read makes zero model calls (census test). A new decision makes the page stale, then fresh after the job. Every sentence in a page has a ref the Desk opens. With no engine the last page is served with its age. |
| 6 | **Palette and Ask use.** Content search in ⌘K; Ask reads pages → observations → recall; `memory.page` chat tool. | **M** | `web/src/desk/components/DeskToolShelf.tsx`, `holdspeak/services/{ask_service,thread_tools}.py`, `holdspeak/grounding.py` | ⌘K finds a note by a paraphrase. Ask in a project answers from the page with refs, and never cites another project. |

Slices 1 and 2 give the owner better search with no LLM in the loop. Slices 3
to 5 are where the engine quality matters; each ships dark until its benchmark
group passes.

---

## 9. Risks, and what we do not build

**Risks**

| Risk | What we do |
|---|---|
| A small local model extracts poor facts. | Facts never replace chunks: recall always has the chunk path. Extraction ships only when the relation questions pass with the owner's assigned engine. |
| Entity resolution merges two people. | Threshold 0.6 with the token guard; no LLM merge; a merge is never needed for recall to work (chunks). An owner "these are one person" verb is a later face. |
| Consolidation writes a wrong belief. | Every observation shows its evidence; history is append only; code checks scope and ids. |
| `InferenceRunner` cost per call is too high for one question embedding. | Measure in slice 1. If over 50 ms, the query embed reuses the engine handle admitted by the last batch receipt. |
| The backlog on a first run (a year of meetings) holds the engine. | The conductor yields to any live meeting or chat call and runs oldest-last; chunks and keyword work at once. |
| 154 MB of full-size vectors in the hub. | Stored at 256 dimensions: 51 MB at 50,000 chunks. |
| Two keyword paths (five old FTS tables + `memory_chunks_fts`). | Accepted for now. Folding the old tables into the chunk FTS waits until the benchmark shows equal recall; the old tables are then parked, not dropped. |

**We deliberately do not build**

- A second database, a Hindsight server, their HTTP API or their clients.
- Banks, tenants, per-bank config. One user; scope is project / person / desk.
- A vector index (HNSW, `sqlite-vec`). A plain scan is enough to 200,000 vectors.
- A cross-encoder reranker. It needs a second model and a torch-class
  dependency. Revisit only if the benchmark stalls after slice 3.
- Stored semantic, temporal or causal links.
- Dispositions, directives, the multi-step reflect agent.
- Any index of People-store content, in any form.
- A memory write API or a "remember this" MCP tool. Memory follows the Desk's
  objects; to make a memory, make a note.
- A page editor or custom standing questions (first: the fixed set).
- Block actions, policy files or webhooks in memory defense.
- A new face before the owner's canvas.

---

## Measured in slice 1 (2026-10-03, this Mac: Apple M2 Max, load average 75+)

| Probe | Result |
|---|---|
| `llama-cpp-python` 0.3.35 loads `nomic-embed-text-v1.5` `Q8_0` (146,146,432 bytes) in process | Yes. Load 0.78 s. Pooling type 1 (mean). Output 768 values, not unit length. |
| Throughput, 100 short texts in batches of 16 | 0.26 s: about 380 texts each second. One text at a time: about 130 each second. |
| One question embedded | 7.5 ms. `memory.search` with the vector retriever on a small desk: 8 ms in all. |
| A batch and one text give the same vector | Yes (cosine 1.0). |
| **Trap:** the default `n_ubatch` (512) | llama.cpp ABORTS the process (`GGML_ASSERT ... encoder requires n_ubatch >= n_tokens`) when one call carries more than 512 tokens. The engine must set `n_ubatch = n_batch = n_ctx`. |
| The 256 cut (cut, then unit length) against 768, on the benchmark | Paraphrase recall@5 0.812 for both. recall@10 0.875 (256) and 0.938 (768). Same-word 1.000 for both. |
| Two bare phrases ("the accounting cutover" and "ledger migration") | NOT clearly apart from unrelated phrases (cosine 0.41 against 0.34 to 0.44 at 256). The model needs a sentence on one side: the question "when is the ledger migration" ranks the cutover note first of 10 with a margin of 0.05. |
| Benchmark (`tests/memory_bench/`, 33 sources, 29 questions), keyword + relation | same-word recall@5 1.000, MRR 0.827; paraphrase recall@5 0.000 |
| Benchmark, fused (RRF k = 60), 256 values | same-word recall@5 1.000, MRR 0.923; paraphrase recall@5 0.812, recall@10 0.875, MRR 0.421 |
| One question through `InferenceRunner.invoke` (real router, real model, warm) | 6 to 13 ms, with a receipt. The first call loads the model. Under the 50 ms limit of section 9, so the question goes through the runner too. The same question again is served from a small cache in the hub. |
| `InferenceRunner.invoke` with a non-chat adapter | Works with no change to the runner. The adapter gets the runner-built engine and reads its model path (local) or its client (endpoint). |
| A SERVICE principal on the direct runner path | Refused. The conductor runs as an OWNER principal named `memory-conductor`, as the other conductors do. |

**Rules found in the build (slice 1, part 2):**

- **`memory.embed` is used only with its own assignment.** The route planner
  lets a capability inherit a wider assignment (the global one). An embedding
  call must never reach a chat model that way, so the engine exists only when
  `capability:memory.embed` has an assignment head.
- **The embedding model has its own local runtime slot.** The local runtime
  lease lets one large local artifact run at a time. The embedding model is a
  separate small model, so the `memory.embed` adapter takes no lease
  (`kernel/local_runtime_slot.py`, `OWN_LOCAL_SLOTS`). A background embed batch
  never refuses a live local chat or dictation call, and the reverse. A local
  engine still gets batches of 16 with a 0.25 s gap, to leave the processor
  to the live call.
- **A search never waits long for the engine.** The question is embedded on
  a worker thread with a 0.5 s limit; after it the search answers by keyword
  and says so in `ranking.engine` (`outcome: timeout`). The route runs the
  search off the event loop.
- **The assignment is checked at every call.** After a clear, the next
  search makes no engine call.
- **A search names its caller and its boundary.** The question's
  `inference.invoke` runs as the principal that searched. A remote engine
  writes the `external.egress` operation and receipt. The answer carries
  `ranking.engine.boundary`.

**Rules found in the review of slice 1 (Astra, 2026-10-03):**

- **Admission is checked at read time.** Each vector candidate is read again
  through the sweep's reader and `memory_admits`, and cut again; the snippet
  is that fresh text. The index is only a way to find a candidate. A source
  that is gone, parked, sensitive, promoted or changed since the last sweep
  does not surface.
- **Scope before the cut.** Kinds, excluded refs, project and time are
  checked before a candidate takes one of the 50 places. The walk has no
  bound.
- **The vector cache is keyed on a generation** (`memory_index_state`),
  moved in the same transaction as every index write.
- **Parked is out for every kind.**
- **Redact the whole text, then cut.** A snippet cut first can start inside
  a key block (no header for a pattern to see) or end inside a secret. So the
  source's complete admitted text is redacted as one text (a secret across
  transcript turns is one secret), and every chunk, snippet, recent row,
  relation row and memory-selected grounding block is cut from that.
- **Secrets.** Every title and snippet memory returns is redacted. The
  keyword tables `*_memory_fts` are filled by triggers in the writer's own
  transaction, so the sweep (and the rebuild) replaces the copy of a source
  that holds a secret and merges the index. Not done: `segments_fts` and
  `thread_messages_fts` hold no copy of the text, only tokens; a secret said
  in a meeting or a thread is still a search key there (the result is
  redacted).

On a corpus this small the vector top 50 holds almost every source, so a
keyword hit on a common word is in both lists and can rank above the one
right vector hit. One paraphrase question (p11) is first in the vector list
and outside the fused top 5 for this reason. A real desk has thousands of
sources; the top 50 is then a small part of them.

## Unknown (not verified for this design)

- That `llama-cpp-python` 0.3.35 loads `nomic-embed-text-v1.5` `Q8_0` and embeds
  correctly on this Mac. Not run. Slice 1 proves it first.
- Embedding throughput on this Mac, so the time to index a year of meetings.
- Whether `InferenceRunner.invoke` accepts a non-chat adapter without change.
  `speech.transcribe` is a non-chat capability in the registry
  (`inference_capabilities.py:1063`); its runner path was not traced.
- How a preset is added to the signed packaged catalogue
  (`inference_setup_catalog.py:25-32` holds a trust root). Not needed: the
  embedding model has its own unsigned local source (section 4).
- Whether a base install (no `meeting` extra) must embed. If yes,
  `llama-cpp-python` moves to core or the default becomes endpoint-only there.
- The real size of the owner's desk. No real database was read. The scale in
  section 0.2 is reasoning.
- The 256-dimension cut of the nomic model is from its model card, not tested
  here; the benchmark in slice 1 measures 256 against 768.
- PR #768 (`memory_grounding.py`, `DESK_REF_KINDS`) was open when this was
  written; names may move before it merges.
