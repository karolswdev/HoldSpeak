# HS-51-04 — Docs: codify the rule in DOCS_STYLE.md

- **Project:** holdspeak
- **Phase:** 51
- **Status:** not started
- **Depends on:** HS-51-02, HS-51-03
- **Owner:** unassigned

## Problem
The scrub (HS-51-02) and the guard (HS-51-03) enforce the rule, but an author
writing a new doc next phase will not know it exists until the guard turns red. The
voice authority should state the rule up front so it is followed by intent, not
discovered by failure. The standing convention also gives every phase its own
dedicated docs story; for a docs-hygiene phase, that story is codifying the policy.

## Scope
- **In:**
  - A rule added to `docs/internal/DOCS_STYLE.md`: user/operator-facing docs speak in
    product-tense and carry no roadmap/process vocabulary. State plainly what is
    **banned** (`Phase <N>`, `HS-<NN>-<NN>`, `PMO`, "closeout", "the current
    roadmap", phase-relative tense) and what is **kept** (product nouns like
    `actuator`/`connector`; named architecture specs `MIR-01`/`DIR-01`; the internal
    corpus under `pm/roadmap/**`, `docs/internal/**`, `docs/evidence/**`, which is
    exempt by design).
  - A one-line pointer to the guard that enforces it
    (`tests/unit/test_doc_drift_guard.py`) so an author who trips it knows where the
    rule lives.
- **Out:** new product docs; restructuring `DOCS_STYLE.md`; the scrub/guard
  themselves.

## Acceptance criteria
- [ ] `docs/internal/DOCS_STYLE.md` carries the rule (banned list, kept list,
      internal-corpus exemption) and points at the guard.
- [ ] The rule matches what HS-51-03 actually enforces (no daylight between the
      written rule and the test).
- [ ] The `humanizer` skill was run over the edited `DOCS_STYLE.md` and its fixes
      applied; doc guards green
      (`uv run pytest -q -k "doc_drift or doc_guard or doc"`); no em/en dashes.
- [ ] `npm run build` n/a (no UI bundle touched); 0 `_built/` tracked.

## Test plan
- `uv run pytest -q -k "doc_drift or doc_guard or doc"`.
- Manual: read the rule as an author about to write a new user guide; it is clear
  what to avoid and what is fine.

## Notes / open questions
- `DOCS_STYLE.md` lives under `docs/internal/`, so it is itself exempt from the
  guard (it must quote the banned tokens as examples). Confirm the guard does not
  scan it.
- Voice: run the `humanizer` skill on the edited `DOCS_STYLE.md` (no em/en dashes,
  plain and direct); it is a required step, not advice.
