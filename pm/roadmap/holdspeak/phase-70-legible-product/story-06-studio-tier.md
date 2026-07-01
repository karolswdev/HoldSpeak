# HS-70-06 — The Studio tier: the power features, framed and contained

- **Status:** done
- **Priority:** MED
- **Depends on:** HS-70-01
- **Evidence:** [evidence-story-06.md](./evidence-story-06.md)

## Goal

Give the six power features one coherent, clearly-secondary **Studio** home so
they are discoverable when a user is ready and invisible when they are not. A
first-run user never gets dumped into Workbench or Cadence and asks "what is
this and why."

## Scope

- A **Studio index** (a landing that the collapsed nav group opens to): each
  tool as a framed card — Workbench, Agent Desk (`/companion`), Cadence,
  Commands, Profiles, Presence — with a one-line "what this is for" and its
  on/off / configured state where relevant. This is the map for the advanced
  tier.
- The tools keep their existing routes and behavior unchanged (Decision B: they
  are grouped and framed, not re-implemented). Cadence and Presence and the
  actuator/connector-backed tools stay **off by default** exactly as today.
- Framing copy states what each is for in canonical, no-prose terms (labels,
  not manuals) — consistent with the owner's "no prose in the UI" rule.
- Studio reads as advanced: visually distinct from the two-mode front door,
  never competing with Dictation/Meetings for a new user's attention.
- Honest state: a tool that is off/unconfigured says so plainly on its card
  (no fake readiness).

## Proof required

Screenshot of the Studio index (all six tools framed with their state); each
tool still opens and works from Studio; off-by-default tools shown off; a
first-run user's path never lands here (verified against HS-70-03).

## Done

Shipped and screenshot-proven. A new `/studio` index frames the six power tools
(Workbench, Desk, Agent Desk, Cadence, Commands, Profiles) as clearly-secondary
`.signal-card`s — glyph + one-line purpose + "Open →", with an honest "Off by
default" chip on Cadence. The nav dropdown's "ADVANCED" eyebrow became a link to
`/studio`; `studioActive` lights the summary on `/studio`; the tools keep their
own routes (framed, not re-implemented). Registered in pages.py + PAGE_ROUTES;
route pre-flight 2 passed; full suite 3045 passed. See
[evidence-story-06.md](./evidence-story-06.md).
