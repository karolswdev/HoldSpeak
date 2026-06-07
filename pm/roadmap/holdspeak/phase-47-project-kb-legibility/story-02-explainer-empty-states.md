# HS-47-02 — In-app explainer + inviting empty states

- **Project:** holdspeak
- **Phase:** 47
- **Status:** done
- **Depends on:** HS-47-01
- **Unblocks:** HS-47-06
- **Owner:** unassigned

## Problem
Both surfaces are bare editors (a key/value grid; a Markdown textarea) behind a
terse `<p>` lede. A user who lands there sees a blank grid and a "Use starter"
button — no plain "what is this / why would I use it / show me an example," and no
inviting empty state. The feature only serves people who already know it exists and
what it does.

## Scope
- **In:**
  - An **in-app explainer** on each surface (per the HS-47-01 model): a compact,
    Signal-styled "what this is / why it helps / a concrete example" header —
    distinguishing **facts** (KB → exact values stamped into templates, no LLM)
    from **context** (`.hs/` → guidance the rewrite LLM reads), and how each shows
    up in output.
  - An **inviting empty state** for each (no rows / no `.hs/` files): a teaching
    state with a one-line value prop, a worked example, and a primary action
    (seed a starter / open the guided flow) — not a blank grid.
  - A tiny **worked-example affordance** (e.g. "see how `{project.kb.stack}`
    becomes text" / "see how `.hs/context.md` shapes a rewrite") so the abstract
    becomes concrete.
- **Out:** the multi-step guided setup (HS-47-03); discovery (HS-47-04); pipeline
  behavior. This story makes the *existing* surfaces self-explanatory.

## Acceptance criteria
- [x] Each surface has an explainer (what / why / example) consistent with the
      HS-47-01 model and accurate per the Phase-46 facts. Facts: "Exact values,
      stamped in word for word" + a `{project.kb.stack}` substitution example;
      Context: "Background the rewrite model reads" + a rewrite-shaping example.
- [x] Each surface has an inviting, teaching empty state with a one-click starter:
      Facts → "Use starter facts"; Context → "Start with an example" (loads an
      unsaved example into the editor). No bare grid/textarea on first visit.
- [x] The premium UX bar is met (Signal eyebrow + display headline + elevated
      surfaces + worked-example panel); reduced-motion safe (`scrollIntoView`
      honors `prefers-reduced-motion`); nothing steals focus (no `.focus()` in the
      bundle — the focus-safe guard passes).
- [x] Behavior unchanged; page-content tests assert the explainer + empty-state
      markers (two new tests); `(cd web && npm run build)` ✓; 0 `_built/` tracked.

## Test plan
- Unit: `uv run pytest -q -k "dictation"`; page-content assertions for the new
  markers.
- Manual + screenshot: open each surface with no data → the empty state teaches and
  invites; with data → the explainer stays out of the way. Capture before/after.

## Notes / open questions
- Reuse the existing "Use starter" path for KB; add the equivalent for `.hs/`.
- Watch the Astro scoped-CSS-on-runtime-DOM trap (the journal fix): any
  JS-injected empty state needs global styles + a screenshot-verify.
