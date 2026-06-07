# Evidence — HS-46-03: Docs voice & structure system + elevated index

**Date:** 2026-06-07. **Author:** Claude (Opus 4.8 session).
**Branch:** `phase-46-documentation-lift`.

## What shipped

A shared **voice + page skeleton** the 13 guides now clear, a **uniform `## See
also` footer** across the whole user-facing set, and the docs index rebuilt as a
**journey map** — so the set reads as one product, not an anthology.

### The style guide

`docs/internal/DOCS_STYLE.md` — the floor every guide clears:

- **Voice:** direct, second-person, confident, honest-over-hype (canon wins over a
  drifted doc); a consistent term glossary (*dictation*, *meeting mode*, *the
  dictation pipeline*, *intel*, *actuator*, *desktop presence*).
- **The page skeleton:** Title → **lede** (what + why) → quickstart/TL;DR →
  reference → troubleshooting → **`## See also`**. A floor, not a cage — reference
  docs keep their depth.
- **The privacy/local-first callout** pattern (one shape everywhere; SECURITY.md is
  authoritative, guides summarize + link).
- **Cross-link & anchor rules** the link-check enforces — relative links only; the
  GitHub slugger anchor rule (carried from the HS-46-01 finding); the exact `## See
  also` footer format (heading + link + em-dash + one-line value prop).

### Footers unified across all 13 docs

Standardized on **`## See also`** — renamed the two inconsistent ones
(USER_GUIDE's "Related Docs", DICTATION_COPILOT's "Where to go next") and added a
footer to every guide that lacked one. Now present in: Getting Started, User
Guide, Intelligent Typing, Meeting Mode, Models, Dictation Copilot, AIPI-Lite
Workflow, Plugin Authoring, Connector Development, Device Protocol, Agent Hook
Install, Security, Firefox Extension — **13/13**. No `Related Docs` / `Where to go
next` strays remain.

### The index is now a map

`docs/README.md` rebuilt from a flat list into a **journey-grouped map**: **Start
here · Dictate · Meet · Extend · Operate & Trust**, each entry a one-line value
prop. Journeys + names kept in lockstep with the README's "Where to go next" table
(HS-46-02). The internal section now also surfaces `DOCS_STYLE.md` +
`DOC_AUDIT_2026-06.md`.

## Voice/structure: leave the depth alone

Per the story, this is voice + structure + navigation, **not** a line-by-line
rewrite. Ledes were already crisp on most guides and were left as-is; reference
docs (Plugin Authoring, Connector Development, Device Protocol) kept their deep
structure and got the consistent footer only. No prose was homogenized away.

## A guard catch worth recording

The dangling-link guard scans inside code fences. The style guide's *example*
`## See also` snippet first used `./MODELS.md`, which doesn't resolve from
`docs/internal/` → red. Fixed honestly: the example now links real **siblings** of
the style guide (`DOC_AUDIT_2026-06.md`, `PLAN_ARCHITECT_PLUGIN_SYSTEM.md`), so the
bare-filename form both resolves *and* correctly demonstrates sibling linking, with
a note on the `../` / `internal/` directions.

## Tests run

- Story test plan: `uv run pytest -q -k "doc_drift or link"` → **7 passed, 1
  skipped** (every new cross-link + the rebuilt index resolve; the plugin-count
  guard still green).
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **2364 passed,
  17 skipped** (exit 0).

## Acceptance criteria

- [x] A docs style guide exists (voice + the standard page skeleton + the privacy
      callout + cross-link/anchor conventions).
- [x] The user-facing guides carry a consistent lede + structure + `## See also`;
      tone reads as one product (13/13 footers unified).
- [x] `docs/README.md` is a journey-grouped, scannable map (Start here · Dictate ·
      Meet · Extend · Operate & Trust), each entry a one-line value prop.
- [x] Dangling-link/anchor + doc-drift guards green (no broken cross-links from the
      restructure).
