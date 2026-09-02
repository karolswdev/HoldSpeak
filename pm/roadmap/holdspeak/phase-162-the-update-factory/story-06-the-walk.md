# HS-162-06 - The walk: PV-H04 measured — five minutes to a copyable truth

- **Project:** holdspeak
- **Phase:** 162
- **Status:** done
- **Depends on:** HS-162-04 (rig vs the wire; face legs after 05's functional)
- **Unblocks:** HS-162-07
- **Owner:** unassigned

## Problem

PV-H04: median edit-to-copy under five minutes AND ≥70% generated
content retained. Both numbers MEASURED (the 156/161 stopwatch
discipline), not asserted.

## Scope

- **In:** tests/e2e/test_hs162_update_glass.py: (1) THE STOPWATCH —
  seeded room → draft → one representative human edit → Copy
  Markdown; wall clock per segment into assets/story-06-stopwatch.json,
  bar < 300s; (2) THE RETENTION MEASURE — diff-based: retained
  chars/lines of the generated draft in the copied artifact ≥70%
  (an honest diff metric recorded in the JSON, not a vibe);
  (3) THE DEGRADED LEG — router down ⇒ deterministic draft on glass
  with honest generator provenance, claims still resolve;
  (4) THE PUBLISH LEG — publish → immutability visible (regenerate
  creates a new draft; the published body never changes). Fixture
  legs ×2 deterministic; shots (draft, claims-open-source, marked
  spans, publish state) both viewports into assets/story-06-shots/,
  all >20KB. Real-metal: the .43 model leg from 03 feeds one
  on-glass draft with real inference (marked, skip-clean elsewhere).
- **Out:** scheduling.

## Acceptance criteria

- [ ] Both PV-H04 numbers in the JSON and the story record; bars met.
- [ ] Four legs deterministic ×2; overflow zero; shots >20KB both viewports.
- [ ] The degraded leg proves UPD-003 on glass.

## Test plan

- **E2E:** the four legs; build-first; ×2.
