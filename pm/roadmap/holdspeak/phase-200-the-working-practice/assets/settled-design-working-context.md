# Scoped working context -- the settled design (Phase 200, HS-200-10)

> **Re-taken 2026-09-07 after counsel's BOUNCE**
> (`assets/counsel-on-design-200-10.md`: seven P0s, nine conditions).
> The orchestrator **REVERSED ruling C2** -- this document's central
> choice -- and replaced it with **C2′: reachable by reference, never by
> relevance.** The reversal, what caused it, and every other change are
> recorded in the **Addendum** at the end; the body below is written to
> the new rulings rather than annotated around the old one.
>
> This is a WIRE design. The faces for this phase were ratified with
> `assets/settled-design-daily-workflow.md`; nothing here redraws them,
> and under ruling C6 **no face ships in this story at all** -- the
> earlier face plan is struck.
>
> **Every `file:line` below was opened on this branch.** Where a claim
> could not be verified, this document says so in those words. Two
> citations counsel corrected, and one it made, are corrected here.

Phase 200's contracts bind: **C2** (claim meaning), **C3** (evidence
manifests and working context), **C4** (coverage vocabulary), **C6**
(setup transactions and recovery), **C11** (shared experience).
Constitution articles III (local first), V (consent) and VI (honest by
construction) bind every line. `EXECUTION.md` "Before implementing a
story" binds the disposition table in D2.1.

---

## D0 -- the Tuesday moment

He is in an Interview on Tuesday morning and he says, out loud:

> *"We cannot take another cut-over without a rollback rehearsal. That
> is not negotiable."*

The model records it as a fact. It is a good fact. It is also a fact
that will matter in the architecture brief on Thursday, in the weekly
Project update on Friday, and in every conversation about the payments
platform for the next quarter -- and today it lives in exactly one
Thread, in a JSON blob keyed to that Thread (`interview_sessions`,
`holdspeak/db/schema.py`), and it dies with it.

So he presses **`Keep`** on the fact row. One Note appears --
*Rollback rehearsal is not negotiable* -- whose body is the sentence he
actually said, not the model's paraphrase of it.

**And then it sits still.** It does not attach itself to anything, and
it does not join the pool of records the desk quietly searches when he
types. It is reachable the way a filing cabinet is reachable: he opens
it, on purpose, by name.

Thursday he opens the context picker, finds it by title, and attaches
it to the architecture Thought. Friday he attaches the SAME Note to the
update Thought. There is one Note. There is no second copy. Neither
Thought owns it.

Saturday he softens it -- *"...unless the change is reversible in under
five minutes"* -- and edits the Note once. Both Thoughts read `STALE`
without either being open, and a cadence run that would have used the
old wording refuses and says which record moved.

The following week he deletes the message he said it in. The Note
stays, because the Note is his now. What goes is the *claim that a
source backs it*.

That is the whole story: **one sentence, said once, kept once, reached
only on purpose, reused by reference, corrected once, and revocable
without erasing his work.**

*(On his actual desk today none of this can happen yet, and the numbers
are in D4. He has zero Interview sessions, zero working Thoughts, and
an empty default context. The mechanism starts empty on his machine.
One thing in D4 is live on his desk today, before any of this ships,
and he should walk it first.)*

---

## D1 -- the laws this design obeys

| Law | Source | How it binds here |
|---|---|---|
| **Reachable by reference, never by relevance** | ruling **C2′**; Article V | A promoted canonical record does not enter the relevance pool. It is reached by an explicit ref -- the context picker, an attach, a `Carry into brief`. It is never returned by a relevance search, and therefore never lands in a prompt the owner did not point at it. **Killed at four choke points, only the first by construction** (D2.4); and the fence travels with the record across sync |
| **Authorship, not reachability, is the distinction** | ruling C2′ | A Note is something he wrote deliberately. A promoted record is something the system extracted from an answer he gave about goals. The first already being in the relevance pool does not license putting the second there |
| **A promotion never attaches** | Article V; owner ruling `feedback_ledger_not_gate_rule.md` | Promotion writes a canonical record and nothing else. It never attaches, never joins Everyday context, never joins the default context. This is still true and still necessary -- it is simply **not sufficient**, which is what the bounce established |
| **The canonical record carries HIS words, never the model's** | C2 ("generated prose requires a separate support check") | The Note body is the verbatim `quote`. The model's `text` becomes the title, which is a label, not an assertion. Only `basis == "stated"` facts may be promoted |
| **Provenance is a locator and a hash, never a copy** | C3 ("removing current Interview context does not promise erasure"); Article III | `context_promotions` stores `source_message_id` + `quote_sha256` + a locator. It never stores the quote text, so revoking the source actually removes the words while provenance stays provable |
| **A content hash contains content, and nothing else** | ruling C2′'s sibling, counsel P0-1 | `target_content_sha256` covers `{ref, title, body_markdown, tags}` **only**. It deliberately does NOT reuse `_leaf`'s recipe (`refinement_context_service.py:975-979`), which folds `last_modified` and `deleted` into the digest and would therefore report `CORRECTED` about an unchanged sentence |
| **`qualified_ref()` is not extended** | `holdspeak/db/relationships.py:25-33` (**20** kinds); C7 | The revision lives in the promotion record's own columns. Extending `kind:id` would touch every stored ref in his live DB and every consumer |
| **A ref names its own kind** | counsel C10 | `target_kind` is derived from `qualified_ref()`'s parsed kind. A caller-supplied kind is ignored |
| **Every mint is deterministic** | counsel P0-4; the precedent `generate_pobs_id` (`holdspeak/project_contracts.py:292`) | Both the promotion id and a newly minted Note id derive from `(thread_id, fact_id)`, so a double-click collides on a UNIQUE instead of minting two Notes |
| **A revocation is never downgraded** | counsel P0-2 | `forbidden` is terminal in `context_dependents` until an explicit re-promotion clears it. No trigger, and no ordinary edit, may rewrite it to `stale` |
| **Forgetting is not suppressing** | AC4; shipped precedent `calendar_event_link_suppressions` (`schema.py:4103-4114`) | An explicit revocation writes a durable suppression keyed by identity, so re-typing the quote cannot resurrect the promotion |
| **A `person:` ref cannot enter this mechanism** | `relationships.py:17-22` -- 20 kinds, no `person` | Every ref passes `qualified_ref()`, which already raises on `person:`. Inherited, not re-implemented |
| **One story, one state machine over `notes`** | `schema.py:882-884` | AC3's "a correction updates the canonical record once" is satisfied by the ORDINARY Note edit. This design adds no second way to edit a Note |
| **The model records; the owner disposes** | shipped asymmetry: `mcp/families/interview.py:27-40` vs `web/routes/threads.py:87`; ruling C6 as amended | Promotion joins the web route's event allowlist. **There is no MCP `promote` tool.** A model that could mint a canonical record is the precise failure AC5 exists to prevent |
| **Additive where it can be; house-precedented where it cannot** | `feedback_migrations_stay_minimal`; `holdspeak/db/reconcile.py:1-7` | Three new tables, three indexes, two new triggers, one seed -- all additive. Two SHIPPED triggers are revised, which the reconciler cannot do with `CREATE TRIGGER IF NOT EXISTS`; the named mechanism for exactly that already exists at `reconcile.py:549-578` and is extended |
| **Every INSERT names its columns** | scar `reference_positional_inserts_reconcile_order` | Enforced by the fence test |
| **The snapshot is regenerated, never hand-edited** | `tests/unit/test_db.py:1731-1758`, normalizer `:1740-1750` | |
| **No face ships here** | ruling C6 as amended; counsel C14 | The face owes a ratified board. The earlier plan to add a `Button` to `InterviewPanel.tsx` is **struck** so a build lane cannot read this document as licence |
| **The shipped coverage words, not new ones** | C4; `holdspeak/services/needs_you_aggregate.py:52` | A gap is `stale`, `unavailable` or `forbidden`. `needs_you_aggregate` is not widened -- that is story 15's |

---

## D2 -- the data model and the verb

### D2.1 -- the disposition per acceptance criterion

