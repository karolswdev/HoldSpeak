# Counsel on the re-take — HS-200-10 (scoped working context)

**Target:** `assets/settled-design-working-context.md` (1383 lines, re-taken
2026-09-07 after the bounce), read fresh against
`feat/phase-200-working-context`.
**Method:** every `file:line` opened. Two of the design's own open questions
were settled by **running** them in a throwaway SQLite in the scratchpad, not
by reasoning. No git verb touched the tree; the owner's database was not
opened this round (the census was re-measured last round and reproduces).

---

## VERDICT — **RATIFY WITH CONDITIONS**

The bounce was answered properly. The re-take did not argue with the finding,
it re-walked it, and then **found a second retrieval route the bounce had
missed** — the graph route reading `FROM notes WHERE id=?` directly
(`db/memory.py:1085-1094`), which a corpus-only fence would not have closed.
Finding that unprompted is the strongest evidence in the document that the
lesson landed.

Three conditions are **P0**. All three are *placement* errors inside a
mechanism whose shape is right — one fence sits on the wrong side of a
function boundary, one sits three lines too late, and one is device-local
where the record it protects is not. **None of them re-opens ruling C2′.** A
second bounce is not warranted and I looked for the reason to give one.

Two of the design's own "asserted, not observed" items I settled by running
them. Both behave as designed, and one fails harder than the document says
when it fails.

---

## THE CONDITIONS

### P0-A — L3 sits on the BY-REFERENCE path. As placed, it silently drops a promoted Note from any attached KB or zone.

**Where:** D2.4, "L3 — a belt at the relevance-side hydrator", which states:
`_hydrate_members` "is called from the global pass (`:209`) and from the
project-scoped search inside the `project:` branch (`:485`)... So the belt can
refuse a promoted ref in `_hydrate_members` **without touching by-reference
hydration at all**." Repeated in D3's retrieval seam ("called `:209` (global)
and `:485` (project-scoped)") and in the D5 test row.

**It has a third caller, and that one is by-reference.**
`_hydrate_container` (`holdspeak/grounding.py:514-535`) calls
`_hydrate_members` at `:526-528`. And `_hydrate_container` is what
`_hydrate_qualified` dispatches to for an **explicit** container ref:

- the `knowledge:` branch — `grounding.py:411-431`, members from
  `db.knowledge_memberships.list_for_knowledge` (`:415-418`);
- the `zone:` branch — `grounding.py:432-450`, members from
  `db.directory_memberships.list_for_directory` (`:436-439`).

So a Thread or an Ask that explicitly attaches `knowledge:<kb>` or
`zone:<z>` containing a promoted Note routes through `_hydrate_members`. With
L3 there, that Note is refused — **silently, with no unknown-ref error**,
because `_hydrate_members` appends to `unknown` only on a `qualified_ref`
parse failure (`:502-505`). The owner attached a container by reference and
one member vanishes from the prompt with no signal.

That is "silent loss of accepted input or kept work" from `ACCEPTANCE.md`'s
critical-defect list, and it also breaks the one thing the cost section leans
on: that by-reference reach survives intact.

**The planned proof would not catch it.**
`test_the_relevance_side_hydrator_refuses_a_promoted_ref_but_by_reference_hydration_does_not`
exercises `_hydrate_qualified` (`:261`) with a direct `note:` ref. A direct
`note:` ref never enters `_hydrate_members`. The container case is untested.

**The change.** Move L3 to the two **relevance call sites** — filter the
`members` list immediately before `_hydrate_members(...)` at `grounding.py:209`
and at `:485` — rather than inside `_hydrate_members` itself. Then add a test:
*an explicitly attached `knowledge:` (and `zone:`) container carrying a
promoted Note still hydrates that member's body.* Without that test the defect
recurs the first time someone "simplifies" the two call sites back into the
shared function.

---

### P0-B — L2's predicate is three lines too late. It corrupts the receipt and returns short pages.

