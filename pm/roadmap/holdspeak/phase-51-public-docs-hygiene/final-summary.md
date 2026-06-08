# Phase 51 — Public-Docs Hygiene: final summary

**Status:** CLOSED (5/5). Opened and closed across 2026-06-07 / 2026-06-08 on user
direction, the cheap release-facing follow-on to Phase 50. Net-new from a
between-phases conversation, captured as [backlog](../BACKLOG.md) candidate H.

## The thesis

Phase 50 cut the release gate, so strangers now install HoldSpeak from the public
repo. But the deeper user and operator guides still narrated the product by its build
history: "Phase 9 shipped the connectors", "Periodic tick (HS-17-05)", "the HS-19
closeout", "the current roadmap". That roadmap vocabulary means nothing to a new user
and reads as half-finished. This phase removed it, rewrote phase-relative claims into
product-tense, and locked the clean state so it cannot come back. Docs and test only;
no product behavior changed.

## What shipped, story by story

- **HS-51-01 — Leak inventory.** `leak-inventory.md`: every offending line in the
  user-facing docs, classified banned vs keep, with a product-tense rewrite each, plus
  the fixed scope and the guard pattern. The full grep found more than the
  scaffold-time list (`SECURITY.md`, `PLUGIN_AUTHORING.md`, an asset readme also
  leaked; the root README was already clean).
- **HS-51-02 — Scrub.** All 6 in-scope guides (`DEVICE_PROTOCOL`,
  `CONNECTOR_DEVELOPMENT`, `SECURITY`, `RELEASING`, `INTELLIGENT_TYPING_GUIDE`,
  `PLUGIN_AUTHORING`) plus the optional asset readme rewritten into product-tense.
  `MIR-01`/`DIR-01` spec names kept. A case-insensitive re-grep before scrubbing caught
  5 lowercase-only leaks the inventory grep missed, which set the case-insensitive
  requirement for the guard. The `humanizer` skill cleared all 15 rewrites.
- **HS-51-03 — The guard.** Three case-insensitive tests in
  `tests/unit/test_doc_drift_guard.py`: a scanning guard over the user-facing docs
  (root README + non-recursive `docs/*.md`; internal, evidence, and assets out by
  construction), a non-vacuity sanity test, and a pattern-narrowness test proving
  `MIR-01`/`DIR-01`/`WFS-01` never trip. Proven red on a planted violation.
- **HS-51-04 — The rule.** A "Product-tense, not roadmap vocabulary (guard-enforced)"
  section in `docs/internal/DOCS_STYLE.md` with no daylight from the guard, so authors
  follow it by intent. Its example tokens sit in `docs/internal/`, so the guard ignores
  them.
- **HS-51-05 — Closeout.** This summary, the dogfood, the suite, the PR.

## Exit evidence

- Dogfood (`dogfood.sh` + `dogfood-transcript.txt`, RESULT: PASS): the guard is green
  on the clean tree, the in-scope grep is empty, a planted lowercase "phase 99" turns
  the guard red with a `path:line` offender, and revert turns it green with the tree
  clean.
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` -> 2454 passed, 17
  skipped (the +3 over Phase 50 is exactly the three new guard tests).
- `npm run build` n/a (no UI bundle touched); 0 `_built/` tracked.

## Decisions worth remembering

- **Scope: user-facing only.** `README.md` + `docs/*.md` are in. The internal corpus
  (`docs/internal/`, `docs/evidence/`, `docs/assets/`, `pm/roadmap/`) keeps its
  phase/story vocabulary by design and is never scrubbed or scanned. Reusing the
  existing `_live_docs()` helper would have been a permanent red, because it includes
  `docs/internal/`.
- **The guard is case-insensitive** because real lowercase leaks existed.
- **Honest limitation.** The guard catches numbered/tagged leaks. Bare process-speak
  with no number ("a separate phase") is on the human scrub and the reviewer; a bare
  `\bphase\b` pattern would false-positive on "a phased rollout" (asserted as a
  non-match).

## Not done (by design)

- A full em-dash purge of the guides. The scrubbed lines carry no em dashes, but the
  pre-existing ones elsewhere are out of this phase's thesis.
- Bare-`phase` prose detection in the guard (see the honest limitation above).

## Next

No follow-on required. The strongest remaining product bet in the backlog is **B**
(voice macros), and pairing it with a scoped slice of **E** (carve only the routing
seam the macros land on) is the way to ship a codebase improvement with a feature
under one thesis. Recorded in the BACKLOG sequencing note.
