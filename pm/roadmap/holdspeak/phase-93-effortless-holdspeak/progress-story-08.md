# HS-93-08 progress record — The Desk works for every body

**Captured:** 2026-07-16<br>
**Baseline:** `agent/phase-93-close` after the HS-93-01..06 closing slices<br>
**Acceptance status:** done at the owner-rescoped machine-verifiable scope;
physical-device walks parked in BACKLOG candidate Y.

## The semantic Desk

`DeskListView` renders the same Desk as an accessible table — one row per
object (select checkbox, open button, kind, attention, zone), zone chips that
dive, `← All` to surface — consuming only the existing store and world
records. Parity is proven by test: opening a row lands the identical
`pulloutId` a floater click lands, the checkbox toggles the exact selection
ref shift-click toggles (raising the same Ask bar), and a dive narrows rows
to `worldObjects(items, zone)`. The mode is a chrome toggle with
`aria-pressed`, persisted as `?view=list` and `hs.desk.view`. No second
dashboard: the same pull-outs, editors, and windows open in place.

## Scale

The spatial stage bounds rendering at 200 floaters with a `role="status"`
chip naming the truth ("Showing 200 of 995. Search or use List view for
everything."); the List view pages by 100 with focus preserved across pages;
Tools search operates on records, not rendered nodes. The production scale
runner seeds 1,000 mixed primitives through the real DB, boots the real
server, and proves the chip, the pagination, and a needle search-and-open
with zero failed API responses (screenshots in evidence/hs-93-08/).

## Reduce Motion

A consolidated prefers-reduced-motion block completes coverage of the float,
NEW-ring, record-pulse, awaiting-pulse, chat-thinking, routing, and print
animations; window entrance springs honor `useReducedMotion` (the
hold-to-arm progress is deliberately kept — it is the state of a live
press).

## Verification

| Lane | Result |
|---|---|
| List-view parity + semantic assertions + scale Vitest | 13 passed (then full desk suite 148 passed) |
| Full Web gate | architecture guard 120 sources; typecheck; 36 files / 198 tests; production build |
| Production scale runner | seeded 1,000; spatial 200/995 + chip; list 100 → 200; needle found and opened; zero failed APIs |
| Desk lock / product copy / doc drift guards | 33 passed |

Captured runs: [evidence-story-08](./evidence-story-08.md).

## Candidate-Y residue

Physical iPhone/iPad VoiceOver screen-curtain, Dynamic Type, Reduce Motion,
and orientation walks with direct device captures.