**Where:** D2.4, "L2 — one predicate at the hit assembly": "`MemoryRepository.search`
(`db/memory.py:168`) builds every `MemoryHit` at one place (`:293-296`)... A
promoted `source_ref` is dropped there."

**The convergence claim is true** — I verified it independently:
`grep -rn "MemoryHit(" holdspeak/` returns exactly one line,
`holdspeak/db/memory.py:295`. That is the right insight.

**The placement is wrong**, because three things happen before it:

- `lexical_total = len(interleaved)` — `db/memory.py:262`
- `total = len(interleaved)` — `:292`
- `page = interleaved[bounded_offset : bounded_offset + bounded_limit]` — `:293`

Dropping rows inside the `MemoryHit` comprehension (`:294-314`) means `total`,
`lexical_total` and `expanded_total` (`:315-322`) all **count records that were
never returned**, and the page comes back **shorter than `limit`** with no
explanation. Downstream, `grounding.py:208` takes `[:GROUNDING_MAX_REFS]` of a
short list and `:215-217` adds `search.total - len(members)` into
`stats["overflow_count"]` — so the grounding receipt reports sources that were
withheld as though they were merely overflow. `ACCEPTANCE.md`'s critical-defect
list names "incomplete observation presented as an all-clear".

**The shipped precedent is exact and the design should use it.** `exclude_refs`
already does precisely this job, at precisely the right places:

- normalised into `excluded` at `db/memory.py:188-192`;
- applied to the lexical rows at `:247-252`, **before** the sort and before
  `lexical_total`;
- threaded into `_expand_related_rows` at `:271` (parameter `:748`) and honoured
  against the neighbour ref at `:775`.

**The change.** Union the promoted refs into `excluded` after `:192`. One
place, both routes, counters stay honest, and it reuses plumbing that already
exists rather than adding a second filtering idiom. Amend D2.4's L2 paragraph
and D3's retrieval-seam row to cite `:188-192` / `:247-252` / `:271` instead of
`:293-296`.

---

### P0-C — F0 is "by construction" on the writing device only. Sync carries the body without the fence.

**Where:** D2.4, "L1 — exclusion from the corpus (construction)"; and the cost
section, which says of `SyncService.pull` "**not blocked** — blocking sync
would break synchronisation of the owner's own record."

Accepting that the body travels is a defensible call. What the design does not
observe is that **the fence does not travel with it.**

- `SYNC_REGISTRY` (`holdspeak/services/sync_service.py:32-43`) registers
  `SyncKindSpec("note", "notes", "note.schema.json", True)` at `:35`, and
  `_MERGEABLE["notes"]` declares `body_markdown` a merged field (`:120`).
- The primitive merge writes through `db.notes.upsert` (`sync_service.py:664-671`).
- `context_promotions` is a **new table with no `SyncKindSpec`**.

On the receiving device the note INSERT fires `notes_memory_ai`, the guard's
`NOT EXISTS (SELECT 1 FROM context_promotions ...)` finds nothing, and **the
body is indexed into that device's relevance corpus.** L1, L2 and L3 all key
on a local `context_promotions` row that never arrived. The record is then
retrievable by relevance on device B exactly as it was before the bounce.

This is not hypothetical plumbing: notes are a synced content class today and
the iPad/HSM track is the reason the class exists.

**The change.** Pick one and say which, in D2.4 and in "cannot promise":
(a) register `context_promotions` (or a minimal `(target_ref)` projection of
it) for sync so the fence travels with the record; (b) exclude promoted notes
from `SyncService.pull`'s note emission, accepting that the record then does
not sync at all; or (c) state plainly that **F0 is single-device** and that a
promoted record re-enters the relevance pool on any other device. (a) is the
only one that keeps both the ruling and the sync contract. What is not
acceptable is the current silence, because the document's whole claim is
"construction, not filtering".

---

### C1 — The cost bound is real but much narrower than stated: the picker searches titles, and the title is the model's words.