| AC | Disposition | Current code | The scenario that actually fails today |
|---|---|---|---|
| **AC1** promotion identifies source quotation, target scope, target revision | **implement missing** | The quotation half is BUILT and ENFORCED: `interview_service.py:213-215` requires the quote to appear literally in a non-sensitive, non-draft `text` part, and `_prune_unavailable_facts` (`:67-80`) rechecks it -- *inside the open transaction*, at `:143`. Scope is `qualified_ref()` (`relationships.py:25-33`) and carries **no revision**. `notes` has zero provenance columns (`schema.py:872-881`) | There is **no promotion verb anywhere** -- no service method, no event kind, no route, no tool, no table |
| **AC2** two Threads reference the same context without separate editable copies | **reuse and prove (at Thought scope) + declare the Thread gap** | TRUE at Thought scope: `refinement_attachment_visible` stores refs + hashes only (`schema.py:970-981`); the body is re-read live at prompt time (`refinement_context_service.py:869-882`, `:973-988`). Proved by `tests/unit/test_refinement_context_service.py:220` | The AC says **Thread**. A Thread's grounding is a frozen COPY: `thread_refs.frozen_json` (`schema.py:3614-3622`) written with the block's full `text` at `thread_service.py:397-408`. This design does **not** convert it; it delivers AC2 at Thought scope, proves it, and records the narrowing against `ACCEPTANCE.md:33` (D2.8) |
| **AC3** a correction updates the canonical record once and marks dependent prepared work stale | **fix a demonstrated gap** | Two working precedents: the pull at `refinement_context_service.py:807-826` with `_stale_conflict` `:1113-1119`, and `InterviewService._invalidate` `:194-197` | Both are **detect-on-read pulls**. `refinement_attachment_visible` is keyed `(thought_id, attachment_revision, ordinal)` (`schema.py:979`) with the ref only a payload column, so "who consumes `note:n1`?" is a scan of every revision of every Thought, and revisions are never pruned. Nothing can mark a consumer that is not open, and nothing can fence a run before it dispatches |
| **AC4** removing or revoking a source blocks new unauthorized disclosure and names the resulting gap | **fix a demonstrated gap, and declare what it does not reach** | Three blocking shapes exist: `calendar_event_link_suppressions` (`schema.py:4103-4114`, consulted `db/calendar_event_projects.py:271-287`), `project_service.py:2745-2749`, `authority_service.py:183-186` | **Nothing names a gap.** `_prune_unavailable_facts` (`:67-80`) drops facts SILENTLY, and it is a *forget*, not a *suppress*: re-typing the quote resurrects the fact. And the honest limit is stated rather than papered over: after this story, **blocking: yes, for consumers that read the index. Naming: to a caller, not to the owner**, because ruling C6 ships no face (D2.6, and "cannot promise" #3) |
| **AC5** protected People content cannot enter ordinary context through promotion or derived suggestions | **fix a demonstrated gap** *(was "integrate"; the bounce re-classified it)* | Direct paths ARE guarded: People is a ciphertext sidecar (`holdspeak/people/store.py:19`, `:414-421`); `RESOURCE_KINDS` omits `person` (`relationships.py:17-22`); interview refuses the People section (`interview_service.py:201`, `:226`); Thread ingress refused (`thread_service.py:314-320`); a `person:` ref freezes display-name-only + `sensitive` (`:359-368`) | **The automatic retrieval path.** `grounding.py:190-197` runs a global relevance search **if and only if `not has_explicit_sources`** (`:188`), takes 16 hits (`:24`, `:208`), and hydrates them through a `note` branch (`:313-321`) that returns `body_markdown` whole with no cap and no sensitivity check -- out of an FTS corpus with no sensitivity condition on notes at all (`db/memory.py:469-495`). **Nine call sites reach that pass** (D3), four of them unconditionally. And a SECOND route exists that never touches the FTS index at all: `MemoryRepository._load_related_row`'s `note` branch reads `FROM notes WHERE id=? AND deleted=0` directly (`db/memory.py:1085-1094`), woven into the same hit list at `:286-290` |

**No AC is deferred.** AC2 is narrowed to the scope where the mechanism
exists, and the narrowing is recorded where it is gated (D2.8).

---

### D2.2 -- P1 settled: where "target revision" lives

**The decision: `qualified_ref()` is NOT extended. The revision is two
columns on the promotion record -- a per-kind display LABEL and a
content SHA256 -- and only the sha256 is ever compared.**

1. **The counter cannot be the comparator.** `notes.last_modified`
   (`schema.py:879`) is a last-write-wins ISO string with a
   `datetime('now')` default. The codebase already learned this:
   `refinement_attachment_visible` stores both `source_last_modified`
   and `visible_sha256` (`schema.py:977-978`) and
   `project_in_transaction` compares the **sha**
   (`refinement_context_service.py:815-818`).

2. **Extending `kind:id` touches everything.** `qualified_ref()`
   (`relationships.py:25-33`) is the single validator behind **20**
   resource kinds (`:17-22`, counted programmatically) and every stored
   ref in his live DB.

3. **The three targets genuinely disagree**, so the mechanism is
   kind-dispatched with a typed refusal, the shape `_resolve_manifest`
   already uses (`refinement_context_service.py:926`,
   `code="context_kind_unsupported"`).

#### The hash recipe -- a NEW one, and NOT `_leaf`'s

The first draft of this design said `target_content_sha256` reuses
`_leaf`'s digest. **That was wrong and counsel caught it.** `_leaf`
computes (`refinement_context_service.py:975-979`):

```python
content_hash = _sha(canonical_json({"ref": ..., "title": ...,
    "body_markdown": ..., "tags": ...,
    "last_modified": str(note["last_modified"]), "deleted": False}))
```

`last_modified` is **inside the digest** -- and so is `deleted`, which
the first draft's stated recipe omitted entirely. The visible digest
has the same property (`:952-953` hashes `source_last_modified` into
`visible_sha256`). Meanwhile
`NoteRepository._upsert_in_transaction` (`holdspeak/db/primitives.py:120-142`)
writes `last_modified=excluded.last_modified` **unconditionally** on
`ON CONFLICT` (`:137`) with `last_modified or now` (`:141`) -- there is
no "did anything change" guard at the primitive.

So `_leaf`'s digest is `f(content, counter)` and moves whenever the
counter moves. A promotion whose target Note is re-saved with
byte-identical content would read **`corrected`**, telling the owner his
constraint moved when it did not. Under Article VI and ACCEPTANCE's
"unsupported prose presented as checked fact", that is the defect this
story exists to prevent.

**`target_content_sha256` is therefore a new recipe over
`{ref, title, body_markdown, tags}` only.** No timestamp, no tombstone
flag. It is a content hash and it contains content.

#### The per-kind table

| Target kind | Revision LABEL (display only) | Comparator (the authority) | Stored where | Compared how | V1? |
|---|---|---|---|---|---|
| `note` | `notes.last_modified` (`schema.py:879`) | sha256 over `{ref, title, body_markdown, tags}` -- **a new recipe**, deliberately not `_leaf`'s | `context_promotions.target_revision_label`, `.target_content_sha256` | recompute inside the reading transaction; equal = `current`, different = `corrected`, row absent or `deleted=1` = `unavailable` | **YES** |
| `thought` | `refinement_thoughts.aggregate_revision` (`schema.py:900`) -- the one counter monotonically covering the other four, proven by `refinement_aggregate_commands` (`schema.py:938-955`) | **two hashes, not one**: `attachment_sha256` (`:899`) covers only attachments; the body needs `refinement_working_revisions.content_sha256` (`schema.py:923`). And a Thought's body IS a Note (`working_note_id`, `:894`), which `_resolve_manifest` refuses to attach to itself (`refinement_context_service.py:879-883`) | not built | not built | **NO** -- `promotion_target_unsupported` |
| `project` facet | three disagreeing counters: `projects.revision` (`schema.py:560`), `project_resources.revision` (`:1476`), `project_items.revision` (`:1513`) | **none exists.** `project_items` has neither a content hash nor a `last_modified` (`:1498-1516`) | not built | not built | **NO** -- `promotion_target_unsupported` |

**`target_kind` is DERIVED, never accepted** (counsel C10). It comes
from `qualified_ref()`'s parsed kind; a caller-supplied `target_kind` is
ignored. Without this, `{target_kind: "note", target_ref:
"artifact:a1"}` passes `qualified_ref` (`artifact` is one of the 20
kinds) and the `note` branch would then `SELECT ... FROM notes WHERE
id = 'a1'`. Any kind but `note` raises `promotion_target_unsupported`.

#### Two target modes, both `note`, both deterministic

- **New Note** (the common case): `target_ref` omitted. **The body is
  the verbatim quote and the TITLE is minted from the quote's leading
  clause** -- not from the model's `text`. The first draft made the
  title the model's paraphrase, which set D1's "his words" law against
  the design's own repair path: the picker searches
  `title LIKE ? ESCAPE '\' COLLATE NOCASE` over **title only**
  (`refinement_context_service.py:637-645`), so with his words in the
  body and the model's in the title, he would search for the sentence
  he said and find it by **neither** route -- not by relevance (F0
  removed it) and not by the picker (it does not read the body). Minting
  the title from the quote costs one line, makes the law and the repair
  path agree, and is the difference between a bounded cost and a useless
  one. The model's `text` stays where it already lives, in the interview
  state. **The minted id is deterministic from `(thread_id, fact_id)`** -- the precedent is
  `generate_pobs_id` (`holdspeak/project_contracts.py:292`), which the
  schema comment at `:3850-3851` describes as making adapter retries a
  no-op. Two clicks therefore mint the *same* ref, collide on
  `UNIQUE (thread_id, fact_id, target_ref)`, and become the
  `updated_at` touch rather than two Notes carrying one sentence.
  Without this the replay guard does not cover the mode at all, because
  `command_id` is caller-supplied (`interview_service.py:133-137`) and
  two clicks are two commands.
- **Existing Note**: `target_ref` supplied with
  `expected_target_revision` (the `last_modified` the caller read). The
  quote is appended inside the same transaction. A moved Note refuses
  `promotion_target_conflict` -- the optimistic-cursor grammar `_mutate`
  already uses (`refinement_context_service.py:717-720`).

#### On `project_evidence_links`: informative, but a trap as a home

Its `excerpt_locator_json` (`schema.py:3876`) is the one column in the
schema shaped like a source quotation, and this design borrows the
idea. It is the wrong table: `project_id TEXT NOT NULL REFERENCES
projects(id) ON DELETE CASCADE` (`:3872`) makes it project-scoped when
promotion must work on a desk with no Project; that CASCADE would
silently delete provenance; and its only index is `(project_id,
target_ref)` (`:3880-3881`), which indexes the CONSUMER -- the opposite
of what P3 needs.

**Correction to the first draft** (counsel C15): `insert_evidence_link`
has **zero references anywhere in the tree**, tests included --
`grep -rn "insert_evidence_link"` over `holdspeak/`, `web/` and
`tests/` returns exactly one line, its own definition at
`holdspeak/db/delta.py:186`. The first draft said grep "finds it only
in `tests/unit/test_delta_schema.py`"; that file tests the *table*,
never the writer. The conclusion is unchanged and stronger.
`project_observations` (`schema.py:3852-3866`) *does* have production
writers (`services/watch_service.py:704-713`,
`services/project_evidence_collector.py:502-508`) but records what an
ADAPTER observed externally, not what the OWNER said, and its
`project_id` is equally mandatory. Neither is the home.

---

### D2.3 -- P3 settled: the reverse index

**One table, one row per (record, consumer) -- never per revision --
written by one reconcile point per consumer kind, pushed by a trigger
that mirrors the shipped FTS triggers, and confirmed by the pull that
already exists.**

#### The shape

```sql
-- HS-200-10: the REVERSE index.  refinement_attachment_visible is keyed
-- (thought_id, attachment_revision, ordinal) (schema.py:979) with the ref only a
-- payload column, so "who consumes note:n1?" is a scan of every revision of every
-- Thought, and revisions are never pruned.  One row per (record, consumer) keeps
-- this table bounded while attachment revisions accumulate.
CREATE TABLE IF NOT EXISTS context_dependents (
    canonical_ref TEXT NOT NULL,
    consumer_kind TEXT NOT NULL,
    consumer_id TEXT NOT NULL,
    consumer_revision INTEGER NOT NULL DEFAULT 0,
    bound_manifest_sha256 TEXT NOT NULL DEFAULT '',
    bound_at TEXT NOT NULL,
    stale_since TEXT,
    stale_reason TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (canonical_ref, consumer_kind, consumer_id)
);
CREATE INDEX IF NOT EXISTS idx_context_dependents_consumer
    ON context_dependents(consumer_kind, consumer_id);
```

`consumer_kind` carries **no `CHECK`**: stories 11, 13, 17 and 20 add
`brief`, `project_facet`, `cadence_run` and `prepared_assignment`, and
widening a SQLite `CHECK` is a table rebuild. *This is a reason for this
column, not house law* -- a sibling lane on this branch shipped
`project_ask_tasks` **with** a `CHECK` (`schema.py:4142-4144`) and was
right to (counsel C15's nuance, adopted).

`stale_reason` uses **C4's shipped words**
(`needs_you_aggregate.py:52`) and only three: `stale`, `unavailable`,
`forbidden`. `''` is fresh.

#### The staleness lattice -- `forbidden` is terminal

Counsel P0-2 found the first draft's trigger **downgrading a
revocation**: `CASE WHEN NEW.deleted = 1 THEN 'unavailable' ELSE
'stale' END` rewrites `forbidden` on the very next Note write, and
`refinement_thought_service` writes a working Note on every accepted
revision (`:142`, `:552`, `:1062`, `:1158`). A consumer fencing on
`forbidden` would then see an ordinary refreshable staleness and
dispatch -- "unauthorized disclosure or execution outside the applicable
scope" from ACCEPTANCE's critical-defect list, defeated by this
design's own push.

**The lattice, stated:**

```
''  (fresh)  →  'stale'        cleared only by a rebind through the reconcile point
             →  'unavailable'  cleared only by a rebind
             →  'forbidden'    TERMINAL. Cleared ONLY by an explicit re-promotion.
                               No trigger and no ordinary edit may leave it.
```

```sql
CREATE TRIGGER IF NOT EXISTS context_dependents_note_au AFTER UPDATE ON notes BEGIN
    UPDATE context_dependents
       SET stale_since  = COALESCE(stale_since, datetime('now')),
           stale_reason = CASE WHEN stale_reason = 'forbidden' THEN 'forbidden'
                               WHEN NEW.deleted = 1            THEN 'unavailable'
                               ELSE 'stale' END
     WHERE canonical_ref = 'note:' || NEW.id;
END;
CREATE TRIGGER IF NOT EXISTS context_dependents_note_ad AFTER DELETE ON notes BEGIN
    UPDATE context_dependents
       SET stale_since  = COALESCE(stale_since, datetime('now')),
           stale_reason = CASE WHEN stale_reason = 'forbidden' THEN 'forbidden'
                               ELSE 'unavailable' END
     WHERE canonical_ref = 'note:' || OLD.id;
END;
```

These two are **new** triggers on `notes`, additive alongside the three
shipped ones (`notes_memory_ai` `schema.py:1214-1218`, `_ad`
`:1219-1221`, `_au` `:1222-1226`) -- a fourth and fifth in an
established house pattern. `COALESCE` keeps the FIRST staleness time.
The `WHERE` hits the PK's leading column, so a Note with no consumers
costs one index probe and matches zero rows.

A trigger cannot hash, so the push is deliberately conservative.
Over-marking says "check this"; under-marking is the breach.

#### The reconcile point -- one per consumer kind

For `consumer_kind = 'thought'` it is `_persist_manifest`
(`refinement_context_service.py:990-1002`), which has **exactly two
call sites**, `:549` (birth) and `:743` (mutate), both inside an open
transaction -- verified by grep, and re-verified by counsel. It does a
scoped delete-then-insert:

1. `DELETE FROM context_dependents WHERE consumer_kind='thought' AND consumer_id=?`
2. one column-named `INSERT` per distinct ref in the manifest (visible
   ∪ leaf, deduped), `bound_manifest_sha256 =
   manifest["attachment_sha256"]`, `consumer_revision =
   manifest["revision"]`.

Bounded at 24 rows by `MAX_VISIBLE = 8` / `MAX_LEAVES = 16`
(`refinement_context_service.py:17-18`). Delete-then-insert is correct
for all four verbs, and dropping `stale` on rebind is correct -- the
manifest just re-bound at the current bytes. **`forbidden` is the
exception: a rebind does NOT clear it**, because the record is under
revocation and re-binding it is exactly what must not silently succeed.
Leaves are indexed as well as visibles because a `knowledge:` visible's
hash covers its members' (`:950-953`); a direct `note:` visible and its
own leaf never collide, because that combination already raises
`context_leaf_overlap` (`:931-938`).

**The invariant, restated honestly** (counsel C9): the first draft sold
"written at ONE call site" as the integrity guarantee. That holds only
for `'thought'`. The true invariant is **one reconcile point per
consumer kind, each doing the same scoped delete-then-insert, and no
other writer.** Stories 11, 13, 17 and 20 each add one, and each owes
the same grep-checkable property for its own kind.

#### The two records, and which answers which question

| Question | Authority | Why |
|---|---|---|
| What does this Thought's face show? | the PULL (`refinement_context_service.py:807-826`) | exact: it recomputes and compares bytes |
| Who consumes `note:n1`? | the INDEX -- one seek | the pull cannot answer this without scanning every revision of every Thought |
| May an unattended run dispatch? | the INDEX, fail-closed | a conservative mark refuses and asks the owner (C9) |

**The index never contradicts the pull; where they differ, the pull
wins for display and the index wins for refusal.**

**The divergence case is real, but not the one the first draft named.**
It claimed "a save that changed nothing" diverges. It does not: an
ordinary re-save bumps `last_modified`, and with `_leaf`'s recipe the
pull would say `stale` too -- the two agree. **The real case** is
`NoteRepository.upsert`'s explicit `last_modified` parameter
(`primitives.py:123`, written at `:141` as `last_modified or now`): a
re-save carrying the **same** `last_modified` UPDATEs `notes`, firing
the trigger, without moving the true content hash. That is the API the
shipped test at `tests/unit/test_refinement_context_service.py:224-229`
already uses. With the new content recipe (D2.2) a byte-identical
re-save *also* diverges, since the new digest excludes the timestamp.
The planned test is named for that mechanism, not for "a no-op save".

#### What "marks stale" DOES for a consumer that is not open

1. **The verb's response names the affected consumers by title, at
   correction time.** Today `_stale_conflict` (`:1113-1119`) can name
   them only once you hold the Thought.
2. **An executor fences on it.** Story 17's cadence run and story 20's
   prepared plan read `context_dependents` for their own
   `(consumer_kind, consumer_id)` before dispatch. **Honest warning
   those stories inherit:** because the push is conservative and
   working Notes are written on every accepted revision, a fence that
   refuses on all three states will refuse *continuously* against a
   record under active edit. Stories 17 and 20 must decide whether
   their fence reads `forbidden`/`unavailable` only, or all three.
   This design does not choose for them; it names the choice.
3. **The consumer's own face reads it on next open**, alongside the pull.

**Nothing is pushed to a notification and no scheduler is introduced**
(C9). And on AC4's second half: after this story a revoked promotion
names its gap **in a service response and in a table, and nowhere the
owner will see**, because ruling C6 ships no face. That is lawful and
ledgered; it is stated here rather than left to read as delivered.

#### The backfill, measured on his live database

The seed is one idempotent statement in the DDL beside the existing
`INSERT OR IGNORE INTO refinement_resume_sequence(id,value) VALUES(1,0)`
(`schema.py:914`), reading only the CURRENT `attachment_revision` and
restricted to `state='working'`.

**Measured read-only on `~/.local/share/holdspeak/holdspeak.db`,
2026-09-07** (`?immutable=1`, no write; counsel re-measured and every
number reproduced): `notes` 17/17 · `refinement_thoughts` 8, **all
`completed`, 0 working** · attachment revisions 4 · visible 5 · leaves 9
· distinct (ref, thought) pairs at current revisions **9**, restricted
to working **0** · `interview_sessions` **0** ·
`knowledge_memberships` 5 · `project_evidence_links` 0 ·
`project_observations` 12 · `projects` 10 (1 active) ·
`thread_message_parts` 28 with **0** sensitive ·
`refinement_default_context_current` revision 0, `refs_json = []`.

**The backfill on his desk is zero rows.**

---

### D2.4 -- P2 settled: reachable by reference, never by relevance

#### What the bounce established

The first draft's primary guard was **containment**: a promotion never
attaches, therefore a promoted Note is "exactly as reachable as one he
typed by hand". The premise is inverted, and I re-walked every limb
myself before rewriting:

| # | Fact | Where |
|---|---|---|
| 1 | `has_explicit_sources = bool(meeting_ids or artifact_ids or qualified_refs)` | `holdspeak/grounding.py:188` |
| 2 | the global relevance pass runs when `include_memory and memory is not None and query and not has_project_ref and **not has_explicit_sources**` | `grounding.py:190-197` |
| 3 | it searches memory, takes the top `GROUNDING_MAX_REFS = 16` and hydrates them, stamping `selection = "ecosystem_relevance"` | `:203-208`, `:209-211`, `:214`; cap at `:24` |
| 4 | the `note` branch those hits land in returns `note.body_markdown` **whole** -- no cap, no sensitivity check. The meeting and thread branches truncate at `GROUNDING_TRANSCRIPT_CAP`; this one does not | `grounding.py:313-321` |
| 5 | the corpus has **no sensitivity condition on notes at all** -- the `p.sensitive=0` filters guard `thread_message_parts`, a different table | `db/memory.py:469-495`; the part filters at `:545` |
| 6 | **every Thread message with non-empty text** calls the hydrator with `meeting_ids=[]`, `artifact_ids=[]`, `include_memory=True` | `services/thread_service.py:380-390` |
| 7 | each block's full text is frozen into `thread_refs.frozen_json` with `"sensitive": False` | `thread_service.py:397-408`, the flag at `:407` |
| 8 | **every Thought refinement** calls it with **empty ref lists, unconditionally** | `services/ask_service.py:516-522`, appended `:526-527` |
| 9 | **every recipe run** does the same, prefixed `"[MEMORY]\n"` | `services/recipe_service.py:111-120`, `:123` |

**Not attaching is the trigger condition for automatic retrieval, not
an escape from it.** The leak sentence passes F1 (section is `goals`),
passes F2 (`sensitive=0`), passes F3 (a newly minted ref cannot already
be in default context) -- and is then pulled by relevance into the next
prompt whose words match it.

And the first draft's best test would have gone green throughout,
because it asserted over `_resolve_manifest`'s `material` -- the
*attachment* envelope -- while the sentence arrives through
`ask_service.py:526-527`. **A test that cannot fail on the real path is
not proof**, and that is the sharpest lesson of the bounce.

#### There are TWO retrieval routes for a note, not one

A verification sweep of every hydrator caller (D3) turned up a second
route that the corpus fence alone would have missed entirely -- and it
is exactly the kind of thing that made the first draft wrong, so it is
named first:

| Route | How a note is selected | Reaches the corpus? |
|---|---|---|
| **Lexical** | the query matches the note's indexed text -- `_note_rows` (`db/memory.py:468-495`) over `notes_memory_fts` | **yes** |
| **Graph** | the note is a one-hop *relationship neighbour* of a lexical seed. `_expand_related_rows` (`db/memory.py:739`) → `_load_related_row` (`:1042`), whose `note` branch reads **`FROM notes WHERE id=? AND deleted=0` directly** (`:1085-1094`), and whose rows are woven into the same `interleaved` list (`:286-290`) and become `MemoryHit`s (`:293-296`) | **NO -- it bypasses the FTS index entirely** |

Both routes end at the same place: `grounding.py:209` hands the hits to
`_hydrate_members` (`:489`), which reaches the `note` branch at
`:313-321` and returns `body_markdown` **whole**. Neither `_note_rows`
nor `_load_related_row` returns a full body themselves -- `_note_rows`
returns a 24-token snippet (`:485`), `_load_related_row` a 420-char
substring (`:1088`) -- so `grounding.py:313-321` is the single place an
unbounded body is produced, via `db.notes.get`.

**A promoted record can therefore be retrieved on words it does not
contain.** Removing it from the corpus closes the lexical route and
does nothing to the graph route.

#### The mechanism: four choke points, only the first by construction

The lexical perimeter is small enough to close completely:

| Role | Where |
|---|---|
| the corpus (DDL) | `notes_memory_fts` (`schema.py:1182-1184`) |
| writer 1 | `notes_memory_ai` AFTER INSERT (`schema.py:1214-1218`) |
| writer 2 | `notes_memory_ad` AFTER DELETE (`:1219-1221`) |
| writer 3 | `notes_memory_au` AFTER UPDATE -- delete-then-conditional-insert (`:1222-1226`) |
| writer 4 | the full rebuild, `rebuild_memory_index` (`db/memory.py:126`, notes at `:139-143`) |
| **the only reader** | `MemoryRepository._note_rows` (`db/memory.py:468-495`), matching `:470`, snippet `:485`, join `:491`; plus a row count at `:152`. **There is no reader outside `holdspeak/db/memory.py`** -- swept and confirmed |

**L1 -- exclusion from the corpus (construction). Three parts, and an
ordering that makes the window not exist:**

1. **Order the writes so the trigger never indexes it.** Inside the
   promotion transaction: mint the deterministic ref → **INSERT the
   `context_promotions` row** → **then** upsert the Note. When
   `notes_memory_ai` fires on that INSERT, its guard already sees the
   promotion and the body is **never written to the corpus at all** --
   not even transiently. This composes with P0-4's deterministic mint,
   which is what makes the ref knowable before the Note exists.
2. **Guard both indexing triggers**, so every later write re-evaluates
   and the state self-heals:

   ```sql
   INSERT INTO notes_memory_fts(source_id,title,body_markdown)
   SELECT NEW.id,NEW.title,NEW.body_markdown
    WHERE NEW.deleted=0
      AND NOT EXISTS (SELECT 1 FROM context_promotions
                       WHERE target_ref = 'note:' || NEW.id);
   ```

   (`notes_memory_ai`'s `WHEN NEW.deleted = 0` becomes the same
   `WHERE`.) **Keyed on the EXISTENCE of a promotion, not on
   `disclosure_state`** -- once a record has been minted or appended to
   by promotion it never enters the relevance pool, revoked or not.
   That removes a class of state-dependent bugs and errs closed.
3. **Guard the rebuild** (`db/memory.py:140-143`) with the same
   `WHERE NOT EXISTS`, so a full re-index cannot re-admit what the
   triggers excluded.

For the **append-into-existing-Note** mode the Note is already in the
corpus, so the promotion transaction additionally executes
`DELETE FROM notes_memory_fts WHERE source_id = ?` -- atomic with the
promotion.

**L2 -- union the promoted refs into `excluded`, inside
`MemoryRepository.search`.** This closes the graph route, which no
corpus fence can reach, and any later route into a hit.

The convergence is real -- `MemoryHit(` appears exactly once, at
`db/memory.py:295` -- but **the constructor is the wrong place to
filter**, and the first draft of this section put it there. Three
things happen before it: `lexical_total = len(interleaved)` (`:262`),
`total = len(interleaved)` (`:292`), and the page slice
`interleaved[offset:offset+limit]` (`:293`). Dropping rows inside the
comprehension would make every total count records never returned and
hand back a page shorter than `limit` with no explanation -- and
`grounding.py:215-217` then adds `search.total - len(members)` into
`stats["overflow_count"]`, **booking withheld sources as mere
overflow**. That is "incomplete observation presented as an all-clear"
from ACCEPTANCE's critical-defect list, produced by the fence itself.

**The shipped plumbing already does this job at the right altitude.**
`exclude_refs` is normalised into `excluded` at `db/memory.py:186-192`,
applied to `interleaved` at `:247-252` -- **before the sort and before
`lexical_total`** -- and threaded into `_expand_related_rows` at `:271`
(parameter `:748`) where it is honoured against the neighbour ref at
`:775`. **One union after `:192` closes both routes, keeps every
counter honest, and reuses an idiom rather than adding a second
filtering shape.** The graph route cannot be closed by construction --
there is no derived index to withhold a directly-read row from -- so it
is closed by a predicate, at the one place both routes pass through
before anything is counted.

**L3 -- a belt at the two relevance CALL SITES, not inside the shared
hydrator.** The filter drops promoted refs from the `members` list
immediately before `_hydrate_members(...)` at `grounding.py:209` (the
global pass) and at `:485` (the project-scoped search).

**It must not go inside `_hydrate_members` itself, and the first draft's
stated reason for putting it there was false.** `_hydrate_members`
(`grounding.py:489`) has a **third** caller: `_hydrate_container`
(`:514-535`) invokes it at `:526-528`, and `_hydrate_container` is
exactly what `_hydrate_qualified` dispatches to for an **explicit**
container ref -- the `knowledge:` branch at `:411-430` (members from
`db.knowledge_memberships.list_for_knowledge`, `:415-418`) and the
`zone:` branch at `:431-449` (members from
`db.directory_memberships.list_for_directory`, `:435-438`). So
`_hydrate_members` is **shared** between the relevance path and the
by-reference path, and a filter inside it would drop a promoted Note out
of any explicitly attached KB or zone -- **silently**, because
`_hydrate_members` appends to `unknown` only on a `qualified_ref` parse
failure (`:502-505`). The owner attaches a container by reference and
one member vanishes with no signal: "silent loss of accepted input or
kept work" from ACCEPTANCE's critical-defect list, and it would have
broken the one thing the cost section leans on.

**The shape of that mistake is worth naming**, because it is the same
one that caused the bounce: a fence placed by reading one caller instead
of sweeping all of them. It is why D5 now carries a container test whose
only job is to fail if someone "simplifies" the two call sites back into
the shared function.

**L4 -- the frozen-ref replay is fenced; the receipt is not.** In the
append mode the promoted body may already have been frozen into
`thread_refs` by a *pre-promotion* relevance pass
(`thread_service.py:397-408`, `"sensitive": False` at `:407`). Those
rows are not read once: `_assemble_payload` re-gathers them on **every
turn** -- scoped to the message path (`:2069-2074`), deduped
newest-per-source and capped at 16 (`:2078-2082`) -- and appends each
one's text into a `system` message (`:2084-2106`). That is a durable row
re-sent on every subsequent turn, which is **not** what
`CONTRACTS.md:66` licenses when it declines to promise erasure of prior
messages.

So the replay skips a `note:` ref carrying an active promotion, **and
the `thread_refs` row itself is left untouched.** The distinction is
deliberate and is the whole of the answer: a frozen ref is a *receipt*
of what turn N actually saw, and rewriting it retroactively would
falsify a receipt (Article XI; C12's "retain failed runs"). A replay is
a *disclosure*, and `CONTRACTS.md:63` evaluates disclosure at each
disclosure. **Receipts are immutable; replays are fenced.**

Four layers, four files, four independently testable properties. **Only
L1 is construction.** L2, L3 and L4 are predicates at convergence
points, and this section says so rather than calling all four "by
construction" -- which is what the first draft did, and it was wrong
twice.

#### The fence travels with the record (P0-C)

L1 is "by construction" **on the writing device only**, and the first
draft did not observe that the fence does not travel with the body it
protects. `SYNC_REGISTRY` registers
`SyncKindSpec("note", "notes", "note.schema.json", True)`
(`services/sync_service.py:35`), `_MERGEABLE["notes"]` declares
`body_markdown` a merged field (`:120`), and the merge writes through
the note repository (`:660-675`). **`context_promotions` has no
`SyncKindSpec`.** On the receiving device the note INSERT fires
`notes_memory_ai`, the guard's `NOT EXISTS` finds no promotion row, and
the body enters that device's relevance corpus -- the pre-bounce state,
on device B. Notes are a synced content class today; the iPad/HSM track
is why the class exists.

**The ruling: the fence travels with the record.** Three parts:

1. **`context_promotions` gets a `SyncKindSpec`**, placed **before**
   `note` in the registry tuple -- registry order *is* apply order,
   verified: `push` iterates `for spec in SYNC_REGISTRY:` and calls
   `spec.merger` in that order (`sync_service.py:1417-1419`). `note` is
   currently third (`:35`), so the promotion spec goes ahead of it and
   promotions land first.
2. **A custom `merger`, not `_MERGEABLE`.** `SyncKindSpec` carries a
   `merger` field for exactly this (`:29`), and `:1064-1065` currently
   assigns `_merge_primitive_spec` only for buckets in `_MERGEABLE` --
   that line gains a branch. `_MERGEABLE`'s last-write-wins field merge
   (`:666-668`) is **wrong here**, because of the disagreement rule
   below.
3. **A post-apply sweep**, so correctness does not rest on ordering
   alone: after promotions are applied, `DELETE FROM notes_memory_fts
   WHERE source_id IN (<the applied targets>)`. One repair per applied
   promotion; the guarded `_au` then declines to re-insert on every
   later write, so it self-heals from there. **Restore and import have
   the same root cause and the same answer** -- any path that recreates
   notes inherits the guard *provided the promotion rows are restored
   too*.

**When the two sides disagree about a promotion's disclosure state,
`revoked` wins -- regardless of timestamp.** This is deliberately NOT
last-write-wins. D2.7's state machine makes `active → revoked` a
one-way transition, so the merge is a monotone join, not a race: under
LWW a stale device still holding `active` could **un-revoke** a
revocation the owner made on his laptop. A promotion row is likewise
**never deleted by sync** -- a tombstone would be an un-revoke by
another name. Same reasoning as `forbidden` being terminal in the
`context_dependents` lattice, and the same direction of error: the
merge fails closed.

**Landing it on an existing database.** L1 part 2 changes two SHIPPED
triggers, and `CREATE TRIGGER IF NOT EXISTS` cannot revise a historical
one -- the reconciler says so in its own words at
`holdspeak/db/reconcile.py:552`. The named mechanism already exists:
`_refresh_tool_turn_lifecycle_guards` (`reconcile.py:549-578`) builds a
reference database from `SCHEMA_SQL` in memory, compares each canonical
trigger's SQL to the live one, and DROPs + CREATEs only where they
differ; it is called from `reconcile_schema` immediately after
`executescript(SCHEMA_SQL)`. This design **extends that function's
`names` tuple** with `notes_memory_ai` and `notes_memory_au` rather
than inventing a second mechanism. The reconciler's additive-only
invariant (`reconcile.py:4-7`: never DROP a table, DROP a column, or
DELETE a row) is preserved -- a trigger refresh is none of those, and
is already precedented.

**Belt as well as braces.** `_note_rows` (`db/memory.py:468-495`) also
gains the predicate as a second, independent clause. The corpus
exclusion is the construction; the query predicate is the belt that
survives a botched trigger refresh. Counsel's own caveat -- that its
eleven-path map is "a floor, not a ceiling" -- is the argument for two
independent mechanisms rather than one.

#### Why this, and not the two alternatives

**Not a `notes` row at all** (the brief asked this be weighed). A
separate `working_context_records` table would sidestep the corpus
entirely. **It kills AC2.** `refinement_attachment_visible.visible_kind`
is `CHECK (visible_kind IN ('note','knowledge'))` (`schema.py:975`) and
`RESOURCE_KINDS` has 20 kinds with no room for a 21st without touching
`qualified_ref`'s validator (`relationships.py:17-22`, `:31-32`);
widening that `CHECK` is a table rebuild, not additive. Two Thoughts
could not share a record the attach machinery refuses, so AC2 would be
undeliverable rather than narrowed. It also contradicts `CONTRACTS.md:57`
("into existing Notes, Thoughts, or Project facets") and the story's own
Scope. **Cost of choosing it: AC2, plus a non-additive schema change,
plus a contract breach.** Rejected.

**`notes.sensitive`.** Still rejected, and the reason still holds even
though the reader count inverted. Nine readers would each have to
honour it -- `grounding.py:313-321`, `db/memory.py:139-142`, `:469-495`,
`:1085-1092`, `refinement_context_service.py:869-882` and `:973-988`,
`thread_modes.py:289`, `support.py:108`, plus the FTS triggers -- and it
**defaults to 0**, so any reader added later that forgets it leaks
silently. It would also have to be honoured on **both** routes -- the
graph route reads `notes` directly (`db/memory.py:1085-1094`), so the
column buys nothing there that L2 does not buy more cheaply. L1 is
strictly stronger than a column for the lexical route: a column is a
predicate every reader must remember; **an absent row is an absent
row**, and a query written next year by someone who never read this
document cannot return bytes that are not there. L2 and L3 are
predicates, but there are two of them at two convergence points, not
nine at nine readers.

**A disclosure class in the verb.** Still rejected: a judgment on free
text at the moment he is least thinking about disclosure, wrong-once-is-
a-breach, and it fails `feedback_ledger_not_gate_rule.md` and
UX-CANON A.3.

#### What it costs, plainly

- **A promoted record is not findable by relevance search.** Not by the
  auto-retrieval pass, not by Desk memory search, not by the
  `memory.search` MCP tool (`holdspeak/mcp/families/memory.py:12-29`,
  which sits in `CHAT_PALETTE` at `services/thread_tools.py:302` classed
  `evidence_read`, not sensitive, at `:139` -- where every `people.*`
  entry is marked sensitive at `:141-157`). That is the ruling's literal
  demand and it is a real usability loss.
- **By-reference discovery survives, and D2.2's minted title is what
  makes that worth anything.** The picker searches `notes` directly --
  `SELECT id,title FROM notes WHERE ... title LIKE ? ESCAPE '\'
  COLLATE NOCASE` (`refinement_context_service.py:637-645`) -- but
  **title only, never body**. Verified. With the title minted from the
  quote (D2.2) he searches for words he actually said and finds them.
  With the model's paraphrase as the title -- the first draft's
  construction -- he would find it by neither route, and "he can still
  find it by title" would have been true and nearly useless. **The bound
  is real because of that one-line change, not independently of it.**
- **In the append mode, a Note that is mostly his own writing leaves
  the relevance pool permanently** because it now contains
  system-extracted text. That is the correct direction and it is a cost,
  not a free win.
- **It does not close whole-table egress**, which is not relevance and
  is not this story's to fix: `desk.snapshot` returns every note via
  `to_dict()` including `body_markdown`
  (`holdspeak/mcp/tools.py:754-755` → `services/desk_service.py:37-47`;
  `NoteRecord.to_dict` at `holdspeak/db/models/__init__.py:568`,
  `body_markdown` at `:572`), `desk.list`/`desk.get` do the same
  (`mcp/tools.py:39-62`), all three in `CHAT_PALETTE`
  (`thread_tools.py:300`), and `SyncService.pull` emits up to 500 full
  note bodies (`services/sync_service.py:1117-1119`, route
  `web/routes/sync.py:38-42`). **Mapped in "cannot promise", tested per
  `CONTRACTS.md:67`, and not blocked** -- blocking sync would break
  synchronisation of the owner's own record.
- One further path, distinct from relevance and worth its own line:
  `ResourcefulService._loose_idea` (`services/resourceful_service.py:163-193`)
  slices a note body to 4000 chars into an autonomous workbench prompt
  (`:190`) when the note is filed in a directory named "Loose Ideas"
  (`:164`). That is **zone membership, not relevance**, so corpus
  exclusion does not close it; a promoted record filed there would be
  picked up. Named, not fixed.

#### The five fences, restated

| # | Fence | Where | What it stops | Status |
|---|---|---|---|---|
| **F0** | **Retrieval exclusion, in four layers** | **L1** ordering + two revised triggers + the guarded rebuild (construction) · **L2** the `excluded` union in `MemoryRepository.search` · **L3** the two relevance call sites · **L4** the frozen-ref replay. Plus the sync spec, so the fence travels | **both retrieval routes, and the replay of anything frozen before the promotion** | NEW; the P0-0 answer, re-placed after counsel's P0-A/B/C |
| **F1** | the section gate on the promotion event | new branch, refusing `state["section"] == "people"` and a fact stored with `section == "people"` | the direct People path, belt-and-braces with `interview_service.py:201` | unchanged |
| **F2** | the quote predicate re-run in-transaction | the SQL at `interview_service.py:69-75` | a source part re-classified or deleted between recording and promotion | unchanged, and **free** -- `_prune_unavailable_facts` is already invoked *inside* the open transaction at `interview_service.py:143`. The first draft under-claimed this |
| **F3** | the auto-attach fence | refuse if `target_ref` is in `refinement_default_context_current.refs_json` (`refinement_context_service.py:70`) or the Everyday KB's membership (`:889`) | **the append-into-existing-Note mode only** | **reworded.** The first draft credited F3 with "the entire leak path". In New-Note mode the service mints the ref, so it is **structurally unreachable** (counsel C8). What closes the auto-attach limb is containment; F3 is still worth building for the append mode, and the walk will never see it fire |
| **F4** | `person:` refuses itself | inherited: `RESOURCE_KINDS` has no `person` (`relationships.py:17-22`), so `qualified_ref` raises at `:31-32` | a `person:` source or target | unchanged; proved by test, not implemented |

The People **store** path remains closed and this design proves it
rather than re-guarding it: People content never becomes a
`thread_message_parts` row (`thread_service.py:359-368` freezes a
`person:` ref display-name-only with `sensitive=True`), and F2 requires
`sensitive=0`. The store is a separate ciphertext file
(`holdspeak/people/store.py:19`, schema `:414-421`) and
`PeoplePolicy` allows only this-device owner operations plus one
capability-gated MCP path (`holdspeak/people/policy.py:42-61`, the
gated branch at `:57`). Fail-closed call sites to copy:
`mcp/families/people.py:384-390`, `:494-499`.

---

### D2.5 -- the tables and the schema changes

**Additive:** three tables, three indexes, two new triggers, one seed.
**House-precedented, not additive:** two shipped triggers revised
through `reconcile.py:549-578`'s mechanism, and one shipped query
(`db/memory.py:140-143`) gaining a predicate.

```sql
-- HS-200-10: one promotion of one Interview fact into one canonical record.
-- The quote is a LOCATOR + HASH, never a copy: provenance stays provable while
-- revoking the source actually removes the text.  The excerpt-locator idea is
-- borrowed from project_evidence_links.excerpt_locator_json (schema.py:3876),
-- whose writer has zero references anywhere; this table is deliberately NOT
-- project-scoped, because a promotion must work on a desk with no Project.
-- `promotion_id` and, in new-Note mode, `target_ref` are BOTH deterministic
-- from (thread_id, fact_id) -- the generate_pobs_id pattern
-- (holdspeak/project_contracts.py:292) -- so a double-click collides here
-- instead of minting two Notes.
CREATE TABLE IF NOT EXISTS context_promotions (
    promotion_id TEXT PRIMARY KEY,
    thread_id TEXT NOT NULL,
    fact_id TEXT NOT NULL,
    source_message_id TEXT NOT NULL,
    quote_sha256 TEXT NOT NULL,
    quote_locator_json TEXT NOT NULL DEFAULT '{}',
    target_kind TEXT NOT NULL DEFAULT 'note',
    target_ref TEXT NOT NULL,
    target_revision_label TEXT NOT NULL DEFAULT '',
    target_content_sha256 TEXT NOT NULL DEFAULT '',
    disclosure_state TEXT NOT NULL DEFAULT 'active',
    request_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (thread_id, fact_id, target_ref)
);
CREATE INDEX IF NOT EXISTS idx_context_promotions_target
    ON context_promotions(target_ref);
CREATE INDEX IF NOT EXISTS idx_context_promotions_source
    ON context_promotions(source_message_id);

-- HS-200-10: the suppression side-table.  Copies calendar_event_link_suppressions
-- (schema.py:4103-4114): keyed by the DURABLE identity, so re-typing the quote
-- cannot resurrect a promotion the owner revoked.
CREATE TABLE IF NOT EXISTS context_promotion_suppressions (
    thread_id TEXT NOT NULL,
    fact_id TEXT NOT NULL,
    target_ref TEXT NOT NULL,
    reason TEXT NOT NULL DEFAULT 'revoked',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (thread_id, fact_id, target_ref)
);
```

`idx_context_promotions_target` is what makes F0's trigger guard and
the multi-promotion revoke rule (D2.6) index seeks rather than scans.

`target_kind` and `disclosure_state` carry no `CHECK` for the reason
given in D2.3 -- widening one is a table rebuild -- and the service
validates instead.

**Every INSERT names its columns**
(`reference_positional_inserts_reconcile_order`).

---

### D2.6 -- the verb, its owner, its transport

**Owner: `InterviewService`.** A promotion is an interview
*disposition*, the category `remove_fact` and `disposition` already
occupy in `_reduce` (`interview_service.py:157-191`). No second state
machine over `notes` is created: the ordinary Note edit remains the
only way to change one.

**Two event kinds**, both on `InterviewService.command()`
(`:115-152`), inheriting its whole concurrency contract:

| Event | What it does, in order |
|---|---|
| `promote` | F1 → F2 → F3 → derive `target_kind` from the ref → mint the deterministic promotion id and (new-Note mode) the deterministic `target_ref` → check the suppression table → **INSERT `context_promotions`** → **then** upsert the Note via `notes._upsert_in_transaction` on the same `conn` → (append mode only) `DELETE FROM notes_memory_fts` → set `fact["promoted_to"]` |
| `revoke_promotion` | `disclosure_state = 'revoked'`, one suppression row, and the dependent marking below |
| `remove_fact` (**existing**, `:161-165`) | unchanged. Removing a fact does NOT revoke its promotion -- the Note is his now. Deliberate, and stated so the asymmetry is not discovered later |

#### Revocation when one record carries several promotions (counsel P0-3)

`UNIQUE (thread_id, fact_id, target_ref)` deliberately permits **N
promotions into one `target_ref`** -- the append mode is the design's
own second mode. Marking every dependent `forbidden` on the first
revoke would poison a record that is still legitimate, and with the
lattice fixed `forbidden` is terminal, so the poison would be
permanent.

**The rule:** `revoke_promotion` marks the target's dependents
`forbidden` **only when no `disclosure_state='active'` promotion into
that `target_ref` survives the revoke.** Otherwise it marks them
`stale` and the response names the removed quotation. One index seek on
`idx_context_promotions_target` decides it.

#### What `revoke` revokes (counsel P0-6)

**`revoke_promotion` revokes the CLAIM THAT A SOURCE BACKS the record.
It does not revoke the record.** The Note stays -- deliberately, because
it is his work. `CONTRACTS.md:63`'s "evaluated at each disclosure" is
therefore met **only for consumers that read `context_dependents`** --
not for ref hydration (`grounding.py:313-321`), not for
`desk.snapshot`/`desk.list`/`desk.get`, not for export
(`sync_service.py:1117-1119`). None of those reads
`context_promotions.disclosure_state`. Corpus exclusion (F0) does remove
the record from relevance permanently, which is the one disclosure
surface revocation genuinely closes. This is repeated in "cannot
promise" because "revoke" is the word the owner will read most
literally.

**Transport.** `web/routes/threads.py:87`'s allowlist gains `"promote"`
and `"revoke_promotion"`. **The MCP interview family
(`mcp/families/interview.py:27-40`) gains nothing.** Ruling C6 was
amended to say so. The shipped asymmetry -- browser allowlist
`{section, remove_fact, disposition, status}` versus the model's four
read/record tools -- encodes that the model records and the owner
disposes; a `promote` tool would let a model mint a canonical record.

**Authority.** Owner-only: `command()` calls `require_owner` (`:121`,
defined `:36-39`).

**No face.** Ruling C6 as amended; counsel C14. The earlier plan to add
one `Button` and one `StateChip` to `InterviewPanel.tsx:120-131` is
**struck**, so no build lane can read this document as licence to add
the control. UX-CANON A.11 is satisfied by withholding the verb and
ledgering it. The ledger entry is owed.

---

### D2.7 -- state, transactions, failure windows

**Promotion state.** `active` / `revoked` is the only STORED axis.
`current` / `corrected` / `unavailable` / `source_unavailable` are
DERIVED on read by comparing the content hash -- the same
detect-on-read discipline as `refinement_context_service.py:807-826`.

**Transaction boundary.** One `BEGIN IMMEDIATE`, the one `command()`
already opens (`interview_service.py:126`): the fences, the promotion
row, the Note upsert, the FTS delete, the interview state (`:145-149`)
and the event row (`:151`). **No cross-service transaction** (C6).

**Every fence reads on the transaction's own `conn`** (counsel C7). The
first draft named `_reduce` (`:154-191`) as "the reducer to extend", but
`_reduce(self, thread_id, state, event, now)` takes **no `conn`**, and
its `_fact` branch reads through a *second* connection while the write
transaction is held (`self._db.threads.get_message` at `:209`,
`get_parts` at `:213`). That is safe today only because
`BEGIN IMMEDIATE` holds the write lock -- an accident, not a design.
**The change:** either `_reduce` gains a `conn` parameter, or `promote`
is handled in `command()` beside the state upsert. **The `_fact`
pattern at `:209`/`:213` is not the pattern to copy**, and the design
says so explicitly so a future reader does not.

**Idempotency** comes from the replay guard `(thread_id, command_id)`
with a `request_digest` (`:133-137`), *plus* the deterministic mint,
which is what covers the two-clicks case the guard cannot.

| Window | Required behaviour | How it is met |
|---|---|---|
| Crash before commit | nothing written | one transaction; record, Note, corpus delete and interview revision commit together or not at all |
| Crash after commit, before the response | replay, no second Note | `interview_events` guard (`:133-137`) |
| Same command id, changed payload | conflict | `interview_command_conflict` (`:135-136`) |
| **Two clicks, two command ids** | one Note | **deterministic `target_ref` from `(thread_id, fact_id)`** → UNIQUE collision → `updated_at` touch |
| **Death between the record write and the index write** | no torn state | **impossible by construction: promotion writes NO `context_dependents` row at all**, because it never attaches. The cleanest answer in this section, and counsel is right that the first draft only implied it |
| Note edited between promotion and read | reads `corrected`; dependents already marked | content-hash recompute + the AFTER UPDATE trigger |
| **Revoke of one promotion among several on one record** | the record is not poisoned | mark `forbidden` only if no active promotion into that `target_ref` survives (D2.6) |
| **A Note write after a revocation** | the revocation stands | the lattice: `forbidden` is terminal in both triggers (D2.3) |
| Source message deleted after promotion | the fact is pruned (`:67-80`); **the promotion survives** and reads `source_unavailable` | `context_promotions` is not derived from interview state |
| Note hard-deleted (`db/primitives.py:204`) | dependents marked `unavailable` (unless `forbidden`) | AFTER DELETE trigger |
| Source revoked mid-promotion | no TOCTOU window | `BEGIN IMMEDIATE` holds the write lock -- **provided the fences read on `conn`** (C7) |
| A model re-records the same fact after a revocation | the FACT may return; the PROMOTION cannot | the suppression row is checked before every promote |
| A promoted Note the owner later adds to default context himself | permitted -- his explicit act, on a face whose subject is that decision | F3 fences only the promotion direction |

---

### D2.8 -- two narrowings, recorded where they are gated (counsel C11)

A story ruling does not amend a phase contract. Both of these are
one-line ledger entries owed in the shipping change, not silent:

1. **`CONTRACTS.md:57`** -- "promoted from Interview into existing
   Notes, **Thoughts, or Project facets**." This story ships `note`
   only (ruling C3), with `promotion_target_unsupported` for the other
   two and the reasons in D2.2. **Counsel read all four downstream
   stories (11, 13, 17, 20) and reports that none requires promoting
   *into* a Thought or a Project facet** -- each needs a *consumer*, a
   ref, or a fence. The narrowing is survivable downstream; what it
   touches is the phase contract line, which must carry the note.
2. **`ACCEPTANCE.md:33` (P200-A08)** -- "reuse it in **another
   Thread**." Ruling C7 narrows AC2 to Thought scope and "cannot
   promise" #5 says Thread scope is undeliverable here. A08 is a phase
   acceptance scenario, not a story AC, and must carry the note.

Left alone these become an end-of-phase surprise at G1 sign-off.

---

## D3 -- the wire

**MISSING** means it does not exist on this branch.

### The retrieval seam (AC5's real path -- new after the bounce)

| What | Where |
|---|---|
| `has_explicit_sources` -- the trigger condition | `holdspeak/grounding.py:188` |
| The global relevance pass and its guard | `grounding.py:190-197` |
| Search, cap, hydrate, stamp | `:203-207`, `:208` (cap `GROUNDING_MAX_REFS = 16` at `:24`), `:209-211`, `:214` |
| The uncapped, unchecked `note` hydration branch | `grounding.py:313-321` |
| The four public hydrators | `hydrate_refs_detailed` `:93`; `hydrate_refs` `:236`; `hydrate_grounding_blocks_detailed` `:538`; `hydrate_grounding_blocks` (exported `:751-770`). **There is no `grounding.build`** -- the proof runs through `hydrate_refs_detailed` and `hydrate_grounding_blocks_detailed` on the unattached path |
| **The second route -- graph expansion, which never touches the corpus** | `_expand_related_rows` (`db/memory.py:739`) → `_load_related_row` (`:1042`), `note` branch reading `FROM notes WHERE id=?` at `:1085-1094`; woven `:286-290`; hits built `:293-296` with `retrieval_origin` at `:306` |
| **`_hydrate_members` is SHARED, not relevance-only** | def `grounding.py:489`; relevance callers `:209` (global) and `:485` (project-scoped); **by-reference caller `_hydrate_container` (`:514-535`) at `:526-528`**, reached from the explicit `knowledge:` branch (`:411-430`) and `zone:` branch (`:431-449`). It reports `unknown` only on a parse failure (`:502-505`), so a filter inside it is silent |
| Where the overflow receipt is written | `grounding.py:215-217` -- `search.total - len(members)` |
| The `excluded` plumbing L2 reuses | `db/memory.py:186-192` (normalised), `:247-252` (applied before the sort and before `lexical_total` at `:262`), `:271` (threaded into `_expand_related_rows`, parameter `:748`), `:775` (honoured against the neighbour ref). The counters L2 must not corrupt: `:262`, `:292`, `:293`; the single `MemoryHit` site `:295` |
| **The frozen-ref replay (L4)** | written `thread_service.py:397-408` (`"sensitive": False` at `:407`); re-gathered every turn `:2069-2074`, deduped and capped `:2078-2082`, appended as a `system` message `:2084-2106` |
| **The sync seam (P0-C)** | `SYNC_REGISTRY` `services/sync_service.py:34-56`, note spec `:35`; `SyncKindSpec` `:21-29` with its `merger` field `:29`; `_MERGEABLE["notes"]` `:120`; the LWW merge write `:660-675`; merger assignment `:1064-1065`; **apply order = registry order**, `push` iterating at `:1417-1419`; pull emission `:1117-1119` |
| The corpus | `notes_memory_fts` (`schema.py:1182-1184`) |
| Its four writers | `schema.py:1214-1218`, `:1219-1221`, `:1222-1226`; `db/memory.py:139-143` |
| Its only reader | `db/memory.py:468-495` (`_note_rows`), plus a count `:152` |
| **The nine call sites that reach the pass** (swept; the four ALWAYS and the five CONDITIONAL are listed below this table) | see the census |
| The trigger-refresh mechanism to extend | `holdspeak/db/reconcile.py:549-578` (`_refresh_tool_turn_lifecycle_guards`), whose docstring at `:552` states the exact problem: "SQLite's `CREATE TRIGGER IF NOT EXISTS` cannot revise a historical trigger" |
| The reconciler's additive invariant | `reconcile.py:1-7` |
| **By-reference discovery, which corpus exclusion does NOT break** | `refinement_context_service.py:635-646` -- the context picker searches `notes` directly with `title LIKE`, not the FTS index |
| Zone-membership autonomy, a separate path | `services/resourceful_service.py:163-193`, body sliced at `:190` |

**The call-site census.** Counsel's map was offered as "a floor, not a
ceiling" and asked the re-take to grep the call signature rather than
trust it. Swept over `holdspeak/` and `web/`, excluding tests and
worktrees. `include_memory` defaults to **False**
(`grounding.py:100`) and all three wrappers forward it verbatim, so a
site that omits it can never fire.

| Verdict | Sites |
|---|---|
| **ALWAYS FIRES** (literal empty ref lists) | `services/ask_service.py:516-522` (every Thought refinement) · `services/recipe_service.py:111-120` (every recipe run) · `services/sequence_workflow_service.py:49-56` (every Sequence/Workflow model node; `"[MEMORY]\n"` at `:60`) · `web/routes/system/coder_steering_support.py:103-105` via `services/coder_service.py:130-149` (`include_memory=True` at `:148`, `qualified_refs` never passed) |
| **CONDITIONALLY FIRES** -- and in every one the "explicit sources" come from an optional request field defaulting to `[]`, so **empty is the normal case** | `services/ask_service.py:573-580` (every Desk Ask with no attachments) · `services/recipe_service.py:202-209` · `services/thread_service.py:380-390` (every plain chat turn) · `workbench_conductor.py:205-213` · `coder_steering_support.py:144-145` |
| **NEVER FIRES** (`include_memory` omitted) | `ask_service.py:171`, `ask_service.py:478` |

Two of those are worth their own line. `thread_service.py:380-390` is
the only site that **persists** the hydrated text -- whole note bodies
into `thread_refs.frozen_json` with `"sensitive": False` (`:407`), so
the sensitivity redaction in `_assemble_payload` can never redact them.
And `coder_steering_support.py:103-110` composes the blocks
(`compose_steer`, `:110`) and `coder_steering_routes.py:424-433` types
the result into a **third-party coding agent's terminal pane**
(`payload["text"]` at `:428`) -- relevance-driven egress off the
machine entirely.

### The promotion seam (AC1)

| What | Where |
|---|---|
| The command envelope | `interview_service.py:115-152` -- `BEGIN IMMEDIATE` `:126`, live recheck `:128-131`, replay guard `:133-137`, revision check `:140-142`, `_prune_unavailable_facts` in-transaction `:143`, state upsert `:145-149`, event row `:151` |
| The reducer, **and its connection problem** | `_reduce` at `:154-191` takes **no `conn`**; `_fact` reads on a second connection at `:209` and `:213`. See D2.7 (C7) |
| Quote enforcement, already built | `:213-215` |
| The recheck predicate | `:69-75` |
| Owner gate | `:36-39`, called `:121` |
| Note write on the same connection | `db/primitives.py:120-142`; the shipped caller pattern at `services/refinement_thought_service.py:142` |
| The unconditional `last_modified` write (P0-1's cause) | `db/primitives.py:137`, value at `:141` |
| Deterministic-id precedent | `holdspeak/project_contracts.py:292` (`generate_pobs_id`), rationale `schema.py:3850-3851` |
| Web transport | `web/routes/threads.py:78-91`; allowlist `:87` |
| MCP surface | `mcp/families/interview.py:27-40` -- four tools. **This design adds none** |
| **MISSING: any promotion verb** | no method, event kind, route, tool or table |
| **MISSING: provenance columns on `notes`** | `schema.py:872-881` |
| **MISSING: a revision on a ref** | `relationships.py:25-33` |

### The reference seam (AC2)

| What | Where |
|---|---|
| Refs + hashes only, body re-read live | `schema.py:970-981`; `refinement_context_service.py:869-882`, `:973-988` |
| The stale comparator | `:815-818` |
| The one reconcile point for `'thought'` | `:990-1002`, called `:549` and `:743` -- exactly two call sites |
| The mutate funnel and its `unchanged` branch | `:681-779`; `unchanged` computed `:730-734`, gating `_persist_manifest` at `:736-743` |
| Proof N Thoughts share one copy | `tests/unit/test_refinement_context_service.py:220-244` |
| **A Thread's grounding IS a copy** | `schema.py:3614-3622`, written `thread_service.py:397-408` |

### The correction seam (AC3)

| What | Where |
|---|---|
| Detect-on-read staleness; the named repair | `refinement_context_service.py:807-826`; `:1113-1119` |
| Suggestion invalidation on a fact edit | `interview_service.py:194-197`, triggered `:221-222` |
| Its limit | covers suggestions only; `refinement_context_service.py:898-901` / `:926` raise `context_kind_unsupported` for everything but `note:` and the Everyday seed (`:16`) |
| The trigger pattern to copy | `schema.py:1213-1226` |
| The idempotent-seed precedent | `schema.py:914` |
| The chatty writer | `refinement_thought_service.py:142`, `:552`, `:1062`, `:1158` |
| **MISSING: any reverse index** | `schema.py:979-980` is thought-first; `project_evidence_links`' index `:3880-3881` points at the consumer |
| **MISSING: any push** | every staleness path in the tree is detect-on-read |

### The revocation and gap seam (AC4)

| What | Where |
|---|---|
| Suppression shape to copy | `schema.py:4103-4114`, consulted `db/calendar_event_projects.py:271-287` |
| Tombstone; state flip | `services/project_service.py:2745-2749`; `services/authority_service.py:183-186` |
| The shipped gap vocabulary | `services/needs_you_aggregate.py:52`; kinds `:53`; record `:91-113`; repair `:65-88` |
| Its limits | `COVERAGE_KINDS` has no context kind; `_repair` hard-wires hrefs at `:71`, `:76`, `:78`, `:83`, `:85`, `:88`. **Not widened here** -- story 15's |
| **The forget-not-suppress defect** | `interview_service.py:67-80` |

### The People seam (AC5, the direct paths)

| What | Where |
|---|---|
| Ciphertext sidecar, outside the main schema | `holdspeak/people/store.py:19`; schema `:414-421` |
| The policy | `holdspeak/people/policy.py:42-61`; the one gated branch `:57` |
| Fail-closed call sites | `mcp/families/people.py:384-390`, `:494-499` |
| `person` is not a resource kind | `relationships.py:17-22` (**20** kinds); raises `:31-32` |
| Interview refuses the People section | `interview_service.py:201`, `:226` |
| Thread ingress refused | `thread_service.py:314-320` |
| `person:` freezes display-name-only + sensitive | `thread_service.py:359-368` |
| Grounding excludes sensitive PARTS -- **thread kind only** | `holdspeak/grounding.py:394`. *The brief cited `holdspeak/services/grounding.py:394`, which does not exist.* The `note` branch at `:313-321` has no check |
| Memory excludes sensitive PARTS -- `thread_message_parts`, not `notes` | `db/memory.py:545` |
| The auto-attach limb (closed by containment) | `refinement_context_service.py:70`, `:515-582`, `:889` |
| **MISSING: any sensitivity concept on the target** | `notes`: `schema.py:872-881`. The schema's only one is `thread_message_parts.sensitive` (`:3608`) |

### The face seam -- **STRUCK** (ruling C6 as amended; counsel C14)

No face ships in this story. The honest note stands and is all that
remains: **no ratified board draws promotion**, and the panel a control
would land on (`web/src/desk/components/InterviewPanel.tsx`) is
pre-Surface-canon in its own right -- raw `<details>` at `:105` and
`:117`, a `Select` rather than `CycleGadget`. The face owes a board
before any verb is drawn.

### The carried unknown -- **CLOSED, from both sides**

Browser side, traced by this design: `RoomAskWell`'s prompt lives in
`useState` only (`web/src/features/project-room/ProjectRoomCore.tsx:1387-1388`)
and `runAsk`'s docstring reads *"Persists nothing — keep/bin is yours"*
(`web/src/desk/ask.ts:127`).

Server side, closed by a sibling lane on this branch:
`holdspeak/db/schema.py:4115-4118` -- "`/api/ask` is one blocking
request/response ... and persists nothing -- the kernel journals a
payload hash, and `ask_results` holds the answer without the question."
That lane's `project_ask_tasks` (`schema.py:4134-4157`) is the durable
record HS-200-41 adds. **Cannot-promise #4 is closed.**

---

## D4 -- the hunts (what fails on his desk)

Measured read-only 2026-09-07; counsel re-measured and every number
reproduced.

**1. THE RETRIEVAL PATH IS LIVE ON HIS DESK TODAY, before this story
ships.** His corpus is 17 notes; the pass takes 16 slots
(`grounding.py:24`, `:208`). **On his machine almost every note he owns
is a candidate on almost every message he types**, and nothing labels an
auto-retrieved block differently from an attached one. **This is
walkable now, with none of this story's code**: promote nothing, type a
message whose words match an existing note, and read
`thread_refs.frozen_json`. It should be beat one of the walk, because
it is the fact that bounced this design.

**2. The `corrected` false positive is what bites next** -- and it is
fixed in D2.2 rather than admitted. With `_leaf`'s recipe, the first
promotion plus any re-save would have reported his constraint as moved.
The new content recipe excludes the timestamp. **The walk must still
try it**: promote, re-save the Note unchanged, and read the state.

**3. He has ZERO Interview sessions and ZERO working Thoughts.** There
is not one fact to promote and not one Thought to index. The backfill is
0 rows. Nothing here can be demonstrated on existing data, and any
evidence claiming "promoted his existing context" would be false.

**4. His default context is EMPTY** (revision 0, `refs_json = []`), so
the auto-attach limb is dormant, and **F3 will never fire on his desk**
-- his default context is empty and the common mode is New Note, where
F3 is structurally unreachable (C8). The walk cannot show F3 working
without a constructed setup.

**5. He has ZERO sensitive message parts.** Every guard keying on that
flag has never fired on his machine. AC5's proof must be a constructed
scenario running through the hydrator, not an assertion over his data.

**6. Corpus exclusion will feel like a loss before it feels like a
fence.** The first time he promotes a sentence and then cannot find it
in Desk memory search, that is the design working as ruled. The repair
is the context picker -- **and it only works because D2.2 now mints the
title from his quote.** The picker reads `title LIKE` and nothing else
(`refinement_context_service.py:637-645`); with the model's paraphrase
as the title he would have searched for the sentence he said and found
it by neither route. **Walk this beat explicitly: promote, then look for
it the way he would.** If he reaches for search first, the answer is a
better path to the picker, never a hole in F0.

**7. The trigger fires on every working-Note save**
(`refinement_thought_service.py:142`, `:552`, `:1062`, `:1158`). With
the new content recipe the pull and the index can now genuinely
disagree, so the face reads truthfully -- but the **fence** stories 17
and 20 inherit will refuse continuously against a record under active
edit. Named in D2.3 as their choice to make.

**8. `remove_fact` does not revoke.** Deleting the fact leaves the Note
and the promotion standing. Deliberate; a surprise; must be said.

**9. Revocation does not un-say what already went to a model**, and
does not remove the record from `desk.snapshot` or `sync.pull`. C3
licenses the first; D2.6 and "cannot promise" state the second.

**10. Relevance can send a note body off the machine entirely.**
`coder_steering_support.py:103-105` hydrates with `include_memory=True`
and no refs (via `coder_service.py:148`), `compose_steer` folds the
blocks in (`:110`), and `coder_steering_routes.py:424-433` types the
result into a **third-party coding agent's terminal pane**. That is a
pre-existing path for every note he owns; F0's four layers close it
for promoted records specifically, because they fence the retrieval,
not the caller. **It is the strongest argument for fencing at the
retrieval rather than at nine call sites**, and it should be on the
walk.

The framing survives review on the ledger law: `deliver_process_input`
carries a `policy` and a `steering_commitment` (`coder_steering_routes.py:414-421`),
its payload names the refs (`:431`), and the result is checked for an
`audit_id` (`:434`) -- a disclosure with provenance, which
`feedback_ledger_not_gate_rule.md` asks for. **What is missing is a
FACE law, and it belongs in the ledger entry so the owning story
inherits something specific.** `buildGrounding` returns `null` precisely
when the owner picked nothing (`web/src/desk/grounding.ts:112-113`), so
the face shows **no egress chips at the moment relevance is about to
pick sixteen sources and type them into a third-party pane**. UX-CANON
A.9 puts the badge at composition time, not only in the audit record
afterwards. *Counsel's finding and its citations; I verified the
server-side half (`coder_service.py:148`, `coder_steering_support.py:103-110`,
`coder_steering_routes.py:424-433`) and not the browser half.*

**11. `use_zone_context` reads like a live privacy switch and is
inert** -- persisted and synced (`services/sync_service.py:122`) and
read by no context assembler. *Counsel's finding; I did not
independently trace every assembler.* Worth a ledger line in whichever
story owns that control; not this one's to fix.

**12. The fence is device-local until its sync spec lands, and his
desk is the two-device case.** Notes are a synced content class today
and the iPad/HSM track is why the class exists. Until
`context_promotions` syncs (D2.4), a promoted record arriving on a
second device re-enters that device's relevance corpus -- the
pre-bounce state, one device over. **This is the one P0 whose failure
he could actually meet**, because everything else in this story starts
empty on his machine.

**13. Two unmeasured costs.** The two new triggers' write cost, and the
`INSERT OR IGNORE ... SELECT` seed running on every open of an 85 MB
database. Neither will surface at his scale (17 notes, 4 attachment
revisions). **Do not treat a quiet walk as proof either is cheap.**

---

## D5 -- the proof

Planned suite **`phase200_working_context`**: state tests in
`tests/unit/test_phase200_working_context.py`, real-service flows in
`tests/integration/test_phase200_working_context.py`.

Two existing tests are **cited and extended, never mirrored**:
`tests/unit/test_interview_service.py:74` (a fact edit flips dependent
suggestions `stale`) and `tests/unit/test_refinement_context_service.py:220`
(a Note edit makes an attachment `stale`; only `refresh_context`
accepts the new version, `:229-244`) -- whose `_attach`/`_cursors`
helpers and explicit-`last_modified` upsert API (`:224-229`) the new
tests reuse.

**The evidence file carries the boundary tests' output BEFORE the index
tests'**, matching the lane order (ruling C1 as extended).

### Boundary tests (AC5, AC4, AC1) -- these run first

| Test | What it demonstrates |
|---|---|
| **`test_a_promoted_record_is_never_returned_by_the_unattached_retrieval_pass`** | **The P0-0 re-enactment, through the REAL envelope.** Type the relationship sentence in `goals`, record the fact, promote it, then call `hydrate_refs_detailed(db, meeting_ids=[], artifact_ids=[], qualified_refs=[], query=<words from the sentence>, include_memory=True)` -- the exact unattached shape `ask_service.py:516-522` uses -- and assert **no returned block carries the sentence**, and that `stats["selection"] == "ecosystem_relevance"` (proving the pass actually ran rather than being skipped). A control note with the same words IS returned, so the test fails if F0 is removed |
| **`test_a_promoted_record_is_not_returned_through_the_GRAPH_route`** | The second route, which the corpus fence does not close. Seed a lexical match on note A, make the promoted note B a one-hop relationship neighbour of A, and assert B is absent from `MemoryRepository.search(...).hits` -- i.e. L2 fires. A control neighbour that is not promoted IS returned, so the test fails if L2 is removed. Without this test L1 alone looks green and the boundary is open |
| `test_the_two_relevance_call_sites_drop_a_promoted_ref` | L3 where it now lives: the `members` list is filtered before `_hydrate_members` at `grounding.py:209` and `:485` |
| **`test_an_explicitly_attached_knowledge_or_zone_container_still_hydrates_a_promoted_member`** | **The P0-A regression guard.** An explicit `knowledge:` ref (`grounding.py:411-430`) and an explicit `zone:` ref (`:431-449`) each carrying a promoted Note still return that member's body. Its only job is to **fail the moment someone "simplifies" the two call sites back into the shared `_hydrate_members`** -- the silent-drop defect, which reports no unknown ref (`:502-505`) and so would otherwise surface as missing prompt content and nothing else |
| `test_by_reference_hydration_of_a_direct_note_ref_is_unaffected` | `_hydrate_qualified` (`:261`) still returns the body -- attach unbroken |
| **`test_search_totals_and_page_length_survive_the_exclusion`** | **The P0-B guard.** With a promoted record excluded, `search.total`, `lexical_total` and the returned page length are the honest post-exclusion numbers, and `grounding.py:215-217` books **zero** withheld sources as overflow. Fails if the predicate migrates back to the `MemoryHit` constructor (`db/memory.py:295`) |
| **`test_a_promoted_record_arrives_promoted_on_a_second_device`** | **The P0-C guard.** Apply a sync payload carrying both the note and its promotion; assert the note's body is absent from the receiving device's `notes_memory_fts`. Run it once with promotions ordered first and once with the note first, so the post-apply sweep is proved to cover the ordering the registry does not guarantee |
| `test_a_revoked_promotion_wins_over_an_active_one_in_a_merge` | the monotone join: `revoked` beats `active` regardless of `last_modified`, in both directions, and a promotion row is never tombstoned by sync |
| **`test_a_frozen_thread_ref_predating_the_promotion_is_not_replayed`** | **L4.** Freeze a pre-promotion relevance block into `thread_refs`, promote the record, then assemble a payload and assert the body is absent from the `system` message (`thread_service.py:2084-2106`) **while the `thread_refs` row still exists** -- receipts immutable, replays fenced |
| `test_the_promoted_body_is_absent_from_the_fts_corpus` | `SELECT count(*) FROM notes_memory_fts WHERE source_id=?` is 0 immediately after the promotion transaction commits -- construction, not filtering |
| `test_a_full_rebuild_cannot_re_admit_a_promoted_record` | run `rebuild_memory_index` (`db/memory.py:126`); the count stays 0 |
| `test_appending_into_an_existing_note_removes_it_from_the_corpus` | the append mode's `DELETE`, atomic with the promotion |
| `test_the_context_picker_still_finds_a_promoted_note_by_title` | `list_context` (`refinement_context_service.py:635-646`) returns it -- by-reference discovery survives, so the cost is bounded to relevance |
| `test_memory_search_does_not_return_a_promoted_record` (**`CONTRACTS.md:67` "search"**) | `MemoryRepository.search` over the `note` kind, and the `memory.search` MCP dispatch |
| `test_desk_snapshot_and_sync_pull_still_carry_the_body` (**`CONTRACTS.md:67` "export"**) | asserts the KNOWN, DECLARED egress rather than a false negative -- `desk.snapshot` (`mcp/tools.py:754-755`) and `SyncService.pull` (`sync_service.py:1117-1119`) DO carry it. The test exists so the boundary's true shape is in the record, not to claim it is closed |
| `test_a_frozen_thread_ref_never_carries_a_promoted_body` (**"cached projections"**) | drives `thread_service.py:380-408` and asserts `thread_refs.frozen_json` is clean -- the projection the first draft never checked |
| `test_the_people_section_refuses_promotion_and_a_person_ref_refuses_itself` | F1 + F4, the latter inherited from `relationships.py:31-32` |
| `test_a_sensitive_or_draft_part_cannot_source_a_promotion` | F2, run inside the promotion transaction |
| `test_promotion_into_the_default_or_everyday_context_is_refused` | F3, **append mode only** -- the test is written for the mode where it can fire |
| **`test_revoking_a_source_blocks_re_promotion_and_names_the_gap`** | the suppression refuses re-promotion of the same `(thread, fact, target)`; dependents read `forbidden` |
| **`test_a_note_save_after_a_revocation_leaves_forbidden_intact`** | **P0-2 directly**: revoke, then save the Note, then assert the dependent still reads `forbidden`. Without the lattice this test fails |
| **`test_revoking_one_of_several_promotions_does_not_poison_the_record`** | **P0-3**: two promotions into one Note; revoke one; dependents read `stale`, not `forbidden`; revoke the second; now `forbidden` |
| `test_deleting_the_source_message_leaves_the_promotion_naming_the_gap` | the fact is pruned (`:67-80`); the promotion survives as `source_unavailable` |
| `test_re_typing_a_revoked_quote_does_not_resurrect_the_promotion` | forget-vs-suppress |
| `test_promotion_records_locator_and_never_copies_the_quote` | asserts **no column of the row contains the quote text** (a substring check over every value) |
| `test_only_a_stated_fact_may_be_promoted_and_the_body_is_his_words` | `basis="inferred"` refuses; the Note body equals the quote verbatim |
| `test_target_kind_is_derived_from_the_ref_not_the_caller` | **C10**: `{target_kind: "note", target_ref: "artifact:a1"}` refuses `promotion_target_unsupported`; it does not read the `notes` table |
| **`test_two_promotions_of_one_fact_mint_one_note`** | **P0-4**: two distinct `command_id`s, one Note, an `updated_at` touch |
| `test_promotion_into_a_moved_note_refuses_on_the_expected_revision` | `promotion_target_conflict` |
| `test_promotion_replays_and_a_changed_payload_conflicts` | replay (`:133-137`) |

### Index tests (AC2, AC3) -- these run second

| Test | What it demonstrates |
|---|---|
| `test_two_thoughts_share_one_promoted_note_and_neither_owns_a_copy` | attach to two Thoughts, edit once, **both** `stale`; refresh one, the other stays |
| `test_thread_grounding_is_a_copy_and_this_design_does_not_change_it` | the declared narrowing PROVED, not asserted in prose |
| `test_correcting_the_note_marks_every_dependent_without_opening_it` | the reverse push -- read `context_dependents` without loading either Thought |
| **`test_the_content_hash_excludes_the_timestamp`** | **P0-1**: re-save with byte-identical content and a new `last_modified`; `target_content_sha256` is unchanged and the promotion reads `current`, **not `corrected`** |
| `test_an_unchanged_last_modified_resave_diverges_index_from_pull` | the **real** arbitration case: `upsert` with an explicit unchanged `last_modified` (`primitives.py:123`, `:141`) UPDATEs `notes`, fires the trigger, moves neither hash. Replaces the first draft's wrong "no-op save" example |
| `test_rebinding_clears_stale_but_never_clears_forbidden` | the lattice from the other side |
| `test_a_detach_removes_the_row_and_a_birth_creates_it` | all four verbs through the one reconcile point |
| `test_concurrent_edit_and_attach_leave_one_consistent_index` | two `BEGIN IMMEDIATE` writers |
| `test_promotion_writes_no_dependent_row` | the failure window that cannot exist |
| `test_promotion_and_its_dependents_survive_restart` | reopen |

### Migration

`tests/unit/test_db.py:1731` (snapshot regenerated with the normalizer
at `:1740-1750`, never by hand) must cover the three tables, three
indexes, **two new triggers, and the two REVISED trigger bodies**; plus
the positional-INSERT fence test. Two further tests are owed:

- `test_the_reconciler_refreshes_the_two_revised_note_triggers` -- open
  a database carrying the OLD trigger bodies, run `reconcile_schema`,
  assert both were replaced (`reconcile.py:549-578`, extended).
- **`test_a_reconciled_older_database_can_still_write_a_note`** -- build
  from an older `SCHEMA_SQL`, run `reconcile_schema`, **then insert a
  note and assert the write succeeds.** This is the assertion that
  proves the ordering, and it is the only thing standing between the
  revised trigger and a desk that cannot save a note (cannot-promise
  #6, now observed rather than assumed).

### Commands

```sh
uv run python docs/internal/architect-assistant/proof/run_tests.py -q --tb=short \
  tests/unit/test_phase200_working_context.py \
  tests/integration/test_phase200_working_context.py \
  tests/unit/test_interview_service.py \
  tests/unit/test_refinement_context_service.py

HOME=$(mktemp -d) uv run pytest -q tests/unit/test_db.py -k canonical_snapshot
```

### What is NOT proved here (counsel C12)

ACCEPTANCE.md **P200-A08** is owned by stories 10 and 20 at level
*Tests, browser*. This story delivers the Tests half **at Thought
scope**; the **Thread limb of P200-A08 is declared undelivered** (D2.8,
and "cannot promise" #5), and the **browser half does not ship at all**
under ruling C6. The first draft said "the Tests half in full", which
contradicted its own cannot-promise #5. Corrected.

---

## Sizes

### One story, ordered (ruling C1, upheld)

The design proposed a split; the ruling refused it on the phase's own
terms -- P200-A08 is one behaviour and neither half demonstrates it
alone. Counsel argued the split case hard, verified the seam is
genuinely clean (different files, different owners, **different
transactions** -- promotion writes no index row), and reported that the
one-story ruling nevertheless survives. **The ordering argument is
adopted in full as the lane order and, per the ruling, as an evidence
requirement**: the evidence file carries the boundary tests' output
before the index tests', so the record shows the fence landed first.

**Honest size: L.** The bounce added rather than removed: F0 is a new
mechanism touching a shipped corpus, two shipped triggers and the
reconciler.

### What this design commits the downstream stories to

| Story | What it inherits |
|---|---|
| **11** preparation | a kept brief registers as `consumer_kind='brief'` **at its own reconcile point** (C9), doing the same scoped delete-then-insert |
| **13** continuity | `Carry into brief` carries a **ref**; the ratified design's hunt 10 is answered by the index |
| **17** recipes | the pre-dispatch fence -- **and the choice D2.3 names**: whether it refuses on `forbidden`/`unavailable` only, or on all three |
| **20** revisit | story 20 AC2 becomes a proof rather than a build; the browser half of P200-A08 lands here |

### Superseded, not deleted (counsel C15; `feedback_never_delete_park_instead`)

The first draft recommended moving `TaskResume` (S5), the focus half of
return-to-task, `DRAFT NOT SAVED` and the two `ThreadComposer` residues
to story 15. **That recommendation is superseded**: the story file has
already moved them to **HS-200-41**, and a sibling lane has landed
`project_ask_tasks` for it (`holdspeak/db/schema.py:4134-4157`). The
reasoning was right, the destination was wrong, and the record keeps
both.

---

## WHAT THIS DESIGN CANNOT PROMISE

1. **A promoted record still leaves the machine through whole-table
   egress**, which is not relevance and not this story's to close. The
   map, each opened: `desk.snapshot` (`mcp/tools.py:754-755` →
   `services/desk_service.py:37-47`; `NoteRecord.to_dict`
   `db/models/__init__.py:568`, body at `:572`), `desk.list`/`desk.get`
   (`mcp/tools.py:39-62`), all three in `CHAT_PALETTE`
   (`thread_tools.py:300`), and `GET /api/sync/pull` up to 500 full
   bodies (`sync_service.py:1117-1119`, route `web/routes/sync.py:38-42`).
   A model in an ordinary Thread can call the first three itself. That
   exposure predates this story and covers every note the owner has ever
   written; F0 does not reduce it, and this design does not pretend to.
2. **`revoke_promotion` revokes the claim that a source backs the
   record, not the record.** `CONTRACTS.md:63`'s "evaluated at each
   disclosure" is met only for consumers that read `context_dependents`
   -- not for ref hydration, `desk.*`, or export. **And revocation closes nothing on the
   relevance surface either** -- F0 fires at *promotion*, keyed on the
   existence of a promotion row, so that surface was already closed.
   Revocation changes the dependent marking and suppresses
   re-promotion; it does not reach a single disclosure surface that
   promotion had left open.
3. **AC4's gap is named to a caller, not to the owner.** Ruling C6
   ships no face, so on the day this lands a revoked promotion names its
   gap in a service response and a table and nowhere he will look.
   Lawful and ledgered; not delivered to his eye.
4. **The call-site census (D3) was swept, not merely inherited** -- nine
   sites, four unconditional -- and it is still a floor. What could not
   be verified is whether every MCP tool that ultimately reaches
   `AskService.ask`, `RecipeService.run/chat` or
   `ThreadService.start_turn` does so with empty grounding; the sweep
   traced wrappers one level and did not enumerate the full tool
   surface. **This is exactly why the fence is at the corpus and the hit
   assembly rather than at the call sites**: a new caller inherits the
   boundary, and a missed caller does not breach it. The residual risk
   is a fourth *retrieval route* into a `MemoryHit` or a second
   unbounded-body producer, not a tenth caller.
5. **AC2 at Thread scope is not delivered and cannot be, cheaply.**
   Converting `thread_refs.frozen_json` (`schema.py:3614-3622`,
   `thread_service.py:397-408`) from a copy to a live reference is a
   rewrite of the Thread prompt path. Recorded against `ACCEPTANCE.md:33`
   (D2.8).
6. **The forward reference fails HARDER than the first draft said, and
   I ran it.** The first draft guessed that a trigger body naming a
   not-yet-created table would be "unresolved ... so this should be
   safe". Observed in a throwaway SQLite: the `CREATE TRIGGER`
   **succeeds** naming the missing table, and then the first
   `INSERT INTO notes` raises `OperationalError: no such table:
   main.context_promotions`. **A database that ends up with the revised
   trigger and without the table cannot save a note at all** -- the desk
   is bricked for note writes, not merely degraded. The shipped ordering
   is safe: there is no window inside one `executescript(SCHEMA_SQL)`,
   and `reconcile_schema` calls the trigger refresh at
   `reconcile.py:644`, *after* `executescript`. That safety is now
   pinned by a migration test (D5) rather than by this paragraph.
7. **The sync fence has not been run two-device.** The spec, the
   apply order (`sync_service.py:1417-1419`) and the merge write
   (`:660-675`) were read, not exercised. Counsel did not run a
   two-device sync either, and neither of us audited whether any
   **other** device-local fence in this repo has the same shape --
   which is the more worrying question, and it is not this story's to
   answer.
8. **L4 fences the replay, not the receipt.** A `thread_refs` row
   frozen before a promotion keeps the body forever, by design. Anyone
   reading that table directly -- a future debug surface, an export,
   an audit tool -- sees it. That is what a receipt is, and it is why
   `CONTRACTS.md:66` declines to promise erasure; it is stated here so
   the word "fenced" is not read as "erased".
9. **Both new triggers' write cost, and the DDL seed's, are
   unmeasured** at any scale.
10. **`_persist_manifest`'s interaction with the `unchanged` no-op
   branch** (computed `:730-734`, gating `:736-743`) needs code: a true
   no-op skips the reconcile, so a row bound at an older manifest hash
   can survive -- harmless to the ref-keyed push, but it makes
   `bound_manifest_sha256` stale.
11. **`stale_reason` reuses C4's words but is not wired to the C4
   aggregate.** Whether context gaps join the arrival's coverage section
   is story 15's decision.
12. **No product test was run and no face was opened.** Line numbers
    were verified by opening the files; behaviour of code that does not
    exist was not. **Three mechanisms have now been observed rather
    than reasoned about** -- L1's write ordering and the `forbidden`
    lattice (run by counsel in scratch SQLite) and the forward-reference
    failure (run by me, D5 and item 6) -- but each was the *mechanism*
    in isolation on a scratch schema, never the product.

---

## Addendum -- the bounce and the re-take (2026-09-07)

Counsel's read: `assets/counsel-on-design-200-10.md` -- **VERDICT:
BOUNCE**, seven P0s, nine conditions. The design gate did its work: no
code was written against the reversed ruling.

### The reversal

| | |
|---|---|
| **What the first draft ruled** | Containment. A promotion never attaches, therefore a promoted Note is "exactly as reachable as one he typed by hand" -- so limbs 5 and 6 of the leak path are deleted outright, and `notes.sensitive` is unnecessary |
| **Why it was wrong** | `grounding.py:188-197` fires a global relevance search **if and only if `not has_explicit_sources`**. Not attaching is the **trigger condition** for automatic retrieval, not an escape from it. The sentence passes F1, F2 and F3 and is pulled into the next matching prompt |
| **The tell the first draft missed** | It walked every **guard** -- every limb keying on `person:`, `people.*` or `sensitive` -- and never walked the **hydrators**. It opened `grounding.py` only at `:313-321` and `:394`, to prove a negative, and never asked who calls `hydrate_refs_detailed` and with what |
| **The proof that would have lied** | The AC5 leak-path test asserted over `_resolve_manifest`'s `material` -- the attachment envelope. The sentence arrives through `ask_service.py:526-527`. **The test would have gone green while the boundary was open**, which is the lesson worth keeping: a test that cannot fail on the real path is not proof |
| **What replaces it (C2′)** | Reachable by reference, never by relevance -- enforced by **removing the bytes from the relevance corpus**, not by a column that defaults to zero |

### Every carried item, and where it landed

| Item | Where it moved | Status |
|---|---|---|
| **P0-0** containment does not contain | D1 laws 1-3; D2.1 AC5 row; D2.4 rewritten whole; D3 new retrieval seam + the swept call-site census; D4 hunts 1 and 10; D5 boundary tests | **Closed for relevance, at four choke points (re-placed after P0-A/B/C).** Narrowed overall -- whole-table egress remains (cannot-promise #1) |
| **P0-1** the hash contains the counter | D1 law 6; D2.2 new recipe over `{ref,title,body_markdown,tags}`; D2.3 arbitration example replaced; D4 hunt 2; two D5 tests | **Closed** |
| **P0-2** the trigger downgrades a revocation | D1 law 11; D2.3 lattice + both trigger bodies; D2.7; D5 `..._leaves_forbidden_intact` | **Closed** |
| **P0-3** revocation across several promotions | D2.6 rule; D2.7 window; D5 `..._does_not_poison_the_record` | **Closed** |
| **P0-4** a double-click mints two Notes | D1 law 9; D2.2 deterministic mint; D2.7 window; D5 `..._mint_one_note`. It also **composes with F0**: the deterministic ref is what lets the promotion row precede the Note, so the FTS trigger never indexes it | **Closed** |
| **P0-5** no search / export / cached-projection tests | D5 boundary tests (three added); cannot-promise #1 carries the egress map | **Narrowed.** The tests land; the egress itself predates this story and is not fixed |
| **P0-6** revocation evaluated at promotion time only | D2.6 "What `revoke` revokes"; cannot-promise #2 | **Narrowed, deliberately.** Stated in the owner's own word rather than fixed -- the Note is his |
| **C7** `_reduce` has no `conn` | D2.7; D3 promotion seam | applied |
| **C8** F3 unreachable in the common mode | D2.4 fence table, F3 row reworded; D4 hunt 4 | applied |
| **C9** "one write point" holds only for `'thought'` | D2.3 restated as one reconcile point **per consumer kind**; Sizes | applied |
| **C10** `target_kind` must be derived | D1 law 8; D2.2; D5 test | applied |
| **C11** two narrowings unrecorded where gated | **new D2.8** | applied |
| **C12** "Tests half in full" contradicts #5 | D5 closing paragraph | applied |
| **C13** MCP conflict | ruling C6 amended; D1 law and D2.6 unchanged -- the design was right | applied |
| **C14** strike the face plan | D3 face seam struck; D1 law; D2.6 | applied |
| **C15** factual corrections | **20** kinds not 22 (verified programmatically); `insert_evidence_link` has **zero** references anywhere including tests; Sizes marked superseded (destination is **HS-200-41**, not story 15); cannot-promise #4 **closed** at `schema.py:4115-4118`; the no-`CHECK` rationale restated as a reason for `consumer_kind`, not house law | applied |

### What the re-take's own sweep added, beyond the bounce

Counsel offered its retrieval map as "a floor, not a ceiling" and asked
the re-take to grep the call signature rather than trust the list. That
sweep found something neither the first draft nor counsel had:

**There are TWO retrieval routes for a note, and only one goes through
the FTS corpus.** `MemoryRepository._load_related_row`'s `note` branch
(`db/memory.py:1085-1094`) reads `FROM notes WHERE id=? AND deleted=0`
**directly** as part of the one-hop relationship expansion
(`_expand_related_rows`, `:739`), and those rows are woven into the
same hit list (`:286-290`) and become `MemoryHit`s (`:293-296`). So a
promoted record can be retrieved **on words it does not contain**, and
a design that fenced only the corpus would have shipped with the
boundary open in the same shape the bounce found -- one layer closed,
one route still live, and a test suite green over the closed one.

That is why D2.4 is now **three** layers rather than one, why L2 sits
at the hit assembly where both routes converge, and why the D5 table
carries a test whose whole purpose is to fail if L2 is removed while L1
stands. The pattern behind both misses is the same one counsel named:
walking the guards, or one route, and calling it the perimeter.

The sweep also fixed the caller count. Nine sites reach the pass
(**four unconditionally**, not two), it confirmed `_note_rows` is the
corpus's only reader outside `db/memory.py`, and it surfaced
`coder_steering_support.py:103-110` → `coder_steering_routes.py:424-433`
-- relevance-driven egress into a third-party coding agent's terminal
pane (D4 hunt 10).

### Counsel's re-read: RATIFY WITH CONDITIONS (2026-09-07)

`assets/counsel-on-design-200-10-reread.md`. Three P0s, all **placement
errors inside a shape counsel agrees is right**; none re-opens C2′.
Counsel settled two of this design's own "asserted, not observed" items
by running them in scratch SQLite; I ran the third myself.

| Item | The finding | Where it moved | Paid? |
|---|---|---|---|
| **P0-A** L3 sat inside `_hydrate_members`, which is **shared** -- `_hydrate_container` (`grounding.py:526-528`) reaches it from the explicit `knowledge:` (`:411-430`) and `zone:` (`:431-449`) branches, so the belt silently dropped a promoted Note out of any attached container, with no unknown-ref signal (`:502-505`) | Moved to the two relevance **call sites** (`:209`, `:485`); D2.4 L3 rewritten and the false reason retracted in its own words; D3 seam row corrected; D5 gains a container regression test | **fully paid** |
| **P0-B** L2's predicate was three lines too late: `lexical_total` (`:262`), `total` (`:292`) and the page slice (`:293`) all run before the single `MemoryHit` site (`:295`), so filtering there over-counts, short-pages, and makes `grounding.py:215-217` book withheld sources as overflow | Rewritten to union promoted refs into `excluded` after `db/memory.py:192` -- the shipped plumbing, applied at `:247-252` before the sort, threaded at `:271`, honoured at `:775`; D5 gains a totals test | **fully paid** |
| **P0-C** the fence is device-local; `note` syncs with `body_markdown` merged (`sync_service.py:35`, `:120`, `:660-675`) and `context_promotions` has no spec | New D2.4 section: a `SyncKindSpec` placed **before** `note` (apply order = registry order, `:1417-1419`), a custom `merger` rather than `_MERGEABLE`, a post-apply corpus sweep, and the disagreement rule -- **`revoked` wins over `active` regardless of timestamp**, a monotone join, never LWW. D4 hunt 12; D5 two tests | **paid in design; unrun** -- see cannot-promise #7 |
| **C1** the picker searches `title` only, and the title was the model's paraphrase | D2.2 now **mints the title from the quote**; the cost bullet and D4 hunt 6 rewritten to say the bound holds *because* of that change | **fully paid** |
| **C2** append-mode residue already frozen into `thread_refs` replays on **every** turn (`thread_service.py:2069-2106`) | New **L4**: the replay is fenced, the `thread_refs` row is not -- receipts are immutable, replays are disclosures. Cannot-promise #8; D5 test | **fully paid** |
| **C3** the honesty slip: revocation credited with closing a surface promotion had already closed | Reworded in D2.6 and again in cannot-promise #2 | **fully paid** |
| **C4** the forward reference fails harder than stated -- **I ran it**: `CREATE TRIGGER` succeeds naming a missing table, then the first `INSERT INTO notes` raises `no such table` and the desk cannot save a note | Cannot-promise #6 restated with the observed failure; D5 gains a migration test whose assertion is that a note write **succeeds** after reconcile | **fully paid** |
| **C5** the coder-steering framing survives on the ledger law; the missing half is a **face** law -- `buildGrounding` returns `null` exactly when nothing was picked (`web/src/desk/grounding.ts:112-113`), so no egress chip is drawn at composition time (UX-CANON A.9) | D4 hunt 10 carries the specific pre-delivery obligation into the ledger entry | **paid as a ledger entry**, not fixed here |
| **nit** `_refresh_tool_turn_lifecycle_guards` is named for tool-turn guards | D4 hunt 13: the function is renamed and its docstring rewritten in the same change | **fully paid** |

**The shape of P0-A is worth recording, because it is the same mistake
twice.** The bounce happened because the first draft read one caller of
the note branch and called it the perimeter. P0-A happened because the
re-take read two callers of `_hydrate_members` and called it the
relevance side. Both times the fix was to sweep. D5's container test
exists specifically so the third occurrence fails loudly instead of
silently.

### What counsel confirmed, and this re-take keeps unchanged

**From the re-read.** There is **no third relevance route**: counsel
swept the eight `include_memory=True` call sites independently (all
appear in D3's census, which counts nine because two
`coder_steering_support.py` entry points share `coder_service.py:148`),
confirmed `MemoryHit(` has exactly one producer, confirmed
`notes_memory_fts` is referenced only in `db/memory.py`, `db/schema.py`
and one test, and enumerated every direct `FROM notes` reader outside
the repositories -- none relevance-driven. **Two routes, as this design
says.** It also ran L1's write ordering (promotion row first → the body
never reaches the corpus, not transiently; a control note with identical
words IS indexed) and the `forbidden` lattice (survives a subsequent
note write; a fresh dependent goes to `stale`). Both behave as designed.
And it verified the reconcile mechanism end to end, including that
`_refresh_tool_turn_lifecycle_guards` is called unconditionally at
`reconcile.py:644` and feeds `shape_changed` at `:653`. One scoping
point it credits and this design keeps: L2 closes any third route **into
a hit**, and does not close a route that reads `notes` without producing
one -- `ResourcefulService._loose_idea` is exactly that, named in the
costs and correctly not claimed as closed.

**From the first read.** The database census reproduces row for row, including the 9 current
pairs and the 0 working Thoughts. `_persist_manifest` has exactly two
call sites. The People **store** walk is accurate limb by limb,
including the correction to the brief's wrong `grounding.py` path, and
the judgment to prove that boundary by test rather than re-guard it was
right. F2 is free -- `_prune_unavailable_facts` already runs inside the
open transaction (`interview_service.py:143`), which the first draft
under-claimed. F3 has no TOCTOU window under `BEGIN IMMEDIATE`,
provided the fences read on `conn`. The suggestion picker is not an
auto-attach (`refinement_context_service.py:588-625`). And the
rejection of a disclosure class on `feedback_ledger_not_gate_rule.md`
grounds stands.

### One correction to the ruling's wording

C2′ says the proof must run "through `grounding.build`". **There is no
`grounding.build`.** The module's public hydrators are
`hydrate_refs_detailed` (`grounding.py:93`), `hydrate_refs` (`:236`),
`hydrate_grounding_blocks_detailed` (`:538`) and
`hydrate_grounding_blocks` (exported at `:751-770`). The proof runs
through the first and third on the unattached path, which is what the
ruling means; recorded so the test names match the tree.
