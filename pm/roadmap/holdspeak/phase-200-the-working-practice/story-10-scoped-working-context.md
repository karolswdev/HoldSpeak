# HS-200-10: Promote reusable working context into canonical records

- **Project:** holdspeak
- **Phase:** 200
- **Status:** done
- **Depends on:** HS-200-06, HS-200-09
- **Unblocks:** HS-200-11, HS-200-13, HS-200-17, HS-200-20, HS-200-40
- **Owner:** unassigned
- **Gate:** G1
- **Trace:** AA-IVW-002–003; AA-CTX; AC-31, AC-37; C3

## Problem

Interview facts belong to one Thread. Useful goals and constraints need explicit, inspectable reuse across related work.

## Scope

Promote selected facts into existing Note, Thought, or Project-owned context and attach canonical refs in later tasks.

Implementation seams: InterviewService; Note/Thought/Project services; qualified refs; context attachment.

Out: A global personal profile, organization crawler, or a new Goals database.

## Acceptance criteria

- [ ] Promotion identifies source quotation, target scope, and target revision.
- [ ] Two Threads can reference the same context without separate editable copies.
- [ ] A correction updates the canonical record once and marks dependent prepared work stale.
- [ ] Removing or revoking a source blocks new unauthorized disclosure and names the resulting gap.
- [ ] Protected People content cannot enter ordinary context through promotion or derived suggestions.

## Test plan