D2.4's cost section: "**by-reference discovery survives intact**, which bounds
the cost precisely. The Thought context picker searches `notes` **directly**,
`SELECT id,title FROM notes WHERE ... title LIKE ?`
(`refinement_context_service.py:635-646`)... He can still find a promoted Note
by title. Verified."

I verified it too, and the SQL is exactly that — `SELECT id,title FROM notes`
with `title LIKE ? ESCAPE '\' COLLATE NOCASE` (`:637-645`). **It searches
title only. Not body.**

Now read it against D2.2's own construction: in New-Note mode "the body is the
verbatim quote, the title is the fact `text` truncated" — the *model's*
paraphrase. So after F0:

- the owner's own words live only in the body, which is out of the FTS corpus
  **and** outside the picker's `LIKE`;
- the only searchable string is the model's truncated paraphrase.

He will look for the sentence he said. It is findable by neither route. "He
can still find it by title" is true and nearly useless in the common case.

**The change.** Either mint the title from the quote's leading clause rather
than the model's `text` (which also serves D1's law that the record carries his
words), or extend the picker's `LIKE` to `body_markdown`, or state this
narrowing in the cost list in these words. My preference is the first: it costs
one line and it makes the design's own law and its own repair path agree.

### C2 — Append-mode residue: bodies already frozen into `thread_refs` are replayed on every future turn.

The append mode deletes the note's FTS row atomically with the promotion. It
does not touch copies the *pre-promotion* relevance pass already froze.
`thread_service.py:397-408` writes the full block text into
`thread_refs.frozen_json` with `"sensitive": False`, and `:2070-2085` replays
those rows **on every turn** — scoped to the message path (`:2071-2075`),
deduped newest-per-source (`:2079-2082`), capped at 16 — into a `system`
message (`:2095-2107`).

So this is not "what already went to a model once", which `CONTRACTS.md:66`
licenses. It is a durable row re-sent on every subsequent turn of that thread,
after the owner has promoted the record and after F0 has supposedly removed it
from relevance. Name it in "cannot promise", and decide whether the append mode
should also supersede matching `thread_refs` rows. I do not think it must —
but the document should not read as though the append mode's `DELETE` finishes
the job.

### C3 — One honesty wording slip, in the section about honesty.

D2.6, "What `revoke` revokes": "Corpus exclusion (F0) does remove the record
from relevance permanently, **which is the one disclosure surface revocation
genuinely closes**." F0 fires at **promotion**, keyed on the existence of a
promotion row rather than on `disclosure_state` — the design says so itself two
paragraphs earlier. Revocation closes nothing there; it was already closed.
Reword to "the relevance surface was already closed at promotion; revocation
adds nothing to it and removes nothing from the surfaces above."

### C4 — The forward-reference failure is harder than "cannot promise" #6 says. I ran it.

Item 6 says: "**If `context_promotions` does not exist when the trigger body is
created, the `NOT EXISTS` subquery is unresolved** — SQLite resolves trigger
bodies lazily at fire time, so this should be safe, but it is asserted, not
observed."

Observed, in a throwaway database:

```
CREATE TRIGGER ... SELECT ... WHERE NOT EXISTS (SELECT 1 FROM context_promotions ...)
  -> trigger created before table: OK
INSERT INTO notes(...)
  -> Parse error: no such table: main.context_promotions
```

So: the `CREATE` succeeds with a forward reference, and **the first write to
`notes` fails hard**. Not "unresolved" — the desk cannot save a note. Inside one
`executescript(SCHEMA_SQL)` there is no window, and `reconcile_schema` calls the
trigger refresh at `reconcile.py:644` *after* `executescript`, so the shipped
ordering is safe. But any database that ends up with the revised trigger and
without the table is bricked for note writes.

**The change.** Restate item 6 with the real failure mode, and add a migration
test that reconciles a database built from an older `SCHEMA_SQL` and then writes
a note — the assertion is that the write succeeds, which is what proves the
ordering.

