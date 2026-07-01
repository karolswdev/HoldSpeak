# HS-70-07 — Guiding empty states everywhere (no scary blanks)

- **Status:** done
- **Priority:** MED
- **Depends on:** HS-70-02
- **Evidence:** [evidence-story-07.md](./evidence-story-07.md)

## Goal

Nothing about a fresh install should feel empty-and-unexplained. Every primary
surface, when it has no data, states what it is and the single action to take.
An empty product that guides is inviting; an empty product that blanks is
scary. This is a core part of "out-of-the-box won't scare users."

## Scope

- One shared Signal **empty-state** component (glyph + one-line "what this is"
  + one primary action), built on the Phase-69 substrate, `<style is:global>`
  so it paints on JS-injected surfaces.
- Applied to: Home (fresh user), Dictation (no dictations yet → "hold your key
  and speak"), Meetings (no meetings yet → "capture or import your first"),
  the archive/facets when filters match nothing, and the Studio tools' empty
  states where a blank reads as broken.
- Copy follows the owner's rules: labels not manuals, no prose, no reassurance
  sentences (egress is the badge, not a sentence). One action, stated plainly.
- Loading vs. empty vs. error are visually distinct (an empty state must not be
  shown while data is still loading — that misreads as "nothing here").

## Proof required

Screenshots of each primary surface in its empty state with the guiding
component; the load-vs-empty distinction shown (no false-empty flash on a slow
load); copy audited against the no-prose rule.

## Done

Shipped and screenshot-proven. A shared `.empty-state` primitive (glyph + title
+ one guiding line + one action) landed in global.css; the Meetings archive
empty was rebuilt on it in two guiding variants (no-match → Clear filters;
first-run → Start a meeting / Import), fixing the stale "Runtime" copy from
HS-70-05. An audit found the other primary surfaces already guide (Home
subtitles, the Dictation journal + no-match variant, ContextSection's teaching
empty); Studio never empties. Load vs empty vs no-match are distinct. Full suite
3045 passed. See [evidence-story-07.md](./evidence-story-07.md).
