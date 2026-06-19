# HSM-7-04 — Profile-effect gate closeout

- **Project:** holdspeak-mobile
- **Phase:** 7
- **Status:** backlog
- **Depends on:** HSM-7-01, HSM-7-02, HSM-7-03
- **Owner:** unassigned

## Problem

The charter's Track H gate is "profile changes measurably alter extraction." It's
easy to claim and easy to fake. This story proves it the way the desktop proved
its own LLM-shaped features: a control-vs-treatment run over one identical input,
changing only the profile, with a defined metric and a recorded delta.

## Scope

- **In:** a control-vs-treatment demonstration — one identical transcript,
  processed under at least two profiles (e.g. Balanced vs Architect / vs
  Incident), everything else held constant; a defined difference metric (artifact-
  type set diff, per-type counts, emphasis ordering); the recorded baseline +
  treatment + delta.
- **Out:** UI. Multi-profile-per-meeting. Tuning profiles to maximize the delta
  (the gate is "measurably different," not "maximally different").

## Acceptance criteria

- [ ] The difference metric is defined before the run (no post-hoc metric).
- [ ] The same input under two profiles produces a **measurably different**
      artifact set, with the metric value for each profile and the delta recorded.
- [ ] The only variable between control and treatment is the profile (model,
      input, settings held constant) — stated in evidence.
- [ ] The demonstration runs on a real Tier-1 device, local, with the
      configuration recorded.

## Test plan

- Manual / device: the control-vs-treatment run on a Tier-1 device; capture both
  artifact sets + the metric.
- Unit: a deterministic-routing assertion (HSM-7-01) backs up that the routing
  differs even before the model runs, so a null delta points at generation, not
  routing.

## Notes / open questions

- "Measurably" needs the metric fixed up front or the gate is a vibe (phase risk).
- If two profiles produce identical artifacts, the routing isn't reaching
  generation — halt and re-examine HSM-7-01's wiring before adding profiles.
- This closes Phase 7; on pass write `evidence-story-04.md` + `final-summary.md`.