### C5 — The coder-steering framing is defensible on the ledger law and one step short on the face law.

The orchestrator's framing — a disclosure question, not an unaudited egress —
is **supported by the code**, and I checked each part rather than taking it:

- `coder_steering_support.py:98-110`: when the client sends no `grounding`, it
  calls `service.hydrate_refs(principal, [], [], "summary", query=text)`
  (`:103-105`) and returns `compose_steer(text, blocks)` (`:110`);
- `web/src/desk/grounding.ts:105-122`: `buildGrounding` returns `null` when the
  owner picked nothing and there are no rails (`:112-113`) — so "no grounding"
  is the ordinary case, exactly as stated;
- `coder_steering_routes.py:414-433`: a `policy` and a
  `steering_commitment(operation, policy)` (`:418-421`) accompany
  `deliver_process_input`, whose payload carries
  `"grounding_refs": list(composed["refs"])` (`:431`), and the result's
  `audit_id` is checked at `:434`.

Policy, commitment, audit id, and a receipt naming the refs. That is a
disclosure with provenance, and `feedback_ledger_not_gate_rule.md` asks for
exactly that. **I would not overturn the framing.**

One step is missing, and it is a face law, not a ledger law. Because
`buildGrounding` returns `null` precisely when the owner picked nothing, the
face shows **no chips** at the moment relevance is about to pick sixteen
sources and type them into a third-party pane. UX-CANON A.9 — "egress exactly
where egress happens... never missing where a fetch is triggered" — puts the
badge at composition time, not only in the audit record afterwards. So:
framing accepted; the ledger entry should carry that the **pre-delivery**
disclosure is the missing half, so whichever story owns the coder pane inherits
a specific obligation rather than a general worry.

---

## THE HUNT

### 1. Is there a THIRD route? — I swept independently. **No, for relevance.**

I did not take the census on report. Four independent checks:

- **`include_memory=True` call sites, my own grep over `holdspeak/`:** eight
  hydrator call sites — `workbench_conductor.py:212`, `ask_service.py:522`,
  `ask_service.py:580`, `thread_service.py:388`, `coder_service.py:148`,
  `recipe_service.py:118`, `recipe_service.py:209`,
  `sequence_workflow_service.py:55`. **Every one appears in D3's census**,
  which counts nine because it counts the two `coder_steering_support.py`
  entry points that share `coder_service.py:148`. Nothing missing.
- **`MemoryHit` producers:** exactly one, `db/memory.py:295`. The convergence
  claim holds.
- **`MemoryRepository`'s public API:** `rebuild()` (`:164`) and `search()`
  (`:168`). There is no public single-ref lookup; `_load_related_row` (`:1042`)
  is private and reached only from graph expansion.
- **`notes_memory_fts` references, whole tree:** only `db/memory.py`,
  `db/schema.py` and `tests/unit/test_reconcile.py`. The "only reader is
  `_note_rows`" claim is verified.
- **Direct `FROM notes` readers outside `db/memory.py` and `db/primitives.py`:**
  all by-id working-note reads in `refinement_thought_service.py`, the attach
  resolver and KB member resolver in `refinement_context_service.py:870` /
  `:907`, and the title picker at `:645`. None is relevance-driven.

**Row sources feeding `interleaved`** (`db/memory.py:194-246`): `_decision_rows`,
`_artifact_rows`, `_meeting_rows`, `_note_rows`, `_thread_rows`, and
`_ecosystem_rows` for six kinds — plus the graph expansion woven in at
`:286-290`. Only `_note_rows` and the graph route yield `note` rows. **Two
routes, as the design says.**

One scoping note the design gets right and should keep: L2 "closes any third
route **into a hit**". It does not close a route that reads `notes` without
producing a hit — and the design's own `ResourcefulService._loose_idea`
(`resourceful_service.py:163-193`) is exactly such a route, correctly named and
correctly not claimed as closed.

