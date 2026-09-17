# HS-200-46: A stale document fails CI instead of misleading the next agent

- **Project:** holdspeak
- **Phase:** 200
- **Status:** ready
- **Depends on:** HS-200-03
- **Unblocks:** HS-200-39, HS-200-40
- **Owner:** unassigned
- **Gate:** G0
- **Trace:** the 2026-09-13 operational-surface audit §7b of `docs/internal/project-rooms/HANDOVER-MUADDIB.md`; the owner's instruction, 2026-09-13

## Problem

**A zero-context agent cannot tell a true document from a stale one, and this tree
has both.** The operational-surface audit checked load-bearing sentences against
the code and found thirteen that are false. Several of them describe work someone
INTENDED, which is precisely how the next reader concludes it was already done:

- `holdspeak/web/routes/mcp_http.py:3` — claims the route composes "on the web
  runtime's LIVE services (never the sidecar's bare `serve()` instances)". It
  reaches the same bare composition (HS-200-45).
- `holdspeak/db/connection.py:3` — claims "WAL pragmas". `journal_mode` is
  `delete`; only `foreign_keys=ON` is set; there is no `busy_timeout`.
- `holdspeak/mcp/resources.py:60` — claims the verb catalog "Mirrors
  web/src/desk/verbRegistry.ts". It has drifted by 20 verbs with 13 phantoms.
- `holdspeak/mcp/resources.py:158` — advertises Desk state "including its stored
  objects **and layout**". No layout is returned.
- `docs/internal/UX-CANON.md:131` — states A1 holds at "4 residues with reasons".
  There are 187 raw `<button>` elements (HS-200-44).
- `docs/USER_GUIDE.md:978` — "the owner's web token is refused on a non-loopback
  request". True only for `/api/mcp`.
- `docs/SECURITY.md:277` — Reach "accepts connections on the tailnet address
  only". `bind_host` is applied by nothing; no CIDR check exists.
- Plus `DESK_GRAMMAR.md:50` (retired localStorage keys), `MCP_SIDECAR.md:854`
  (stale counts), `CLAUDE.md:153` (dw-mcp wiring), and Phase 172's settled design
  asserting a queue drains intel jobs it never touches (HS-200-42).

Handover §7b is the hand-maintained version of this list. **A hand-maintained
list of lies rots exactly like the lies it catalogues.** The durable form is a
test.

This is the same defect class as the guard in HS-200-44 and the doubles in
`reference_lying_test_doubles`: a claim nothing checks. Here the claim happens to
be in prose rather than in an assertion.

## Scope

A fence that binds load-bearing documentation claims to the code they describe,
as a down-only ratchet in the shape HS-200-03 established, so a stale sentence
fails a check rather than misleading a reader.

Implementation seams: a claims registry beside the test; `tests/unit/`;
`scripts/` if a reporting entry point helps; the CI job HS-200-03 built;
handover §7b becomes generated or is retired in favour of the registry.

Out: verifying prose in general, or any form of natural-language checking. This
fence covers a CURATED set of claims, each with an executable predicate. A claim
that cannot be expressed as a predicate does not belong in the registry.

Out: fixing the thirteen false sentences. Each belongs to the story that repairs
its code — 42, 44, 45 — or is a one-line doc correction made here only when no
story owns it.

## Acceptance criteria

- [ ] A claims registry exists in which each entry carries: the document and
      anchor, the sentence in the author's own words, an executable predicate
      over the code, and a state — `holds` or `known_false`.
- [ ] `holds` entries FAIL the check when the code stops satisfying them. Proven
      by mutating the code, not the registry.
- [ ] `known_false` entries FAIL the check when the code starts satisfying them —
      so fixing the code forces the sentence to be corrected in the same commit,
      and a fixed claim cannot sit in the ledger pretending to be debt.
- [ ] The `known_false` count is a **dated, down-only ratchet**. It may shrink; it
      may not grow without a named reason in the same commit, exactly as
      HS-200-03's three fences were converted.
- [ ] The thirteen claims from handover §7b are the opening registry, each with
      its measured truth recorded.
- [ ] The check runs in the existing CI job and names, on failure, the document,
      the sentence, and what is actually true — a failure a reader can act on
      without opening the test.
- [ ] Handover §7b is generated from the registry or deleted, so there is one
      list and not two.
- [ ] The fence is proven to FAIL against the pre-fix tree in both directions:
      one `holds` claim broken, one `known_false` claim satisfied.

## Test plan

Planned suite: `phase200_doc_claims`. Every predicate reads the real module, the
real generated surface, or the real scanner output — never a copy of the value
typed into the test (`reference_lying_test_doubles`: asserting against a constant
you transcribed proves only that you can transcribe).

## Notes / open questions

**The owner's instruction, 2026-09-13:** he was told §7b is hand-maintained and
will rot, and that the durable version is a test that fails CI. His answer:
*"Please, add it..."*

Two claims in the opening set are worth their own predicate design, because they
are the ones most likely to drift again: the verb-catalog mirror
(`resources.py:60` against `web/src/desk/verbRegistry.ts`, which the audit found
drifted by 20 verbs with no test binding them) and `desk_snapshot`'s advertised
shape. Both are also prerequisites the audit named for any future wire-face work,
so building them here is not scope creep — it is the cheap half of that
groundwork, paid where it already belongs.
