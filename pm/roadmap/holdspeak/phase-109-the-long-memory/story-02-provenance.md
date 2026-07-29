# HS-109-02 - Provenance — the transcript moment

- **Project:** holdspeak
- **Phase:** 109
- **Status:** backlog
- **Depends on:** HS-109-01
- **Unblocks:** HS-109-03, HS-109-05
- **Owner:** unassigned

## The thesis (the bar)

Action items already carry `source_timestamp` back to the transcript;
decisions do not — the capture prompt
(`holdspeak/plugins/builtin/decision_capture.py:29-39`) asks for
`decision` and `rationale` and nothing else, and Phase 49 recorded
the limitation honestly. A memory the owner will trust years later
must answer "show me the moment we said that."

The bar: **a newly captured decision carries its transcript moment,
and a record without one says so plainly.** Fabricated or guessed
timestamps are worse than absence — Article VI makes absence honest
and invention a defect.

## Problem

A decision record (01) knows its meeting but not its moment. The
transcript is the receipt (`HistoryCore` renders it as exactly that),
yet the one artifact family the owner queries by "when did we decide"
cannot jump to its evidence.

## Recipe

1. **Capture.** Extend the decision-capture plugin's prompt/schema to
   emit an optional `source_timestamp` per decision, the same shape
   action items use. The plugin remains a deferred LLM job; a model
   that returns no timestamp yields honest absence.
2. **Verify, never trust.** A returned timestamp is accepted only if
   it lands inside the meeting's real segment range; out-of-range
   timestamps are dropped with the drop recorded (the model does not
   get to invent provenance).
3. **Projection carries it.** The 01 deriver maps the timestamp onto
   the decision record (`decided_at` upgrades from meeting-date to
   moment, `date_basis` flips accordingly).
4. **Best-effort backfill, labeled.** For existing records, a
   conservative text-anchor pass over the meeting's own segments may
   attach a moment ONLY on an exact-normalized-substring hit;
   anything weaker stays absent. Backfilled moments are labeled
   `anchored`, capture-time ones `reported`.
5. **The jump.** A decision's moment resolves to its segment
   (repository-level: meeting + offset → segment), so 05 can open the
   transcript at the moment. No UI in this story; the resolver +
   route land here.
6. **Aftercare keeps working.** Its existing `source_timestamp`
   resolution (`meeting_aftercare.py:84-119`) is untouched; where a
   decision record exists, aftercare's provenance and the record's
   agree — asserted by test.

## Out of scope

- Any UI (HS-109-05).
- Promotion (HS-109-03).
- Re-running the LLM over the whole archive (backfill is text-anchor
  only; a model pass over years of audio is not this phase).
- Speaker attribution on decisions.

## Acceptance

- A live meeting on real metal produces a decision whose record
  carries a verified transcript moment; the resolver returns its
  segment.
- An out-of-range model timestamp is dropped and the drop is visible
  in the plugin run record, by name.
- A record without a moment renders `date_basis: meeting_date` —
  absence, not invention; zero fabricated timestamps under test.
- Backfill anchors only exact hits; a fuzzy near-miss stays absent
  (test pins one).
- The `anchored` / `reported` distinction is stored and queryable.
- Full suite green; spine byte-unchanged.

## Test plan

- **Unit:** timestamp validation window; anchor exact-hit rule;
  date_basis transitions; resolver offset→segment.
- **Integration:** capture→projection carries the moment; aftercare
  agreement; backfill over seeded archive.
- **Live (evidence):** a real recorded meeting through the real chain
  against `.43` — decision with moment, jump resolved; one honest
  absence shown.

## Chef's notes

- The verification window should tolerate segment-boundary rounding
  (a timestamp equal to the meeting's end is in range). Pin the
  boundary in a test, not a comment.
- Do not let the prompt change regress capture quality: the schema
  addition is optional-field, and the existing golden outputs must
  still parse.
- `.43` proof rule applies (LAN endpooint; sandboxed Bash cannot
  reach it — run live legs with sandbox disabled per house practice).