### 2. Is L1 actually by construction? — **Yes on the writing device, and I ran it. No across sync (P0-C).**

I built the mechanism in a throwaway database and exercised it:

```
-- promotion row first, then the note, in one transaction
promoted-note rows in fts (expect 0): 0
control rows in fts (expect 1): 1
```

The ordering claim holds exactly: with the promotion row inserted first, the
guarded `notes_memory_ai` never writes the body — **not even transiently**, so
there is no window for a concurrent reader. The control note with the same
words IS indexed, which is what makes the planned test able to fail.

The write paths I traced for re-admission:

- **Triggers** — `notes_memory_ai` (`schema.py:1214-1218`) and `notes_memory_au`
  (`:1222-1226`) both guarded; `notes_memory_ad` (`:1219-1221`) only deletes.
  Every `notes` write goes through `NoteRepository._upsert_in_transaction`
  (`db/primitives.py:120-142`) or `soft_delete` (`:197`), so every write
  re-evaluates the guard. Self-healing, as claimed.
- **Rebuild** — `rebuild_memory_index` (`db/memory.py:126`, notes at `:139-143`)
  gains the same `WHERE NOT EXISTS`. Correct, and it is the only bulk writer.
- **Reconcile** — verified. `_refresh_tool_turn_lifecycle_guards`
  (`reconcile.py:549-579`) builds a reference database from `SCHEMA_SQL` in
  memory (`:558-569`), compares each named trigger's SQL to the live one
  (`:571-573`), and DROP+CREATEs only where they differ (`:575-577`). It is
  called **unconditionally** at `:644` and its return feeds `shape_changed` at
  `:653`. Extending its `names` tuple works. The docstring at `:552` states the
  exact problem. The reconciler's additive invariant (`:1-7`) is preserved — a
  trigger refresh is not a DROP TABLE, DROP COLUMN or DELETE.
  *Nit:* the function is named for tool-turn guards; adding note triggers to it
  earns a renamed docstring, not a second mechanism.
- **Append mode** — the explicit `DELETE FROM notes_memory_fts` is belt: the
  note upsert that follows fires the guarded `_au`, which deletes and declines
  to re-insert. Harmless and worth keeping. The ordering matters here too, and
  D2.6's event table states it correctly.
- **Sync** — **fails. P0-C.**
- **Restore/import** — any path that recreates notes goes through the same
  triggers, so it inherits the guard *provided the promotion rows are restored
  too*. Same root cause as P0-C: the fence lives in a second table.

### 3. Does L2's predicate sit where it claims, and survive every caller?

The **convergence** is real (one `MemoryHit` site). The **placement** is
wrong — P0-B.

On callers: every consumer goes through `MemoryRepository.search`, so the
predicate covers all of them —
`MemoryService.search` (`services/memory_service.py:38`) behind both the MCP
tool (`mcp/families/memory.py:33-49`) and the web/Desk search,
`grounding.py:203-207`, and `meeting_service.py:467`. Filtering inside
`search()` is the right altitude; only the line number is wrong.

### 4. The stated cost — real, but narrower than stated. C1.

