# Counsel on the settled design — HS-200-10 (scoped working context)

**Target:** `assets/settled-design-working-context.md` (1072 lines, settled
2026-09-07 on `feat/phase-200-working-context`).
**Counsel:** hunted, not admired. Every `file:line` below was opened on this
branch; every database number was re-measured read-only against
`~/.local/share/holdspeak/holdspeak.db` with `?immutable=1`.

---

## VERDICT — **BOUNCE**

One P0 forces it, and it is the one the brief ranked first.

**The design's primary People guard rests on a false premise.** D2.4 and ruling
C2 both hold that because a promotion never attaches, "limbs 5 and 6 of the leak
path" are deleted outright. The opposite is true: **not attaching is the trigger
condition for an automatic, relevance-driven retrieval pass that injects
unattached note bodies into model prompts.** `holdspeak/grounding.py:190-197`
runs a global `memory.search` **if and only if** `not has_explicit_sources` —
i.e. precisely when the owner attached nothing. Nine model-bearing callers opt
into it, including every Thread message the owner types and every Thought
refinement dispatch. I opened and confirmed each load-bearing limb myself
(P0-0 below).

The consequence is not a documentation gap. The design's most valuable planned
test — the AC5 leak-path re-enactment — asserts over `_resolve_manifest`'s
`material`, which is the *attachment* envelope. The sentence arrives through a
different envelope (`ask_service.py:514-527`), so **that test would pass green
while the leak is live.** AC5 is this product's hard boundary, and the phase's
critical-defect list names "unauthorized disclosure ... outside the applicable
scope."

This is not counsel designing around ruling C2. The ruling is refused on its
own stated premise, with the evidence the ruling would have been taken on had
it been available: `holdspeak/grounding.py:184-217` was not walked when
containment was chosen, and containment cannot be weighed against
`notes.sensitive` until it is.

**Everything else in this document survives the bounce and should be carried
into the re-take.** This is the best-evidenced wire design the phase has
produced. I re-measured its entire database census and it is **exact** (D2.3
reproduces row-for-row, including the 9 current pairs and the 0 working
Thoughts). Its one grep-checkable structural claim — `_persist_manifest` has
**exactly two call sites** — holds
(`holdspeak/services/refinement_context_service.py:549`, `:743`, def `:990`).
Its People *store* walk is accurate limb by limb, including the correction it
makes to the brief's wrong citation. Six further P0s and nine conditions are
below; all are fixable in the document and none of them, alone, would have
bounced it.

---

## THE P0 THAT FORCES THE BOUNCE

### P0-0 — Containment does not contain. Not attaching is the condition that triggers automatic retrieval.

