# HS-160-04 - The decisions: four verbs, one atomic accept, dismissals that stay dead

- **Project:** holdspeak
- **Phase:** 160
- **Status:** done
- **Depends on:** HS-160-03
- **Unblocks:** HS-160-05
- **Owner:** unassigned

## Problem

DEL-002..005: accept / edit-and-accept / defer / dismiss are durable
per-proposal decisions; dismissed material MUST NOT recur unless its
basis changes (the dismissal_basis_hash law); deferred material
returns at its due condition without masquerading as new; accepting
the review atomically applies accepted patches, freezes the summary,
and advances the Project's review pointers (SYS-023) — all under the
158 revision law.

## Scope

- **In:** `decide_proposal(project_id, proposal_id, verb, patch?)` —
  accept applies the registered patch through the EXISTING item/room
  commands (accepted proposals whose kind maps to item
  create/update/transition ride those handlers — §5.7's "applied
  through a registered command handler"; no parallel mutation path);
  edit-and-accept takes the edited TYPED patch (WEB-DLT-004's
  server side); defer takes optional deferred_until; dismiss stamps
  the basis hash. `accept_review(project_id, review_id)` — ONE
  transaction: apply accepted, review→accepted, last_review_id/at +
  cursor forward, revision law envelope (conn-accepting helpers per
  the 159 M-1 law). Recurrence: the next open_review suppresses
  dismissed-unchanged (hash match) and returns deferred-due
  material marked as returning, not new (DEL-004).
- **Out:** routes (05), the face (06), bulk accept (the face may
  batch client-side over compatible kinds — WEB-DLT-007's server
  side is just N decide calls).

## Acceptance criteria

- [ ] Each verb durable + idempotent under command_id; a decided proposal refuses re-deciding (typed conflict).
- [ ] DEL-003 proven: dismissed → identical next window suppresses; a changed basis (new source_version/patch) yields a LINKED successor, not a resurrection.
- [ ] DEL-004 proven: deferred returns at due, flagged returning.
- [ ] DEL-005/SYS-023: accept_review atomic (fault-injected), cursor + pointers advance exactly once, accepted patches land through the registered handlers (an item-kind proposal creates a REAL project_item via the 158 command).
- [ ] DOM-007 still holds: no proposal path completes a milestone without the transition verb.

## Test plan

- **Unit:** `tests/unit/test_review_decisions.py` (verbs, recurrence laws, atomic accept fault-injection, handler routing, the DOM-007 guard).

## What shipped

- The four verbs on ProjectDeltaService, idempotent under command_id,
  already-decided → typed conflict. CLOSED handler map:
  risk_attention → ProjectService.create_item (a REAL project_item,
  the 158 command, DOM-007 guarded — a reached-milestone patch is
  stripped); review_flag / observation_attention / coverage_degraded
  → record-only (the accepted proposal + evidence links ARE the
  truth, documented); conflict → accept REFUSED (typed capability;
  judgment framing only).
- RULINGS documented: proposal decisions don't bump the aggregate
  revision (§5.7's decided_at is proposal-level; accept_review and
  handler-created items ride DOM-003); undecided-at-accept →
  SUPERSEDED (neither suppressed nor returning — fresh material gets
  a fresh proposal).
- Recurrence: dismissal_basis_hash = sha256(source_version|patch);
  unchanged → suppressed; changed basis → linked successor
  (predecessor id in patch_json — no schema change); deferred-due
  returns FLAGGED returning; un-due stays suppressed.
- accept_review: ONE transaction (conn-accepting family) — status +
  cursor + revision law + ledger event; fault-injection proves
  all-or-nothing; cursor advances exactly once.
- ORCHESTRATOR HARDENING (in-story): the cursor compare became
  aware-UTC (`_parse_utc` both sides) — the naive-vs-offset
  lexicographic hazard the worker flagged is dead, with a
  TZ-boundary test. 30 + 1 new tests; 172→76-scoped re-verified
  green.

## Notes / open questions

- The registered-handler map is the extension seam P4's Steward reuses — name it clearly, keep it closed.
- **HONESTY CORRECTION AT THE CLOSE:** counsel caught that the
  DEL-003 suppression claim above was weaker than its words — the
  basis hash used review_window_key (unique per window) so
  cross-window suppression never fired; everything returned as
  linked successors. FIXED IN-ROUND at 08: the observation's
  source_version now rides patch_json (`_source_version`, outside
  the deterministic-ID inputs) and BOTH hash sites derive from it;
  `test_unchanged_basis_suppressed` now proves HARD suppression
  across two windows (len == 0). The claim is true as written.
- Banked: PROVENANCE_KINDS is closed to {owner} — delta-born items carry provenance via evidence links, not a new enum value (revisit at P4 if the Steward needs its own).
