# HS-56-04 — Learning + aftercare cards

- **Project:** holdspeak
- **Phase:** 56
- **Status:** done
- **Depends on:** HS-56-02
- **Unblocks:** HS-56-06, HS-56-07
- **Owner:** unassigned

## Problem
The learning loop and meeting aftercare are the product's proudest honest
moments, and both resolve silently: a correction's reach lands in a digest
tab; a wrapped meeting's open items wait at /history. Neither reaches the
user where they are.

## Scope
- **In:**
  - **`learning_event`** broadcast at the journal correct route, **only when
    `taught && similar > 0`** (the honest-reach rule — quiet at N=0), payload
    `{kind, gist, value, similar}`. The `learned` 💡 card: "Learned from you
    — applied *gist*; matches N past dictations", with a "View digest"
    action (opens the Memory digest surface) and dismiss.
  - **`aftercare_ready`** fired from the meeting wrap/save flow (never from
    the GET route): compute the digest once on wrap and broadcast only when
    `not is_empty`, payload `{meeting_id, title, open_total, top_items}`.
    The `present-note` card: "Your meeting left N open items", the top 1–2,
    an "Open aftercare" action (deep-link to the meeting at /history) and
    dismiss.
  - Auto-dismiss timings for these non-actionable-risk cards per the shell's
    spec (pause-on-hover holds them).
- **Out:** milestone/celebrate cards; any change to correction storage,
  reach math, or aftercare computation.

## Acceptance criteria
- [x] A taught correction with reach > 0 broadcasts `learning_event`; a
      correction with reach 0 (or not taught) broadcasts nothing
      (integration tests both ways; the broadcast's reach is asserted equal
      to the route's — one matcher, one number).
- [x] A wrapped meeting with a non-empty digest broadcasts `aftercare_ready`
      once; an empty digest stays silent (tests both ways, plus the
      unfinished-meeting negative — an autosave mid-meeting stays quiet; the
      deferred-intel path hands the same moment over via an observational
      `on_meeting_ready` hook, exploding-observer-safe).
- [x] Both cards render with honest copy, their actions navigate, and they
      respect the shell's queue/dismiss rules (live dogfood 4/4, zero page
      errors, two reviewed screenshots — see `evidence-story-04.md`).

## Test plan
- Integration on both seams (positive + negative); Playwright card pass via
  the broadcasts. Full suite.

## Notes / open questions
- The wrap-flow hook point: where the meeting save completes with intel
  status known — keep the digest computation off the hot path if wrap is
  latency-sensitive (it is not; saving already does DB work).
