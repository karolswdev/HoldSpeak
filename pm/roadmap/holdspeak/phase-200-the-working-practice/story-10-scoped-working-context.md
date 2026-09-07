# HS-200-10: Promote reusable working context into canonical records

- **Project:** holdspeak
- **Phase:** 200
- **Status:** in-progress
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
