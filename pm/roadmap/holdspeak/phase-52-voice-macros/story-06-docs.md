# HS-52-06 — Docs: the Voice Macros guide

- **Project:** holdspeak
- **Phase:** 52
- **Status:** not started
- **Depends on:** HS-52-03, HS-52-04
- **Owner:** unassigned

## Problem
Voice macros are a new user-facing capability with a specific promise (deterministic and
editable, not LLM). That promise has to be documented clearly, in product-tense, and the
doc must obey the Phase-51 roadmap-vocabulary guard.

## Scope
- **In:**
  - A "Voice macros" user guide (e.g. `docs/VOICE_MACROS.md`): what they are, that they
    are deterministic and inspectable (contrast with the LLM rewrite), the built-in pack,
    how to add and edit your own in the settings cockpit, the whole-utterance-match
    limitation, and the off-by-default behavior.
  - Link it into the docs index (`docs/README.md`) under the right journey, and add it to
    the README "Where to go next" table if appropriate (keep the index a map, per
    `DOCS_STYLE.md`).
  - Product-tense, no roadmap vocabulary (the Phase-51 guard
    `test_no_user_facing_doc_leaks_roadmap_vocabulary` will fail otherwise). Run the
    `humanizer` skill over the new doc.
- **Out:** new feature work; internal design docs.

## Acceptance criteria
- [ ] `docs/VOICE_MACROS.md` exists: deterministic-vs-LLM clear, built-in pack listed,
      add-your-own walkthrough, limitations + off-by-default stated; every claim grounded
      in the shipped code.
- [ ] Linked in `docs/README.md` (and README "Where to go next" if added); the index
      stays a map.
- [ ] Passes the Phase-51 roadmap-vocabulary guard and the dangling-link / image-ref
      guards (`uv run pytest -q -k "doc_drift or doc_guard or doc"`); `humanizer` run, no
      em/en dashes.
- [ ] `npm run build` n/a; 0 `_built/` tracked.

## Test plan
- `uv run pytest -q -k "doc_drift or doc_guard or doc"`; manual read as a new user.

## Notes / open questions
- This is the dedicated docs story (standing rule: every phase gets one).
- The guard from Phase 51 now protects this doc; keep `Phase 52` / `HS-52-xx` out of it.
