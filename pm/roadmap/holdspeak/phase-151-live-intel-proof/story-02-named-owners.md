# HS-151-02 — The named-owner intel (the prompt learns people)

- **Project:** holdspeak
- **Phase:** 151
- **Status:** ready
- **Depends on:** —
- **Unblocks:** HS-151-03
- **Owner:** unassigned

## Problem

The intel prompt (holdspeak/intel/parsing.py:16-46) constrains
owners to "Me|Remote|null" — designed pre-150, person-blind by
construction. The delegation lane exists to answer waiting-on-WHOM,
and the model demonstrably emits real names when allowed (probe 2).
Today the product actively steers its own intelligence away from
the manager suite's whole point.

## Scope

### In

1. The prompt's action_items owner shape becomes
   `"owner": "<person's name as spoken>|Me|Remote|null"` with one
   tight instruction line: name the owner ONLY when the transcript
   names them; Me = the speaker/leader; Remote = the counterpart;
   null when unclear. COUNSEL M3: the prompt states Me/Remote are
   the ONLY reserved tokens — every other string is a literal
   person name. COUNSEL M4: prompt and the story-01 schema
   constant update TOGETHER (one shape, all consumers). No other
   prompt changes.
2. Parsing pins for the messy reality (_coerce_action_items):
   names pass through verbatim (strip only); "null"/""/None → None
   (already); NEW pins for "Me"/"Remote" casing variants arriving
   from real models (pass through — the 150 reserved contract
   handles them downstream) and for a multi-word name.
3. The 150 interplay pins (read-only assertions, no product
   change): a named owner from intel shows map… on the Door
   (unmapped) and maps through the normal gesture; "Me"/"Remote"
   stay unmappable (isReservedOwner); person_overlay counts a
   mapped intel-born card.
4. If any story-01 schema source-of-truth exists by then, the
   named-owner shape flows into the response_format too (one
   shape, two consumers) — coordinate through the orchestrator,
   not by editing story-01 files blind.

### Out

- Any normalization/fuzzy matching of owner strings (the contract
  forbids inference; multiple aliases per person is the answer).
- UI changes.

## Acceptance criteria

1. Prompt emits the named-owner schema; goldens updated.
2. The parsing + interplay pins green.
3. A canary extraction against the stub server (story-01's)
   round-trips a named owner into an action_items row with
   review_state=pending.

## Test plan

Focused: intel parsing tests, the canary, the interplay pins.