The bound exists (the picker does search `notes` directly, verified at
`refinement_context_service.py:635-646`) but it is a **title-only** bound over a
**model-authored** title. The design has not made the feature useless — a
promoted record is still attachable, still shared by reference between Thoughts,
still corrected once — but the discovery story is thinner than the document
claims, and D4 hunt 6 ("the first time he promotes a sentence and then cannot
find it in Desk memory search") under-states it: he will not find it in the
picker either, unless he remembers the model's paraphrase.

### 5. The six carried P0s — checked one at a time. **No narrowing dressed as a closure.**

| Carried | Claim | My check |
|---|---|---|
| **P0-1** hash contains the counter | closed | **Closed properly.** D2.2 states a **new** recipe over `{ref, title, body_markdown, tags}`, names `_leaf`'s digest as wrong (`refinement_context_service.py:975-979`), and cites the unconditional `last_modified` write (`primitives.py:137`, `:141`). The replacement arbitration test — `upsert` with an explicit unchanged `last_modified` — is the real divergence case and replaces the wrong "no-op save" example |
| **P0-2** trigger downgrades a revocation | closed | **Closed, and I ran the SQL.** `forbidden` survived a subsequent note write; a fresh dependent went to `stale`. The lattice is stated as a lattice, and `test_a_note_save_after_a_revocation_leaves_forbidden_intact` fails without it |
| **P0-3** revoke one of several | closed | **Closed.** The survivor rule ("only when no `disclosure_state='active'` promotion into that `target_ref` survives") is exactly right, decided by one seek on `idx_context_promotions_target`, and has its own test with both halves |
| **P0-4** double-click mints two Notes | closed | **Closed.** Deterministic `target_ref` and `promotion_id` from `(thread_id, fact_id)`; the precedent `generate_pobs_id` exists at `holdspeak/project_contracts.py:292`. The reason it is needed — `command_id` is caller-supplied — is stated |
| **P0-5** search/export tests | closed | **Closed, and honestly.** Three tests, and `test_desk_snapshot_and_sync_pull_still_carry_the_body` asserts the **known egress** rather than a false negative. Asserting what is true rather than what one wishes were true is the right shape for a contract test |
| **P0-6** revoke at each disclosure | **narrowed, and labelled as narrowed** | Correct handling. It says in D2.6 and again in "cannot promise" that `CONTRACTS.md:63` is met **only** for consumers reading `context_dependents`, and lists what it is not met for. That is a narrowing declared, not disguised. One wording slip inside it — C3 above |

C10, C11, C12, C13, C14 and C15 all landed, including the correction that
`insert_evidence_link` has zero references anywhere (I re-ran that grep; it
returns one line, its own definition).

### 6. The coder-steering framing — see C5. Accepted, with one addition.

---

## WHAT MOVED FROM ASSERTED TO OBSERVED

Two of the design's open items, settled by running them in a scratch database
rather than reasoning about them:

1. **L1's write ordering.** Promotion row first → the body never reaches the
   corpus, not transiently; a control note with identical words IS indexed.
2. **The lattice.** `forbidden` survives an `AFTER UPDATE ON notes` trigger
   whose `SET` reads the target table's own pre-update column; a fresh
   dependent goes to `stale`.
3. **The forward reference** (this one is worse than the document says) — see
   C4.

---

## WHAT I COULD NOT VERIFY

- **Whether the design behaves as designed.** No code exists for it. What I
  ran was the *mechanism* — the trigger guard, the write ordering, the lattice
  CASE — in isolation on a scratch schema, not the product.
- **Whether the eight `include_memory` sites are the whole surface at runtime.**
  My grep covers static call sites in `holdspeak/`. The design's own
  "cannot promise" #4 makes the same admission about MCP tools that reach
  `AskService.ask` / `RecipeService.run` / `ThreadService.start_turn` through
  wrappers, and its answer — fence at the corpus and at hit assembly, not at
  the call sites — is the correct architectural answer to that residual.
- **The sync fence gap's blast radius (P0-C).** I verified `SYNC_REGISTRY`
  (`sync_service.py:32-43`), the `notes` mergeable fields (`:120`) and the
  merge write (`:664-671`). I did **not** run a two-device sync, and I did not
  audit whether any *other* device-local fence in this repo has the same shape.
- **Whether L3's container breakage (P0-A) would surface in practice on his
  desk.** He has `knowledge_memberships` rows (5, measured last round) but zero
  working Thoughts, so the container-attach path is cold. The defect is in the
  code path, not in his data.
- **The two unmeasured costs** (trigger writes, DDL seed on an 85 MB database).
  Unchanged from last round.
- I ran no product test, opened no face, and did not open the owner's database
  this round.
