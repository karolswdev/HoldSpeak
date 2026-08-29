# Phase 147 — One-Tap Record: the exit record

Written 2026-08-29 at the close. Chartered and delivered in ONE arc
(2026-08-28 late → 2026-08-29), 7/7, under the owner's open-throttle
directive ("push this as much as you can, without any of my
prompts") with the merge word given in advance via the standing
goal; the shot exhibit is delivered with the close per the standing
law.

## What the owner can do now (the Tuesday answer)

See the 10:00 on the UPCOMING rail. Tap **Record this** — once. The
row wears **ARMED**; the recording is a real Phase-136 one-shot
whose title, duration, and fire time (start − 60 s) were computed
from the event server-side. If the meeting moves, the arm follows.
If it runs long in the calendar, the duration follows. If it's
cancelled, the arm cancels itself by name. If it's already started,
the tap records the remainder. The captured meeting knows which
event it was — **FROM \<SOURCE\> · \<EVENT\>** on the Meetings
surface — and its action items land on the Door with full
traceability. Cancel is two beats on the same row. Every refusal is
named, in place: **ALREADY ARMED / EVENT ENDED / EVENT NOT FOUND**.

## How it went (the arc in one table)

| Story | What shipped | Commit |
|---|---|---|
| Charter | 2 parallel audits → counsel-ruled design (§2b, RATIFY-WITH-CONCERNS, 0 must-fix, 3 absorbed pre-build) → 7 stories | `96c4b01d` |
| 05 snapshot polish | 422 refusals surface at the button; vision pre-filter, zero wasted dispatch | `9c897b5a` |
| 01 the link | 3 link columns + L1 one-live-arm index; server-computed arm verb; 3 named refusals (HTTP+MCP); armed_schedule_id projection; REAL-conductor lifecycle proof | `5cbaf296` |
| 02 the tap | RECORD THIS / ARMED + two-beat Cancel? / in-flow refusals on the rail; new real-hub glass proof; **one-intent-one-row ruling** from the shot cross-read | `37b8dfea` |
| 03 the honest follow | R1 refresh-in-place / R2 nearest-uid rebind / R3 event_removed cancel / X1 live-capture immunity / D3b idempotence; deterministic snapshot UIDs | `0adbf0e6` |
| 04 meeting provenance | pending_calendar_event_id fire seam → meetings row; read-side (HTTP+MCP); origin line with honest degradation | `02d4a8fc` |
| 06 the record book | USER_GUIDE one-tap section (labels verbatim), README sentence, ARCHITECTURE pipeline section (anchors verified) | `3f4ad5fe` |
| 07 walk + close | one-tap walk leg; walk 8/8 ×2; sync round-trip fix; close sweep + counsel; this record | (the close commit) |

## The walk (scripts/door_walk_hs144.py, now 8 legs)

**8/8 PASS, twice**, fresh HOME, no lore, production authorities
only. The new `one-tap` leg: seed two events through the settings
API + the real conductor → RECORD THIS on every event row → ONE
real tap → ARMED, server truth asserted, the 60 s lead read back
from the wire (`next_fire_at` exactly start − 60 s) → the
suppression ruling asserted on the aggregate → two-beat cancel →
the HONEST stale-row refusal (out-of-band arm, stale tap, live L1
guard, **ALREADY ARMED** in-flow) → a linked meeting delivered
through the PRODUCTION SYNC authority wearing the origin line on
the Meetings surface → 393 in a fresh context. Shots + machine
reports in [`assets/story-07-walk/`](./assets/story-07-walk/).

**Honest scope note:** the walk hub is deliberately runtime-less
(no `_start_meeting` on its stub callbacks), so the leg does not
fake a FIRE; the fire → meeting chain is proven by story 01's
real-conductor lifecycle test and story 04's glue test, and the
origin line is walked live via sync — which is exactly how a peer
device delivers a linked meeting.

## Defects found and killed by the process itself

1. **Census fallout mis-attributed by a builder** (05's retirement
   of the registered resolve_placement fallback) — caught by
   orchestrator triage; retired with attribution.
2. **The armed intent rendered twice** on the rail — caught by the
   shot cross-read law; ruled one-intent-one-row; suppressed
   server-side with a unit pin + glass assertion; re-shot.
3. **An extended meeting was invisible to the follow** (projection
   id hashes starts_at only) — caught by the PRE-BUILD design
   counsel; R1 became refresh-in-place before any code existed.
4. **A linked meeting lost its provenance crossing the sync wire**
   (`meeting_state_from_sync_value` violated its exact-inverse
   contract) — caught while constructing the walk's origin leg;
   fixed + round-trip pinned.
5. Four census pins drifted (pure 1:1) — remapped lawfully, zero
   unmatched entries.

## Close verification

- Mid-arc sweep (quiet tree, after 01+05): 6823 passed / 13 failed —
  11 inherited baseline names, 2 = the census drift above, healed.
- Close sweep: recorded in [`evidence-story-07.md`](./evidence-story-07.md)
  with the readable-log pairing; verdict vocabulary per the house
  law.
- Both walk runs green the same day; glass files
  `test_hs144_door_glass.py` + `test_hs145_door_polish_glass.py` +
  the new `test_hs147_one_tap_glass.py` green serially.

## The consolidated ledger (owner-visible)

| Item | Class |
|---|---|
| Adjacent recurring arms colliding on an R2 rebind (L1 refuses the second honestly; re-armable) | design counsel ledger |
| Identical snapshot events collapse to one deterministic uid (projection index already treats them as one) | design counsel ledger |
| Rare pre-read-failure R2→R3 degrade (needs a DB read failure inside one tick; loud `event_removed`, re-armable) | story-03 triage ledger |
| Walk observation: the hs144-era in-world schedule row's STARTS label rendered an odd instant in the walk fixture (pre-existing leg, all assertions green ×2) | recorded note, next polish candidate |
| Phase 146 ledger items NOT touched here: none remain (both snapshot riders SHIPPED as story 05); the no-real-vision-probe moment still stands | carried |
| Phase 145/144 carried items stand unchanged | carried |

## Close counsel

Verdict + dispositions recorded in
[`evidence-story-07.md`](./evidence-story-07.md) and the phase
decision log after this summary was briefed to a fresh Opus counsel
with pointers to the artifacts.

## Standing charter questions

**Will you use this on a tired Tuesday?** Yes — the design counsel's
human-compliance ruling ("the refusal surface is complete, the
visibility surface is complete, the one-tap promise holds") is now
backed by a walk that does the whole journey cold, twice.
**Does it operate with joy?** One tap where there were two clicks
plus hand-retyped times; one row where there were two; feedback in
one re-fetch; refusals that name themselves.