Planned suite: phase200_working_context. Exercise concurrent edits, promotion replay, source deletion, cross-Thread reuse, protected material, and reopen.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G1](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.

Re-judged M to L on 2026-09-07 after three trace lanes, and narrowed to the five
acceptance criteria above. The obligations the daily-workflow design's Sizes table
had added here — `TaskResume`, the focus half of return-to-task, Thread draft
custody and the composer residues — moved to
[HS-200-41](story-41-return-to-unfinished-work.md); they are about resuming
unfinished work, not about working context, and they were placed here only because
the design had nowhere else to put them.

The wire is designed before it is built:
[assets/settled-design-working-context.md](assets/settled-design-working-context.md).
Three problems the story text does not settle, and the design must:

1. **Target revision has no home.** `qualified_ref()` is `kind:id` and carries no
   revision (`holdspeak/db/relationships.py:25-33`), and the three targets disagree
   about what a revision even is — a Note has one timestamp
   (`holdspeak/db/schema.py:879`), a Thought five counters (`:898-902`), a Project
   revisions on itself, each resource and each item.
2. **The People boundary is a classification problem.** Every existing guard keys
   on the `person:` ref kind, the `people.*` tool family, or
   `thread_message_parts.sensitive` (`schema.py:3608`), and a promoted Note is none
   of the three. `notes` has no sensitivity column at all. People refusals are a
   hard boundary, so the guard is designed before the verb exists.
3. **Stale is a pull; AC3 asks for a push.** `refinement_attachment_visible` is
   keyed by thought and revision with the ref as a payload column, so there is no
   reverse index from a corrected record to its consumers, and stories 11, 13, 17
   and 20 all add consumers.

One built-but-dead target already exists and the design must judge it rather than
ignore it: `project_evidence_links` (`schema.py:3870-3878`) carries
`excerpt_locator_json`, the one column in the schema shaped like a source
quotation, and its writer `insert_evidence_link` (`holdspeak/db/delta.py:186-213`)
has no production caller.

### The design rulings (2026-09-07)

The wire design is
[assets/settled-design-working-context.md](assets/settled-design-working-context.md).
Counsel's hunt on it is owed before build closes; these rulings stand meanwhile.

**C1 — one story, ordered, not two.** The design proposed splitting into a
boundary half (AC1, AC4, AC5) and a reference half (AC2, AC3). Refused on the
phase's own terms: scenario P200-A08 is "promote a stated constraint, reuse it in
another Thread, correct it, and revoke a source" as **one** behaviour, and neither
half could demonstrate it alone. The design's ordering argument is accepted in
full and becomes the lane order: the boundary lands **before** the thing it
bounds, so there is never a window in which promotion exists without fence F3.

**C2 — containment, not classification.** A promotion writes a canonical record
and **never attaches it to anything**. That deletes the last two limbs of the leak
path outright: a promoted Note becomes exactly as reachable as one the owner typed
by hand, and attachment stays his own separate verb. Both alternatives are
refused. A disclosure class chosen inside the verb asks him for a judgment on free
text at the moment he is least thinking about disclosure, and wrong once is a
breach — that is a gate, and this repo's law is ledger, not gate. A
`notes.sensitive` column is worse: nine readers would each have to honour it, it
defaults to 0 and is therefore **fail-open**, and `notes` is the Desk's most-read
table. Verified while ruling: `holdspeak/grounding.py:313-321` — the `note` branch
— has **no sensitivity check of any kind**; the `sensitive` filter at `:390-396`
guards only the `thread` kind. Containment is what makes that survivable.

**C3 — `qualified_ref()` is not extended.** It stays `kind:id`; extending it would
touch every consumer and every stored ref in the owner's live database. The
revision lives on the promotion record as two columns, and only one is ever
compared: a per-kind display label, and an authoritative content hash computed by
the recipe already in `refinement_context_service.py:975-979`. The codebase
already learned that a timestamp cannot be the comparator — `refinement_attachment_visible`
stores both and compares the hash (`schema.py:977-978`,
`refinement_context_service.py:815-818`). The mechanism is kind-dispatched and
service-validated; the `note` kind ships, and every other kind refuses with
`promotion_target_unsupported` rather than pretending. Thoughts and Project facets
are named honestly in the design as needing more than one hash, or having none at
all.

**C4 — `project_evidence_links` is not the home.** Its `excerpt_locator_json` idea
is borrowed; the table is not. It is `project_id NOT NULL ... ON DELETE CASCADE`
(`schema.py:3872`) where promotion must work on a desk with no Project, that
cascade would silently delete provenance, and its only index points at the
consumer — the opposite of what the reverse index needs.

**C5 — the reverse index is `context_dependents`, one row per record and
consumer**, never one per revision, which is what makes it survive a table whose
revisions are never pruned. One write point, `_persist_manifest`, with exactly two
call sites. Where the index and the existing on-read check disagree, **the pull
wins for display and the index wins for refusal** — exact where the owner is
looking, fail-closed where something would run unattended.

**C6 — the promotion face is not built here.** These five criteria need no new
control, and the one the design would add is a new verb the owner clicks, which
under the face canon owes a ratified board first. The Interview panel it would
land on is pre-Surface-canon in its own right. Both are ledgered; this story ships
the wire and its MCP and route surface.

**C7 — AC2 is narrowed to the scope where the mechanism exists.** Two Thoughts
already share one editable record by reference. The criterion says Thread, and a
Thread's grounding is a **copy** (`thread_refs.frozen_json`, `schema.py:3614-3622`).
That gap is proved by a test that demonstrates it, not asserted in prose.

### Counsel's bounce, and the rulings it overturns (2026-09-07)

Counsel's read: [assets/counsel-on-design-200-10.md](assets/counsel-on-design-200-10.md).
**VERDICT: BOUNCE**, on seven P0s and nine conditions. The design gate did its
work — no code was written against it.

**C2 is REVERSED. Containment does not contain, and the premise was inverted.**
The ruling held that a promotion which never attaches is safe, because a promoted
record becomes exactly as reachable as a Note the owner typed by hand. That is
false, and the orchestrator verified the chain rather than taking it on report:
`holdspeak/grounding.py:188-197` runs a **global relevance search if and only if**
`not has_explicit_sources` — that is, **not attaching is the trigger condition for
automatic retrieval**, not an escape from it. It takes 16 hits, hydrates them
through the `note` branch at `:313-321` which returns `body_markdown` whole with
no sensitivity check, and `holdspeak/db/memory.py:484-491` pulls notes out of the
FTS index with no sensitivity condition at all — the `p.sensitive=0` filters at
`:545` and `:1104` guard `thread_message_parts`, not `notes`. Model-bearing
callers opt in on every Thread message with non-empty text
(`thread_service.py:380-390`, frozen verbatim into `thread_refs.frozen_json` with
`"sensitive": False` at `:397-408`) and on every Thought refinement
(`ask_service.py:514-527`).

So the design's own leak sentence passes F1, passes F2, passes F3 — a newly minted
ref cannot already be in default context — and is then pulled into the next prompt
whose words happen to match it. Counsel's sharpest point: **the design's most
valuable planned test would have passed green while the leak was live**, because
it asserts over the attachment envelope and the sentence arrives through a
different one.

The distinction the reversed ruling missed is one of authorship. A Note is
something the owner wrote deliberately. A promoted record is something the system
extracted from an Interview answer he gave about goals. Putting the second into a
relevance pool he cannot see is the breach, and it is not excused by the first
already being there.

**C2′ — the replacement ruling: reachable by reference, never by relevance.** A
promoted canonical record must not enter the relevance pool at all. Explicit
reference reaches it; a relevance search never does. That kills the path by
construction rather than by a column that defaults to zero and fails open. The
re-take settles the mechanism — the FTS triggers at `schema.py:1213-1226` are the
obvious seam — and **proves it through `grounding.build` on the unattached path**,
never through the attachment manifest. A test that cannot fail on the real leak
path is not proof.

**C6 is AMENDED, accepting counsel's C13 and C14.** Routes only: there is **no
MCP `promote` tool**. The design was right to refuse a model the power to mint a
canonical record, and the earlier phrasing "its MCP and route surface" contradicted
it. The design's face plan is struck under the same ruling; the face still owes a
board.

**C1, C3, C4, C5 and C7 stand.** Counsel argued the strongest case it could
against the one-story ruling and reported that it survives, with one addition
adopted here: the evidence file carries the boundary tests' output **before** the
index tests', matching the lane order.

The remaining six P0s and nine conditions are carried into the re-take in
counsel's own words; they stand independently of the bounce.

### The build rulings (2026-09-08) — three lanes, and two things the build changed

The wire was built in three lanes with strict file ownership, in the order ruling
C1 requires: the boundary (A), then the verb it bounds (B), then the reverse index
and the two fences A could not reach (C).

**B1 — L4 is keyed on EXISTENCE, and fences only rows frozen BEFORE the
promotion. ACCEPTED.** D2.4's wording was "the replay skips a `note:` ref carrying
an *active* promotion". Lane C deviated twice and both deviations are right.
Keying on `active` would let a **revocation re-open a replay surface that
promotion had closed** — the opposite direction from every other fence here, and
inconsistent with the corpus guard, which keys on existence. And a blanket
ref-keyed fence would **break by-reference attachment in Threads**: a Thread's
explicit `refs=[...]` reach the model ONLY through the `thread_refs` replay, so a
blanket fence silently drops a promoted Note the owner attached on purpose. That
is "silent loss of accepted input" and a direct contradiction of C2′, which
promises reachability BY REFERENCE. Because L1/L2/L3 mean relevance can no longer
produce a promoted ref, anything frozen *after* a promotion can only have arrived
by reference, so the time key is sound. An unparseable `created_at` fences
everything. This is the L3 mistake — a fence placed inside a shared path — one
layer down, and only one test in the tree catches it.

**B2 — `forbidden` is TERMINAL IN PRACTICE, and nothing in the product clears it.
Recorded as a known limitation, NOT fixed.** The schema comment inherited from the
design says the mark is "cleared ONLY by an explicit re-promotion". That sentence
is **unimplementable as the design stands**: promotion deliberately writes no
`context_dependents` row (D2.7's "failure window that cannot exist"), a rebind
through `_persist_manifest` deliberately re-inserts `forbidden` with its original
`stale_since`, and the note triggers preserve it. So `revoke_promotion` sets a
mark that no route lifts.

The orchestrator implemented the clearing, and **the existing P0-2 test refused
it** — `test_a_revocation_is_never_downgraded_by_a_later_stale_marking` asserts
that a standing `forbidden` survives a later promotion into the same record. That
is counsel's own P0 and it is ratified; a consumer fencing on `forbidden` must
never see refreshable staleness and dispatch. The change was reverted. Fail-closed
wins, and a design sentence written before the lattice existed does not outrank a
ratified P0 test.

**The consequence, as it was stated here on 2026-09-08 — and it was FALSE.** This
ruling read: "a consumer fenced once is fenced forever, for that record, by every
route." Counsel-on-built traced the code and refuted it. `_reconcile_dependents`
(`refinement_context_service.py:1095-1108`) carries `forbidden` forward by reading
the live table into `held`, deleting every row for the consumer, and re-inserting.
A **detach deletes the row outright** — the tree's own
`test_a_detach_removes_the_row_and_a_birth_creates_it` proves it — so on a later
re-attach `held` is empty for that ref and the row returns with `stale_reason=''`.

**Detach then re-attach clears a standing `forbidden`. Two ordinary owner clicks,
silently.** It is a worse escape hatch than the one the design asked for: the
designed clear was an explicit re-promotion, a deliberate act on the record; this
one is a side effect of attachment churn that the owner has no reason to connect
to a revocation.

So the choice was never "fail-closed forever versus a way out". The system already
has a way out and it is the wrong one. The hole is now PINNED BY A TEST rather
than described in prose —
`test_a_detach_then_reattach_currently_clears_a_standing_forbidden`
(`tests/unit/test_phase200_working_context_index.py`), whose docstring says
plainly that it records a known hole and not a desired property.

**Why it is not closed on this commit.** Counsel's proposed fix is to stop
carrying `forbidden` in the row and derive it at reconcile time from the record's
own state (`EXISTS a revoked promotion AND NOT EXISTS an active one`). Counsel
argued this keeps the ratified P0-2 test green. **It does not.** P0-2
(`test_a_revocation_is_never_downgraded_by_a_later_stale_marking`) asserts that a
standing `forbidden` SURVIVES a later promotion into the same record; under
derivation that later promotion leaves an `active` row and the predicate correctly
stops fencing, so the assertion fails. That is the same collision that made the
2026-09-08 clearing revert, one layer down.

**The ruling stands, on a narrower and honest basis: `context_dependents` is
WRITE-ONLY today.** Outside tests nothing in `holdspeak/` reads it for a refusal —
`forbidden` fences nothing yet. The lattice is therefore unproven against a real
consumer, and re-cutting its semantics with no consumer to prove it against is the
wrong trade. Stories 11, 13, 17 and 20 land the first consumer; the shape of the
way out is settled with that story, and it needs both halves — the derived
predicate AND an owner verb on the record that lifts the
`context_promotion_suppressions` row — because a clear reached through
`_persist_manifest` is a clear by attachment churn, which is what P0-2 was right
to refuse.

**B3 — the backfill is wired, and proven wired.** `backfill_dependents_in_transaction`
lives beside `_persist_manifest` and calls `_reconcile_dependents`, the same writer
`_persist_manifest` itself calls, so the two shapes cannot drift. (This ruling
first said it calls `_persist_manifest`; counsel-on-built caught that. The code is
right and the sentence was wrong: calling `_persist_manifest` would also write
`refinement_attachment_revisions` / `_visible` / `_leaves` rows, which a backfill
must never do.) It
is invoked from `db/reconcile.py` after the trigger refresh, under a
function-local import (`db/` must not depend on `services/` at module level) and
inside a swallowing guard — a blind reverse index is a recoverable stale-marking
gap, a reconcile that cannot finish is a desk that cannot open.
`test_reconcile_actually_calls_the_backfill` drives `reconcile_schema` rather than
the helper, because the helper shipped built, tested and uncalled.

**B4 — what AC4 does NOT cover, said here rather than only in the design asset.**
AC4 reads "Removing or revoking a source blocks new unauthorized disclosure." The
honest half: **a model in an ordinary Thread can read a promoted body with one
`desk.list` / `desk.get` / `desk.snapshot` call.** Those three carry the full
`body_markdown`, sit in `CHAT_PALETTE` (`holdspeak/mcp/thread_tools.py:300`), and
are model-callable every turn. Two more routes read bodies unfenced:
`ResourcefulService._loose_idea` (`resourceful_service.py:163-193`, a body sliced
to 4000 characters into an unattended prompt) and `SyncService.pull`'s notes
bucket. All five are named at file:line in the settled design
("WHAT THIS DESIGN CANNOT PROMISE" #1) and pinned POSITIVELY by
`test_desk_snapshot_and_sync_pull_still_carry_the_body`, so a shape change is
caught — but that is an asset, and this story file is what is read at close.

**F0 fences RELEVANCE and reduces no part of that exposure.** C2′ is "reachable by
reference, never by relevance", and a `desk.list` call is a reference the model
chose to make. Closing it is a different boundary — the model's own read surface —
and it belongs to the story that gives `context_dependents` its first consumer,
not to this one. Counsel-on-built asked for this to be stated where the owner will
see it, and that condition is accepted in full.

### Counsel-on-built (2026-09-09) — two lanes, and what they changed

Two counsel Fedaykin hunted the built wire, one on the boundary (`db/memory.py`,
`db/schema.py`, `db/reconcile.py`, `grounding.py`), one on the verb, the reverse
index, sync and the consumers. **Both returned RATIFY-WITH-CONDITIONS.**

**The central claim survives.** The boundary lane enumerated every path that reads
a note body and found NO undisclosed route: the lexical route is fenced three deep
(L1 corpus, L2 `excluded` union, the belt predicate), the graph route is fenced at
`db/memory.py:827`, both `grounding` relevance call sites are fenced, and the
three genuinely unfenced routes are the disclosed ones now recorded in B4. Every
note write reaches one of the two guarded triggers; nothing writes
`notes_memory_fts` outside them but three deliberate `DELETE`s. Promoted-after-
indexed, undelete, hard-delete-then-recreate, `rebuild_memory_index` and an
unreconciled older database were each traced and hold.

**P0-1 — L4's time key was unsound across devices, and this commit is what made
promotions cross-device.** B1 keyed the replay fence on time, arguing that
anything frozen after a promotion could only have arrived by reference. That is
true only on the device where the promotion row exists. A desktop that has not yet
synced has an unfenced corpus; a relevance pass there freezes the whole body into
`thread_refs.frozen_json` at 10:00 while the laptop's promotion says 09:00, the
post-apply sweep repairs the corpus and never touches `thread_refs`, and
`10:00 >= 09:00` then reads a relevance body as "arrived by reference" **forever
on that device**. No clock skew required; skew only widens the window. The
comparison was also a REMOTE wall clock (`created_at`, copied verbatim on merge
and deliberately excluded from the LWW field set) against a LOCAL one.

**FIXED by recording the ORIGIN and consulting no clock at all.** `thread_refs`
carries how the ref arrived — `relevance` or `reference` — stamped at the freeze
site, and L4 drops a promoted `note:` ref of relevance origin unconditionally.
That is what B1 was reaching for; the timestamp was a proxy and the proxy is what
broke. B1's real constraint is preserved exactly: **a promoted Note the owner
attached BY REFERENCE still reaches the model**, which is C2′'s own promise, and
the `thread_refs` row itself stays untouched — receipts immutable, replays fenced.

**P0-2 — `revoke_promotion` downgraded `unavailable` to `stale`.** The `CASE` at
`interview_service.py:545-549` protected `forbidden` and nothing else, so a
dependent whose note had been DELETED was overwritten to ordinary refreshable
staleness the moment any other promotion into that ref was revoked while a
survivor remained — a consumer would then attempt a refresh that cannot succeed,
against the schema's own declared lattice. FIXED.

**AC4 could not be exercised at all.** `InterviewService.promotions()` had no HTTP
route and no MCP tool, and `get()` does not carry promotions, so there was no way
to obtain a `promotion_id` outside the single `promote` response — the owner could
not revoke anything. The READ route is added here as WIRE. Ruling C6 stands: the
face is still struck and still owes a board, and there is still **no MCP tool** for
any of these verbs.

**Two latent fail-open seams, both closed.** The B3 backfill sat outside the
module's own partial-failure transaction, so a `_reconcile_dependents` failure
after its `DELETE` and one `INSERT` would COMMIT a half-built row set that the
`id NOT IN (...)` skip then treats as complete on every later open — a reverse
index permanently blind to that consumer, which is exactly AC3's job. Each
consumer now runs under its own `SAVEPOINT`. That fix closed a second defect
counsel did not name and which is **not** latent: the swallowed exception left the
implicit transaction OPEN on the connection reconcile was still using, so step 4's
`BEGIN` would raise "cannot start a transaction within a transaction" — a desk
that cannot open. And `grounding._drop_promoted` returned members UNFENCED for a
handle lacking `promoted_refs`, where its own sibling's docstring says this fence
must never fail open; it now raises, with `memory is None` the one deliberate
exemption (no relevance search ran, so there is no pool to fence).

**Four test repairs.** The "no MCP tool" guard read one family and would have
passed a promote tool registered in any other — it now asserts over the whole
registry. The revoke path had never been driven against a row the REAL reconcile
point wrote; lanes B and C now meet in one integration test.
`test_the_backfill_never_clears_a_forbidden_mark` did not drive the backfill, and
was proven blind: re-run against the deleted skip predicate it stayed GREEN. The
detach/re-attach hole is now pinned by the test named in B2.

**The law held again, and it was applied on purpose this time.** Counsel judged
the boundary lane's fence tests the strongest in this repo — real entry points,
positive controls, byte-level assertions, `retrieval_origin` asserted so the graph
route is provably exercised, a substring check over every column proving the quote
is never copied, and docstrings that record honestly where a fence is redundant
instead of pretending it is load-bearing. Every fix above was written test-first
and watched FAIL against the shipped code, and every new fence was mutated out and
watched go red.
