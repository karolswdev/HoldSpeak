# HS-103-02 - The voice guard reads the glass, not just the docs

- **Project:** holdspeak
- **Phase:** 103
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** HS-103-06
- **Owner:** unassigned

## The research finding (the bar)

The same independent audit (2026-07-22) that rated the Desk's OS-ness
found three instances of exactly the prose the project's own canon
bans, rendered live in the glass:

- `web/src/pages/cores/DictationCore.tsx:370` — "Hold to talk, or type
  below — on paper"
- `web/src/pages/cores/DictationCore.tsx:226` — "The pipeline is off —
  speaking here still works on paper"
- `web/src/pages/cores/SettingsCore.tsx:675` — "Values stay on this
  hub — reads show configured or not, never the value"

Constitution Art. VII.1 bans prose/reassurance in the interface; the
POSITIONING canon bans em/en dashes in prose. Two DIFFERENT guards
already exist, and neither covers this: `tests/unit/test_web_vocabulary_guard.py`
scans rendered `web/src` string/JSX literals, but only for banned
TERMS ("intel", "persona", absolute paths) — not dash-prose.
`tests/unit/test_doc_drift_guard.py::test_no_user_facing_doc_uses_dashes_in_prose`
enforces the em/en-dash-in-prose ban, but only over user-facing DOCS —
it never looks at `web/src` at all. The dash rule has a hole exactly
where it matters most: the actual glass the user reads. This is a
real, if cosmetic, self-inflicted violation of the project's own
ratified bar, caught by an external reviewer that neither existing
guard was positioned to catch.

## Problem

There is no guard enforcing the em/en-dash-in-prose ban against
rendered UI strings — the two existing guards each cover one axis
(vocabulary-in-glass, dashes-in-docs) but the intersection
(dashes-in-glass) is unguarded. Fix the gap mechanically and fix the
three named instances it should have caught.

## Scope

- In: extend `tests/unit/test_web_vocabulary_guard.py` (it already has
  the JSX/string-literal scan machinery over `web/src` — reuse that
  scan, add the dash-in-prose rule from `test_doc_drift_guard.py`
  alongside the existing term bans) so ONE pass over `web/src` checks
  both vocabulary and dash-prose. Rewrite the three named lines to the
  composed, dash-free, no-prose form the canon requires. Sweep the
  rest of `web/src/pages/cores/` and `web/src/desk/` for any other
  instances the new rule surfaces — fix what's found, don't just
  satisfy the three named ones.
- Out: rewriting the guard's doc-level rule (keep it — this adds
  glass-level coverage alongside it, doesn't replace it); non-prose
  uses of a hyphen (compound words, ranges) — the guard must not
  false-positive on those; re-litigating what counts as "reassurance"
  language beyond what Constitution Art. VII.1 / POSITIONING already
  define.

## Acceptance criteria

- [ ] The three named lines no longer contain an em/en dash or
      reassurance phrasing; the surrounding UI still communicates the
      same fact, just composed per canon.
- [ ] A new or extended guard test fails on any em/en dash in a
      rendered core string literal (with a narrow, documented
      exception list if truly needed — none expected) and passes clean
      on the current tree after the fixes.
- [ ] The guard runs in the standard test command
      (`uv run pytest -q tests/unit/test_web_vocabulary_guard.py`) and
      is added to whatever CI/pre-commit path the existing vocabulary
      guard already runs in, so it doesn't require a special
      invocation to matter.
- [ ] Full web vitest + tsc + build stay green (the guard is Python;
      confirm nothing else drifted).

## Test plan

- Unit: `uv run pytest -q tests/unit/test_web_vocabulary_guard.py`
  (grown), plus the interior-canon guard suite to confirm no overlap
  regression.
- Integration: n/a.
- Manual / device: n/a — this is a text-content fix, not a layout
  change; a quick screenshot of the three affected surfaces is still
  worth capturing for evidence, not required for correctness.

## Notes / open questions

Decide the guard's scan strategy: parsing JSX string literals via a
simple regex/AST-lite pass (matching the existing interior-canon
guard's grep-based style, per `feedback_no_validation_spikes` — no need
for a full JSX parser) is almost certainly sufficient and keeps the
guard consistent with the rest of the guard suite's mechanism. Record
the chosen approach and any false-positive exceptions in evidence.