**Where:** design D2.4 in full ("The decision: containment, not
classification"); D1 law 1; D2.4's fence table row F3 ("the entire leak path");
D4 hunt 3; D5's AC5 test row; and story ruling C2.

**The mechanism, opened line by line on this branch:**

1. `holdspeak/grounding.py:190-197` — inside `hydrate_refs_detailed`, the
   global memory pass runs when `include_memory` **and** `query` is non-empty
   **and** `not has_project_ref` **and** `not has_explicit_sources`, where
   `has_explicit_sources = bool(meeting_ids or artifact_ids or qualified_refs)`
   (`:188`). It searches memory (`:203-207`), takes the top
   `GROUNDING_MAX_REFS = 16` hits (`:208`, cap at `:24`) and hydrates them
   (`:209-211`), stamping `selection = "ecosystem_relevance"` (`:214`).
2. `holdspeak/grounding.py:313-321` — the `note` branch those hits land in
   returns `note.body_markdown` **whole**. The meeting and thread branches
   truncate at `GROUNDING_TRANSCRIPT_CAP`; the note branch applies no cap and
   no sensitivity check of any kind.
3. `holdspeak/db/memory.py:139-142` and `holdspeak/db/schema.py:1214-1226` —
   every undeleted note is in that corpus, written by trigger at INSERT time.
   A promoted Note is searchable inside the promotion transaction.
4. `holdspeak/services/thread_service.py:380-390` — **every Thread message with
   non-empty text** calls `hydrate_refs_detailed(..., query=text,
   include_memory=True)`. When the owner simply types (no `grounding_refs`),
   `has_explicit_sources` is False and the pass fires on his sentence.
5. `holdspeak/services/thread_service.py:397-408` — each retrieved block's
   **full text** is then frozen into `thread_refs.frozen_json` with
   `"sensitive": False` (`:407`), and replayed to the model as a `system`
   message at `:2095-2107`.
6. `holdspeak/services/ask_service.py:514-527` — `_frozen_grounding_with_memory`
   calls the same hydrator with **empty ref lists, unconditionally**, so the
   branch fires on every Thought refinement regardless of what is attached, and
   appends the result to the frozen envelope at `:527`.

So the D2.4 sentence — a relationship sentence typed in the `goals` section,
`sensitive=0` because nothing classifies free text — passes F1 (section is
`goals`), passes F2 (`sensitive=0`), passes F3 (a newly minted note ref cannot
be in default context), is promoted, and is thereafter pulled **by relevance**
into the next Thread message or Thought dispatch whose words match it. No
attachment. No default context. No further owner action beyond typing about the
subject.

**Why the planned proof would not catch it.** D5's
`test_a_relationship_sentence_in_the_goals_section_never_reaches_a_new_thread_prompt`
asserts that `_resolve_manifest`'s `material` does not contain the sentence.
`_resolve_manifest` is the attachment resolver. The sentence enters at
`ask_service.py:527` as `envelope + material` from a *different* hydrator. The
test passes; the boundary does not hold.

**What the re-take has to answer.** Not "which of Candidate A or Candidate B",
but the question that was never put: **containment was scored against
`notes.sensitive` on the assumption that a promoted Note reaches a prompt only
by attachment. It reaches a prompt by retrieval.** The nine readers D2.4 lists
as the cost of `notes.sensitive` are the same readers this path runs through,
so the cost comparison inverts. Three shapes worth weighing, in the order I
would weigh them:

- **Exclude promoted Notes from the automatic pass only.** One predicate, at
  one place (`grounding.py:203-207` or the `_note_rows` query), keyed on the
  existence of an active `context_promotions` row — no `notes` column, no
  fail-open default, and it leaves the owner's own explicit attach untouched.
  This preserves C2's containment *and* makes it mean what it says.
- **Reconsider `notes.sensitive`** with the true reader count now that
  retrieval, not attachment, is the dominant path.
- **Refuse the promotion of free text outright** and promote only into a
  target the owner names, accepting the friction.

I have no ruling to give here; I have the evidence the ruling needs.

---

## THE OTHER P0s AND CONDITIONS

All of these stand independently of P0-0 and should be carried into the
re-take.

### P0-1 — The "content hash" is not a content hash. It contains the counter the design just rejected.

**Where:** design D1 law 4; D2.2's `note` row ("sha256 over canonical bytes
`{ref, title, body_markdown, tags, last_modified}` — the recipe already in
`_leaf`"); D2.3 arbitration table; D4 hunt 7; D5 test row
`test_the_index_is_conservative_and_the_pull_is_exact`.

**The fact.** `_leaf`'s digest is computed at
`holdspeak/services/refinement_context_service.py:975-979`:

```python
content_hash = _sha(canonical_json({"ref": ref, "title": str(note["title"]),
    "body_markdown": str(note["body_markdown"]), "tags": tags,
    "last_modified": str(note["last_modified"]), "deleted": False}))
```

`last_modified` is **inside the digest** (and so is `deleted`, which the
design's stated recipe omits). The visible digest has the same disease:
`refinement_context_service.py:952-953` hashes `source_last_modified` into
`visible_sha256`.

And `NoteRepository._upsert_in_transaction`
(`holdspeak/db/primitives.py:120-141`) writes
`last_modified=excluded.last_modified` **unconditionally** on every
`ON CONFLICT` — with `last_modified or now`. There is no "did anything change"
guard at the primitive.

**Three consequences, each of which lands on a design claim:**

1. The design's headline P1 argument ("the counter cannot be the comparator" —
   D2.2 reason 1) is self-defeating if it uses this recipe. The comparator it
   adopts is `f(content, counter)`; it changes whenever the counter changes.
   A promotion whose target Note is re-saved with byte-identical content reads
   **`corrected`** and tells the owner his constraint moved when it did not.
   Under Article VI and ACCEPTANCE's "unsupported prose presented as checked
   fact", a face that says `CORRECTED` about an unchanged sentence is the
   defect this whole story exists to avoid.
2. D2.3's arbitration example is **wrong**: "If the owner saves a Note without
   changing a byte, `context_dependents` says `stale` and
   `project_in_transaction` says `current`." It does not. An ordinary re-save
   bumps `last_modified`, so the pull says `stale` too. The two records agree.
3. The planned test named for that ruling (`test_the_index_is_conservative_and_the_pull_is_exact`)
   **cannot pass as described**.

**The change.** In D2.2's `note` row, define
`target_content_sha256` over `{ref, title, body_markdown, tags}` **only** —
a new, true content recipe — and say plainly that it is NOT `_leaf`'s, with
this reason. Then either (a) delete the "conservative index vs exact pull"
arbitration from D2.3 and D4 hunt 7, or (b) keep it and give it the *real*
divergence case, which does exist: `NoteRepository.upsert` accepts an explicit
`last_modified` (`primitives.py:123`) and writes the row unconditionally, so a
re-save carrying the **same** `last_modified` UPDATEs `notes` (firing the
trigger) without moving either hash. The shipped test at
`tests/unit/test_refinement_context_service.py:224-229` already uses exactly
that API. Name that mechanism, not "a no-op save".

---

### P0-2 — The designed trigger DOWNGRADES a revocation to a mere staleness. AC4 leaks through its own mechanism.

**Where:** D2.3, `context_dependents_note_au`.

```sql
SET stale_reason = CASE WHEN NEW.deleted = 1 THEN 'unavailable' ELSE 'stale' END
```

`revoke_promotion` (D2.6) sets `stale_reason='forbidden'` on every dependent of
the target. The very next `UPDATE` on that Note — and
`refinement_thought_service` writes a working Note on every accepted revision
(`:142`, `:552`, `:1062`, `:1158`) — rewrites `forbidden` to `stale`
unconditionally. A consumer that fences on `forbidden` (D2.3 effect 2, the hook
stories 17 and 20 are promised) then sees an ordinary refreshable staleness and
dispatches.

That is "blocks new unauthorized disclosure" defeated by the design's own push,
and it lands on ACCEPTANCE's critical-defect line "unauthorized disclosure or
execution outside the applicable scope."

**The change.** The trigger must never downgrade:

```sql
SET stale_reason = CASE WHEN stale_reason = 'forbidden' THEN 'forbidden'
                        WHEN NEW.deleted = 1 THEN 'unavailable'
                        ELSE 'stale' END
```

and D2.3 must state the lattice explicitly (`forbidden` is terminal until an
explicit re-promotion clears it; only a rebind through `_persist_manifest`
clears `stale`). Add a test: revoke, then save the Note, then assert the
dependent still reads `forbidden`.

---

### P0-3 — Revocation is not defined when one record carries several promotions.

**Where:** D2.5 (`UNIQUE (thread_id, fact_id, target_ref)`) against D2.6
(`revoke_promotion` → "`stale_reason='forbidden'` on every dependent of the
target").

The UNIQUE key deliberately permits **N promotions into one `target_ref`** (the
"Existing Note / append" mode is the design's own second target mode). Revoking
one of them marks every consumer of that Note `forbidden` — including consumers
that depend on it for the owner's own hand-typed body and for the other,
un-revoked quotes. And with P0-2 fixed, `forbidden` is terminal, so one
revocation permanently poisons a record that is still legitimate.

**The change.** D2.6 must say what a revoke does when other active promotions
remain on the same `target_ref`. The honest rule: mark dependents `forbidden`
**only when no `disclosure_state='active'` promotion into that `target_ref`
survives**; otherwise mark `stale` and let the response name the removed
quotation. Add it to the failure-window table and to the AC4 test row.

---

### P0-4 — A double-click mints two Notes. The replay guard does not cover the new-Note mode.

**Where:** D2.2 "New Note (the common case): `target_ref` omitted, **the service
mints the id**"; D2.7 idempotency.

The replay guard is keyed `(thread_id, command_id)`
(`holdspeak/services/interview_service.py:133-137`) and `command_id` is supplied
by the caller. Two clicks that mint two `command_id`s are two distinct commands.
In new-Note mode each mints its **own** `target_ref`, so
`UNIQUE (thread_id, fact_id, target_ref)` does not collide, and the desk gets
two Notes carrying the same sentence — "unexplained duplicate consequential
effects" from ACCEPTANCE's critical-defect list, and the exact thing AC2's
"without separate editable copies" forbids.

**The change.** D2.2 must specify the minted id is **deterministic** —
derived from `(thread_id, fact_id)`, the way the design itself notes
`project_observations` "carries a deterministic id" — so a second promotion of
the same fact collides on the UNIQUE and becomes the `updated_at` touch D2.7
already promises. Say it in D2.2, not only in D2.7.

---

### P0-5 — `CONTRACTS.md:67` requires tests over search and export. The design has neither, and both are live paths.

**Where:** `CONTRACTS.md:67` — "Tests cover future prompts, cached projections,
**search, export**, and result previews." Against D5's proof table: 18
deterministic tests, no search test, no export test, no cached-projection test.

The contract wrote that line because these paths exist, and they do:

- **Search.** `notes_memory_ai` (`holdspeak/db/schema.py:1214-1218`) indexes the
  promoted body at INSERT. `memory.search` is an MCP tool
  (`holdspeak/mcp/families/memory.py:11-29`, named at `:13`) returning title
  plus a 24-token body snippet (`holdspeak/db/memory.py:483-491`), and it sits
  in the model's own `CHAT_PALETTE` (`holdspeak/services/thread_tools.py:300-302`)
  classed `evidence_read` and **not** marked sensitive (`:139`) — where every
  `people.*` entry is (`:141-157`).
- **Whole-table egress.** `desk.snapshot` (`holdspeak/mcp/tools.py:754-755` →
  `holdspeak/services/desk_service.py:37-46`) returns every note via
  `to_dict()`, which carries `body_markdown`
  (`holdspeak/db/models/__init__.py:267`). `desk.list` and `desk.get`
  (`holdspeak/mcp/tools.py:39-62`) do the same. All three are in the same
  palette.
- **Export.** `SyncService.pull` (`holdspeak/services/sync_service.py:1117-1119`)
  emits up to 500 full note bodies, served at
  `holdspeak/web/routes/sync.py:37-42`.

**The change.** Add the three tests `CONTRACTS.md:67` names, and add the
egress map above to "WHAT THIS DESIGN CANNOT PROMISE" so the sentence "exactly
as reachable as one he typed by hand" is accompanied by what that reach *is*.

---

### P0-6 — `CONTRACTS.md:63` says revocation is evaluated **at each disclosure**. Here it is evaluated at promotion time only.

**Where:** D2.6 `revoke_promotion`; D2.7's state machine.

After a revoke: the suppression row blocks re-promotion, and dependents are
marked. The **Note is untouched** — deliberately, and I agree with the choice
("the Note is his now"). But `notes_memory_fts` still holds it, `memory.search`
still returns it, `grounding.py:313-321` still hydrates it, and no reader
consults `context_promotions.disclosure_state`. So at "each disclosure",
revocation is not evaluated at all except for consumers that read
`context_dependents`.

**The change.** State it in one line, in D2.6 and again in "cannot promise":
*`revoke_promotion` revokes the CLAIM THAT A SOURCE BACKS the record. It does
not revoke the record, and `CONTRACTS.md:63`'s "evaluated at each disclosure"
is met only for consumers that read `context_dependents` — not for memory
search, ref hydration, or export.* Without that line the design promises more
than it delivers on the one word ("revoke") the owner will read most literally.

---

### C7 — The `promote` branch cannot live where D3 puts it. `_reduce` has no connection.

`_reduce(self, thread_id, state, event, now)` —
`holdspeak/services/interview_service.py:154` — takes no `conn`. D3's wire table
names `:154-191` as "the reducer to extend" and D2.4 requires F2/F3 and the Note
write to run **inside** the open `BEGIN IMMEDIATE`. Worse, the precedent branch
`_fact` reads through a *second* connection while the write transaction is held
(`self._db.threads.get_message` at `:209`, `get_parts` at `:213`).

It is safe today only because `BEGIN IMMEDIATE` (`:126`) holds the write lock so
nothing can commit under it — but that is an accident the design does not state
and a future reader will copy the `_fact` shape and break it.

**The change.** D3 must name the signature change (`_reduce(..., conn)`) or
handle `promote` in `command()` beside the state upsert, and D2.7 must add one
sentence: *every fence reads on the transaction's own `conn`; the `_fact`
pattern at `:209`/`:213` is not the pattern to copy.*

### C8 — F3 is structurally unreachable in the common mode, so "stops the entire leak path" is overstated.

D2.4's fence table credits F3 with "**the entire leak path**". In the New Note
mode the service mints the target id, so a brand-new `note:` ref cannot already
be in `refinement_default_context_current.refs_json` or in the Everyday
`knowledge_memberships`. F3 can only ever fire in the append-into-existing-Note
mode. What actually closes limbs 5–6 is **containment** (the promotion never
attaches). Reword the F3 row to say so; the fence is still worth building for
the append mode, and the honesty matters because the walk will never see F3
fire.

### C9 — "One write point" holds only for `consumer_kind='thought'`.

D2.3 sells "written at ONE call site, verifiable by grep" as the integrity
guarantee, and ruling C5 adopts it. But `_persist_manifest` only ever writes
`'thought'` rows. Stories 11, 13, 17 and 20 add `brief`, `project_facet`,
`cadence_run`, `prepared_assignment` — each of which needs **its own** write
point, at which moment the stated invariant is false. Restate it as: *one
reconcile point per consumer kind, each doing the same scoped delete-then-insert
(`DELETE ... WHERE consumer_kind=? AND consumer_id=?`), and no other writer.*
Add it to "what this design commits the downstream stories to".

### C10 — `target_kind` must be derived, not accepted.

D2.5 gives `context_promotions.target_kind TEXT NOT NULL DEFAULT 'note'` and
D2.2 says the mechanism is "kind-dispatched and service-validated", but nowhere
says the kind comes from the ref. A caller can send
`{target_kind: "note", target_ref: "thought:t1"}`; `qualified_ref` accepts it
(`thought` is not in `RESOURCE_KINDS`, so that exact one raises — but
`workbench_item:`, `artifact:`, `project_item:` and 17 others do not), and the
`note` branch would then `SELECT ... FROM notes WHERE id=<the tail>`. One
sentence in D2.2: *`target_kind` is derived from `qualified_ref()`'s parsed
kind; a caller-supplied kind is ignored, and any kind but `note` raises
`promotion_target_unsupported`.*

### C11 — Two narrowings are ruled at story level but unrecorded where they are gated.

- `CONTRACTS.md:57` — "promoted from Interview into existing Notes, **Thoughts,
  or Project facets**." The design ships `note` only (ruling C3 accepts this).
  A story ruling does not amend a phase contract. Record the narrowing against
  C3, or the phase carries a contract it does not meet.
- `ACCEPTANCE.md:33` P200-A08 — "reuse it in **another Thread**". Ruling C7
  narrows AC2 to Thought scope, and the design's own "cannot promise" #5 says
  Thread scope is undeliverable. Same problem: A08 is a phase acceptance
  scenario, not a story AC.

Both are one-line edits with a ledger note. Left alone they become an
end-of-phase surprise at G1 sign-off.

### C12 — D5 contradicts "cannot promise" #5.

D5: "This story delivers the **Tests half in full**." Cannot-promise #5: AC2 at
Thread scope "is not delivered and cannot be, cheaply." P200-A08's Thread limb
is therefore not delivered. Change "in full" to "at Thought scope; the Thread
limb of P200-A08 is declared undelivered."

### C13 — The design's own MCP decision conflicts with ruling C6.

Story ruling C6 ends "this story ships the wire and **its MCP** and route
surface." Design D2.6: "**The MCP interview family gains NOTHING.**"

**The design is right and the ruling's wording should be corrected**, not the
design. The shipped asymmetry is real and I verified both halves: the browser
allowlist is `{section, remove_fact, disposition, status}`
(`holdspeak/web/routes/threads.py:87`) while the model's four tools are
`interview.get`, `.change_section`, `.record_fact`, `.suggest`
(`holdspeak/mcp/families/interview.py:27-40`). A `promote` tool would let a model
write a canonical record — the precise failure AC5 exists to prevent. Ask the
orchestrator to restate C6 as "route surface only; the MCP interview family
gains nothing, and the reason is that the model records and the owner disposes."

### C14 — Under ruling C6, the design's face plan is superseded and should be struck.

D3's face seam plans "exactly one `Button` and one `StateChip`" on
`InterviewPanel.tsx:120-131`, and D5 has no browser proof. Ruling C6 says the
face is not built here. Strike the face-seam plan from D3 (keep the honest note
that no ratified board draws promotion), so a build lane cannot read the design
as licence to add the control. UX-CANON A.11 ("a verb that does nothing is a
lie — withhold it and ledger it") is satisfied by the wire-only shipment; the
ledger entry is owed.

### C15 — Small factual corrections, so the document's citation record stays clean.

- `RESOURCE_KINDS` has **20** kinds, not 22 (`holdspeak/db/relationships.py:17-22`;
  counted programmatically). The design says 22 three times, and once as "the 22
  consumers", which also conflates kinds with consumers.
- `insert_evidence_link` has **zero** references anywhere, including tests
  (`grep -rn "insert_evidence_link"` returns only the definition,
  `holdspeak/db/delta.py:186`). The design says grep "finds it only in
  `tests/unit/test_delta_schema.py`" — that file tests the *table*, never the
  writer. The design's conclusion is right and stronger than stated.
- The Sizes section is stale. It recommends moving `TaskResume`, the focus half,
  `DRAFT NOT SAVED` and the composer residues to **story 15**; the story file
  has already moved them to **HS-200-41**, and a sibling lane has landed
  `project_ask_tasks` for it (`holdspeak/db/schema.py:4115-4155`). Mark the
  section superseded rather than deleting it (never delete — park).
- Cannot-promise #4 (`/api/ask` server side untraced) is **answered on this
  branch** by that same sibling work: `holdspeak/db/schema.py:4115-4118` —
  "`/api/ask` is one blocking request/response ... and persists nothing — the
  kernel journals a payload hash, and `ask_results` holds the answer without
  the question." Close #4 with that citation.

---

## THE HUNT, SECTION BY SECTION

### 1. The People boundary (P2)

**Broken. See P0-0.** The containment decision fails in exactly the direction
the design claims to have closed. Below is the rest of the walk, which is
sound, plus the full map of how a promoted body reaches a prompt, a tool, a
search result or the wire — the answer to the brief's first question.

**The automatic paths — no attach action of any kind required.** Each was
verified by opening the file.

| # | Path | Where | What fires it |
|---|---|---|---|
| 1 | The global auto-memory retrieval pass | `holdspeak/grounding.py:190-197`, hits hydrated `:209-211` | any model-bearing call with a query and **no explicit sources** (`:188`) |
| 2 | The uncapped `note` hydration branch it feeds | `holdspeak/grounding.py:313-321` | full body, no truncation, no sensitivity check |
| 3 | Every Thread message | `holdspeak/services/thread_service.py:380-390`; frozen verbatim `:397-408`; replayed as `system` `:2095-2107` | the owner typing any text |
| 4 | Every Thought refinement dispatch | `holdspeak/services/ask_service.py:514-527` — empty ref lists, unconditional | any refinement, attached or not |
| 5 | Every recipe run and chat | `holdspeak/services/recipe_service.py:111-125` (`"[MEMORY]\n"` prefix), `:202-210` | `recipe_run` / `recipe_chat` |
| 6 | Every Sequence/Workflow model node | `holdspeak/services/sequence_workflow_service.py:45-70` | `sequence_run` / `workflow_run` |
| 7 | Every workbench item run, including scheduled | `holdspeak/workbench_conductor.py:154-220`; `holdspeak/services/workbench_runner.py:267-271` | a workbench run |
| 8 | Coder steering hydration | `holdspeak/services/coder_service.py:130-150` | coder steer |
| 9 | `memory.search`, `desk.snapshot`, `desk.list`, `desk.get` | `holdspeak/mcp/families/memory.py:11-29`; `holdspeak/mcp/tools.py:754-755`, `:39-62`; all in `CHAT_PALETTE`, `holdspeak/services/thread_tools.py:300-302` | the model calling them itself |
| 10 | `GET /api/sync/pull` — up to 500 full bodies | `holdspeak/services/sync_service.py:1117-1119`; route `holdspeak/web/routes/sync.py:37-42` | a sync pull |
| 11 | Idle-timer autonomy: 4000 chars of a note body into a prompt with no human present | `holdspeak/services/resourceful_service.py:163-193` | the note being filed in a zone named "Loose Ideas" |

**F3 never fires on any of them.** It fences the promotion *direction* into
default/Everyday context, and in the common New-Note mode it is structurally
unreachable (C8). The design credits it with "the entire leak path"; it stops
none of the eleven rows above.

**What the design got right, and I confirm:**

- **Auto-attach at birth is real and containment does close that limb.**
  `apply_default_at_birth_in_transaction` resolves default refs
  (`refinement_context_service.py:531-533`) and persists them (`:549`); Everyday
  members are read at `:889`. That limb is genuinely removed. It is simply not
  the only one.
- **F3's transaction placement is safe** — `BEGIN IMMEDIATE`
  (`interview_service.py:126`) holds the write lock, so there is **no TOCTOU
  window** between the fence read and the commit, provided the fence reads on
  `conn` (C7).
- **The suggestion picker is not an auto-attach.**
  `refinement_context_service.py:588-625` pins candidates into a *picker*;
  nothing attaches without the owner's verb.
- **`person:` genuinely refuses itself.** `RESOURCE_KINDS`
  (`relationships.py:17-22`) has no `person`; `qualified_ref` raises at `:31-32`.
  The store is a separate ciphertext file (`holdspeak/people/store.py:19`, schema
  `:414-421`), the policy allows only this-device owner ops plus one
  capability-gated MCP path (`holdspeak/people/policy.py:44-57`), and a `person:`
  ref freezes display-name-only with `sensitive=True`
  (`thread_service.py:359-369`), which F2's `sensitive=0` predicate excludes as
  a promotion source. **The People store path is closed and the design proves it
  rather than re-guarding it — that judgment was correct.** What is open is the
  path the design itself named: ordinary free text in a non-People section.
- **F2 is free.** `_prune_unavailable_facts` is already invoked *inside* the
  open transaction at `interview_service.py:141` with exactly the SQL cited
  (`:67-80`). The design under-claims here.

**Verified clean** (the sweep checked and I spot-confirmed the shape): meeting
export (`holdspeak/meeting_exports.py` has no `notes` reference), Slack export,
`monday_brief_service`, `needs_you_aggregate`, `project_evidence_collector`,
and the mesh modules read no note bodies.

One dead control worth a ledger line: **`use_zone_context` is persisted, synced
(`holdspeak/services/sync_service.py:122`) and never read by any context
assembler.** It reads like a live privacy switch and is inert.

**Verdict on P2:** the ruling is refused on its stated premise. P0-0.

### 2. The revision model (P1)

`qualified_ref()` is `kind:id` and returns `kind:id` — verified
(`relationships.py:25-33`). Not extending it is right, and the cost argument is
real.

The hash recipe is **not stable**: P0-1. That is the load-bearing failure of
this section.

`promotion_target_unsupported` is reachable for every unshipped kind **only if
the kind is derived from the ref** — C10.

**Do 11, 13, 17 or 20 break under `note`-only?** I read all four. **No.**
Story 11's ACs need a bound source manifest and a kept brief attached to a
Project — a *consumer*, not a promotion target. Story 13 needs decision recall
and a ref-carrying `Carry into brief`. Story 17 needs a pre-dispatch fence read
of `context_dependents`. Story 20 needs corrections to invalidate dependent
plans. None of the four requires promoting **into** a Thought or a Project
facet. The narrowing is survivable downstream; what it breaks is the
phase-level contract line, C11.

### 3. The reverse index (P3)

**Call-site count verified by grep: exactly two** —
`refinement_context_service.py:549` and `:743` (definition `:990`). The design's
riskiest structural claim is true.

The delete-then-insert reconcile is right for all four verbs, and it is scoped
by `consumer_kind`, so it cannot wipe another kind's rows. The `unchanged`
no-op branch the design flags in "cannot promise" #2 is real: `unchanged` is
computed at `:730-734` and gates `_persist_manifest` at `:736-743`. Its
consequence is exactly as the design says — a surviving stale
`bound_manifest_sha256`, harmless to the ref-keyed push.

**The chatty-writer problem is worse than "noisy".** `refinement_thought_service`
writes the working Note on every accepted revision (`:142`, `:552`, `:1062`,
`:1158`), and with P0-1 unfixed the *pull* agrees with the index every time. The
design's mitigation ("the pull is authoritative for display, so the face reads
truthfully") therefore does not hold: both records say stale. Where this
actually bites is D2.3's effect 2 — the **refusal** hook stories 17 and 20 are
promised. An unattended run whose context includes any actively-edited Note
refuses on every dispatch. Add the honest sentence: *the fence stories 17 and 20
inherit will refuse continuously against a record under active edit; those
stories must decide whether their fence reads `forbidden`/`unavailable` only, or
all three.*

**Backfill, re-measured read-only 2026-09-07:** every number in D2.3 reproduces
exactly — `notes` 17/17, `refinement_thoughts` 8 (all `completed`),
`interview_sessions` 0, attachment revisions 4, visible 5, leaves 9,
`thread_message_parts` 28 with 0 sensitive, `knowledge_memberships` 5,
`project_evidence_links` 0, `project_observations` 12, `projects` 10, default
context revision 0 with `refs_json = []`. I also re-ran the pair query: **9**
distinct (ref, thought) pairs at current revisions, **0** restricted to
`state='working'`. The claimed zero-row backfill is correct.

**The arbitration rule tested on one screen:** see P0-1. The design's example
is wrong; a real one exists (`upsert` with an explicit unchanged
`last_modified`, `primitives.py:123`) and should replace it.

### 4. Transactions, concurrency, late results

The failure-window table is the strongest part of the document and most of it
holds: one `BEGIN IMMEDIATE`, the replay guard keyed
`(thread_id, command_id)` with a `request_digest`
(`interview_service.py:133-137`), the deliberate `remove_fact` asymmetry, and
the correct observation that `context_promotions` is not derived from interview
state so it survives a source prune.

Four windows it does not cover:

- **Two clicks, two Notes** — P0-4.
- **Revoke of one promotion among several on one record** — P0-3.
- **Source revoked mid-promotion** — closed by `BEGIN IMMEDIATE`, but only if
  the fences read on `conn` — C7.
- **Death between the record write and the index write** — genuinely absent by
  construction, because promotion writes **no** `context_dependents` row at all
  (it never attaches). The design should say that outright; it is the cleanest
  answer in the whole section and it is currently only implied.

### 5. AC4's gap vocabulary

**Half met.** The design reuses `COVERAGE_STATES`
(`holdspeak/services/needs_you_aggregate.py:52` — verified, five words) and
declines to widen `COVERAGE_KINDS` (`:53` — verified, no context kind) or
`_repair`'s hard-wired hrefs (`:65-88`, `/projects/…` and `/settings` — verified
at `:71`, `:76`, `:78`, `:83`, `:85`, `:88`). That restraint is right; the
aggregate is story 15's.

But the criterion is "blocks new unauthorized disclosure **AND names the
resulting gap**", and the design's own honest answer is that a context gap is
"visible only where a consumer shows it" — and under ruling C6 **no consumer
face ships in this story**. So on the day story 10 lands, a revoked promotion
names its gap in a service response and in a table, and **nowhere the owner will
see**. That is lawful (the gap is ledgered, the words are C4's) but the design
should say it in those words in D2.3 rather than leaving AC4 reading as
delivered. Combined with P0-6, AC4's honest status is: *blocking: yes, for
consumers that read the index. Naming: to a caller, not to the owner, until a
face story lands.*

### 6. Canon

I found **no** canon break in the wire, and I checked each law named in the
brief:

- **Additive only** — three tables, three indexes, two triggers, one seed; no
  `ALTER`. Holds.
- **Every INSERT names its columns** — stated as a requirement and the fence
  test is in the proof table. Holds.
- **Snapshot regenerated by the normalizer** — `tests/unit/test_db.py:1731`
  cited with the normalizer at `:1740-1750`. Holds.
- **Never delete, park instead** — the design parks nothing wrongly; but see
  C15, its own stale Sizes section should be marked superseded, not deleted.
- **No prose in the UI / no counters of zero / every verb the library Button** —
  no face ships (ruling C6), so nothing to break. C14 asks the face plan be
  struck so a build lane cannot reintroduce it.
- **Ledger not gate** — F3 is a refusal, not a ceremony; the receipt in
  `context_promotions` buys provenance. Holds. The rejection of Candidate A on
  exactly this ground is well argued.
- **UX-CANON A.2 (canvas before build)** — the design refers the question up
  rather than assuming. Correct behaviour; ruling C6 answered it.
- One nuance on the "no `CHECK`" rationale: a sibling lane on this same branch
  just shipped a new table **with** a `CHECK` (`schema.py:4145-4147`). The
  design's reason is still right *for `consumer_kind`* — stories 11/13/17/20
  will widen it — but it should be stated as a reason for that column, not as
  house law.

### 7. The honest-size question — **the ruling should stand**

The strongest case against C1: the seam the design draws is genuinely clean. I
verified it. 10a touches `InterviewService`, `web/routes/threads.py` and two new
tables; 10b touches `RefinementContextService._persist_manifest`, `schema.py`
and one new table. Different files, different owners, and — the sharpest
argument — **different transactions**: promotion writes no index row, so the two
halves share no write path at all. Two evidence files would each carry a clean
suite. And the design is right that as one story this is L, not M.

Against that: P200-A08 (`ACCEPTANCE.md:33`) is one behaviour, owned by stories
10 and 20, and neither half can demonstrate it — a split would produce two
evidence files each proving half a scenario, and the phase would have to
re-assemble them at G1. The gate is scenario-shaped, not seam-shaped.

**It survives.** One story is carryable: the ACs are five, the disposition table
is written, the proof table is 18 deterministic tests plus two migration tests
and a reopen test, and the ordering (boundary first) is preserved as the lane
order — which is the whole of what the split bought. What the orchestrator
should add to the ruling is the ordering as an *evidence* requirement: the
evidence file should carry the boundary tests' output before the index tests',
so the record shows the fence landed first.

### 8. What the design cannot promise

The section is unusually honest — nine items, several of them costly to admit.
It is **not complete**, and the omission is the one that bounced the design.

1. **The document promises containment in D1 and D2.4 and disclaims nothing
   about retrieval** — P0-0. This is the item the section exists for and does
   not contain. The nearest it comes is "a promoted Note is exactly as reachable
   as one he typed by hand", stated as reassurance; the section never says what
   that reach *is*, and the eleven-row map in hunt 1 is what it is.
2. **What `revoke` revokes** — P0-6.
3. **AC4's gap is named to a caller, not to the owner** — hunt 5.
4. **"The Tests half in full"** — C12; contradicted by item 5 of this very
   section.

One item can now be **closed**: #4 (`/api/ask` server side), answered on this
branch at `holdspeak/db/schema.py:4115-4118`.

The pattern behind the omission is worth naming for the re-take. The design
walked the *guards* exhaustively and correctly — every limb that keys on
`person:`, `people.*` or `sensitive` — and did not walk the *hydrators*. Every
one of the eleven automatic paths lives in a hydrator or a search, and the
document opens `grounding.py` only at `:313-321` and `:394`, to prove a
negative about the note branch's missing check. It never asked who calls
`hydrate_refs_detailed` and with what.

---

## UNVERIFIED IN PRACTICE — what fails first on his real desk

I re-measured his database read-only. The design's D4 is accurate: **17 notes
(all live), 8 Thoughts all `completed`, 0 working, 0 interview sessions, 0
sensitive message parts, default context revision 0 with `refs_json = []`.**

Flagging the claims that were reasoned, not run:

1. **The retrieval path is live on his desk today, before this story ships**
   (P0-0). His corpus is 17 notes; the auto-memory pass takes 16 slots
   (`grounding.py:24`, `:208`), so on his machine **almost every note he owns is
   a candidate on almost every message he types**. He will not notice, because
   nothing labels an auto-retrieved block differently from an attached one. The
   first promoted sentence joins that corpus inside the promotion transaction.
   This is the thing to walk first, and it is walkable *now*, without any of
   this story's code: promote nothing, type a message whose words match an
   existing note, and read `thread_refs.frozen_json`.
2. **The `corrected` false positive is what bites next** (P0-1). The moment he
   promotes a fact into a Note and anything re-saves that Note, the promotion
   reads `corrected` and his constraint is reported as having moved. There is no
   Interview data on his machine to hide it behind: the very first walk beat
   creates the first promotion, and the second beat trips it.
3. **The whole mechanism starts empty.** He has zero facts to promote and zero
   working Thoughts to index. Nothing in this story can be demonstrated on
   existing data — the design says so, and I confirm it. Any evidence claiming
   "promoted his existing context" would be false.
4. **F3 will never fire on his desk.** His default context is empty and the
   common mode is New Note (C8). The walk cannot show the fence working without
   a constructed setup.
5. **The trigger's write cost is unmeasured** — the design admits it. His
   `notes` table is 17 rows, so it will not show there; it is not a real risk at
   his scale and should not be treated as one.
6. **The `INSERT OR IGNORE ... SELECT` seed on every database open** is
   unmeasured against an 85 MB database. It reads three joined tables at open
   time. The design flags it; on his file it will run against 4 attachment
   revisions and cost nothing, so this will *not* surface on his desk and would
   surface only later. Do not treat a quiet walk as proof it is cheap.
7. **No test was run and no face was opened** for this document. Its author
   says so. I confirm the line numbers; I did not run the code either.

---

## WHAT I COULD NOT VERIFY

- **Whether the promotion behaves as designed.** No code exists. Every judgment
  above is against the read source, the read-only database, and the contracts.
- **The write cost of either trigger, and of the DDL seed**, at any scale. Not
  benchmarked.
- **Whether hunt 1's eleven automatic paths are all of them.** The enumeration
  came from a delegated read-only sweep of `holdspeak/` and `web/`; I then
  opened and personally confirmed the six load-bearing limbs of P0-0
  (`grounding.py:184-217`, `:313-321`; `thread_service.py:380-408`, `:2095-2107`;
  `ask_service.py:514-527`; `recipe_service.py:111-125`) plus the search, MCP
  and sync rows. The rest of the table I cite on the sweep's verification, not
  my own. **Treat it as a floor, not a ceiling** — one more caller of
  `hydrate_refs_detailed` with `include_memory=True` is one more path, and the
  re-take should grep for that call signature rather than trusting this list.
- **Whether a promoted Note is retrieved *in practice*** — retrieval is
  relevance-ranked over 16 slots against his whole corpus, so how often a given
  promoted sentence actually surfaces is a measurement nobody has taken. The
  path is proven; the frequency is not. It is not a defence: the boundary must
  hold at rank 1, not on average.
- **`web/src/desk/ask.ts:127` and `ProjectRoomCore.tsx:1387-1414`** — the
  design's traced-and-closed unknown. I did not open the browser sources; I
  closed the same question from the server side instead, via
  `holdspeak/db/schema.py:4115-4118`, which a sibling lane traced on this branch
  and which reaches the same answer.
- **Whether the orchestrator reads ruling C6's "its MCP and route surface" as
  binding on the MCP question** (C13). I argue the design's refusal is right; I
  cannot rule.
- **Whether P200-A08's "another Thread" was meant literally** — the difference
  between a declared narrowing and an unmet acceptance scenario is his call
  (C11).
- I did not run any test, did not open the product, and touched the owner's
  database only through `sqlite3 -readonly` with `?immutable=1`.
