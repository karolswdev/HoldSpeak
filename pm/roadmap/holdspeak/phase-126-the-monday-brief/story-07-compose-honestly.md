# HS-126-07 — Compose honestly

- **Project:** holdspeak
- **Phase:** 126
- **Status:** backlog
- **Depends on:** HS-126-03, HS-126-04, HS-126-05, HS-126-06
- **Unblocks:** HS-126-08
- **Owner:** unassigned

## The thesis (the bar)

The Monday Brief is a deterministic receipt with four fixed sections:
Changed, Broke, Waiting, and Your Decisions. It speaks plainly from selected
evidence. It does not manufacture activity to make an empty day sound useful.

### What changes

1. Compose and persist the four fixed sections from collector output.
2. Render empty Changed as "Nothing material changed." and use equally
   factual empty states for the remaining sections.
3. Derive the headline from the selected, cited items.
4. Permit optional local inference only to polish wording after deterministic
   selection; it may never choose items, alter ranking, or invent content.

## Acceptance criteria

1. Every generated brief has Changed, Broke, Waiting, and Your Decisions.
2. Every non-empty item is traceable to persisted source evidence.
3. Empty Changed renders exactly "Nothing material changed."
4. No-inference generation produces complete, honest output.
5. Enabling local inference cannot add, remove, rank, or substantively change
   selected facts.

## Test plan

- Unit: compose all populated sections from fixed collector fixtures.
- Unit: compose empty collectors and assert exact honest empty copy.
- Unit: compare inference-off and inference-on item identities and priorities.
- Integration: generate and reload a persisted brief with cited items.
