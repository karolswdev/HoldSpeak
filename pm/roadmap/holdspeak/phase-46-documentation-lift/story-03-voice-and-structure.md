# HS-46-03 — Docs voice & structure system + elevated index

- **Project:** holdspeak
- **Phase:** 46
- **Status:** done
- **Evidence:** [evidence-story-03.md](./evidence-story-03.md)
- **Depends on:** HS-46-01
- **Unblocks:** HS-46-05
- **Owner:** unassigned

## Problem
The 13 guides (4,677 lines) were written across many phases with different tone,
structure, and entry points — they read like an anthology, not one product. The
index (`docs/README.md`, 64 lines) is a flat list, not a map. A reader can't
predict where a guide starts, what voice it speaks in, or how to navigate the set.

## Scope
- **In:**
  - A short **docs style guide** (`docs/internal/DOCS_STYLE.md` or a section in
    `CONTRIBUTING.md`): the **voice** (direct, confident, honest, second-person),
    the **standard page skeleton** (one-line what + why → quickstart/TL;DR →
    reference → troubleshooting → "see also"), the **privacy/local-first callout**
    pattern, cross-link conventions, and the heading/anchor rules the link-check
    enforces.
  - **Apply the skeleton + voice** across the user-facing guides (Getting
    Started, Intelligent Typing, Meeting Mode, Models, Dictation Copilot, the
    AIPI workflow) — add a crisp lede + a "see also" footer, unify tone, fix
    structural inconsistencies. *Reference/dev docs* (Plugin Authoring, Connector
    Development, Device Protocol) get accuracy + a consistent header/lede, not a
    rewrite (default; revisit depth per the phase's deferred decision).
  - **Elevate `docs/README.md`** into a real **map**: grouped by journey (Start
    here · Dictate · Meet · Extend · Operate/Trust), each entry a one-line value
    prop, scannable in seconds.
- **Out:** the README (HS-46-02); visuals (HS-46-04); factual fixes (HS-46-01,
  consumed here). Voice + structure + navigation.

## Acceptance criteria
- [ ] A docs style guide exists (voice + the standard page skeleton + callout +
      cross-link/anchor conventions).
- [ ] The user-facing guides carry a consistent lede + structure + "see also";
      tone reads as one product, not 13 phases.
- [ ] `docs/README.md` is a journey-grouped, scannable map (not a flat list),
      each entry with a one-line value prop.
- [ ] Dangling-link/anchor + doc-drift guards green (no broken cross-links from
      the restructure).

## Test plan
- Unit: `uv run pytest -q -k "doc_drift or link"`.
- Manual: read three restructured guides back-to-back; confirm the skeleton + a
  consistent voice; confirm the index reads as a map.

## Notes / open questions
- Don't homogenize away useful per-doc structure — the skeleton is a floor, not a
  cage (reference docs keep their depth).
- Coordinate with HS-46-02 so the README's "where to go next" table and the docs
  index map don't contradict each other (same journeys, same names).
