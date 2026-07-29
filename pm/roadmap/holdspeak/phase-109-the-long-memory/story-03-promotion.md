# HS-109-03 - Decisions become artifacts — promotion

- **Project:** holdspeak
- **Phase:** 109
- **Status:** backlog
- **Depends on:** HS-109-01, HS-109-02
- **Unblocks:** HS-109-05
- **Owner:** unassigned

## The thesis (the bar)

The owner's charge is verbatim: *"records decisions and then creates
artifacts out of those decisions."* The synthesis system already
renders ADRs, decision announcements, and runbook deltas
(`holdspeak/plugins/synthesis.py:13-29`) — but only from a meeting's
plugin run. Nothing lets the owner take ONE accepted decision and
mint the artifact that formalizes it, and no artifact can cite the
decision it came from, because until 01 decisions had no identity.

The bar: **promotion is the owner's gesture on a record, the lineage
is causal, and the consent spine is the existing one.** An accepted
decision promotes into an ADR (or announcement, or note) whose
`artifact_sources` row says `decision:<id>` — the flexible lineage
table (`db/core.py:415-447`) carries it without a new mechanism.
Accepting IS approval (Article XI.4); only the model call admits.

## Problem

A decision that matters gets re-typed by hand into an ADR somewhere
outside the system, and the causal thread — this ADR exists because
of that decision, which that later decision superseded — is exactly
the memory the archive cannot hold today.

## Recipe

1. **The lineage kind.** `artifact_sources` learns a `decision`
   reference kind. The artifact repository's atomic source-replace
   (`db/plugins.py:656-758`) is reused untouched.
2. **Deterministic promotion.** Promote-to-note / promote-to-ADR from
   the record's own fields (text, rationale, moment, meeting link) —
   no model, no admission, instant, exactly like aftercare's
   deterministic follow-up draft (`meeting_aftercare.py:290-355`).
   The owner's promote gesture is the approval; the write leaves the
   house receipt.
3. **Model-assisted promotion.** "Draft the ADR with the model" runs
   through the registered `inference.run@1` operation — admitted,
   receipted, destination-badged — and lands as a `draft` artifact
   for review. RuntimeProfile resolution as everywhere else; no new
   inference path.
4. **Review verbs on the record.** Accept / reject / supersede from
   01 gain their product meaning: superseding a promoted decision
   marks the derived artifact's face (05 renders it); statuses ride
   the existing artifact `review_status` field
   (`db/plugins.py:679-693`), which finally earns its keep.
5. **Idempotency + re-promotion.** Promoting twice updates the same
   derived artifact (stable derived ID); promoting after supersession
   refuses by name ("superseded by <id> — promote that one").
6. **No modals, no prose.** Everything in-world through existing
   routes; UI lands in 05 — this story ships the seams + routes and
   proves them at the API level.

## Out of scope

- The memory window UI (HS-109-05).
- New artifact types — the fifteen existing syntheses are the menu.
- External filing (Slack/GitHub) of promoted artifacts — the existing
  actuator spine already covers it separately.
- Editing promoted artifact bodies (notes are already editable
  primitives; ADR body editing beyond that is not this story).

## Acceptance

- An accepted decision promotes deterministically to a real artifact
  whose `artifact_sources` cite `decision:<id>`; the decision lists
  its derived artifacts; both directions queryable.
- A model-assisted promotion leaves an `inference.run@1` receipt with
  destination named; the artifact lands `draft`; zero model calls
  happen without admission (census-checked in tests).
- Superseding propagates: old decision → `superseded_by`, its derived
  artifact queryably marked; re-promotion of a superseded decision
  refuses by name.
- Double-promotion is idempotent — one artifact, updated.
- No new consent surface exists; no modal; the promote gesture writes
  a receipt.
- Full suite green; spine byte-unchanged.

## Test plan

- **Unit:** lineage kind round-trip; derived-ID stability; refusal on
  superseded; review_status transitions.
- **Integration:** promote→artifact→sources; model-assisted path with
  a fake runner asserting admission precedes generation.
- **Live (evidence):** a real decision from a real meeting promoted
  both ways — deterministic and via `.43` — receipts read back;
  supersession walked end to end.

## Chef's notes

- The receipt for deterministic promotion is the ordinary write
  receipt — do not invent kernel ceremony for a local DB write the
  owner just performed (Article XI clause 1 judges the effect, and
  filing a local artifact is the desk's bread and butter).
- Watch `artifact_sources` uniqueness: a promoted artifact cites its
  decision AND its meeting; the atomic replace must keep both.
- The refusal string is product surface — "superseded by" must name
  the successor so the owner can follow it.
