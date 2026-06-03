# Evidence — HS-32-06 (Stale non-PMO doc sweep + drift guard)

**Shipped:** 2026-06-02. Reconciled the non-PMO docs that asserted false *current*
state, removed the vestigial `web_enabled` flag, and committed a lightweight guard
so the worst doc-rot (false stub counts) can't return. Phase-closing story.

## Doc-truth fixes

- **The stub-count rot (the worst drift).** `docs/PLAN_ARCHITECT_PLUGIN_SYSTEM.md`
  listed 4 built-ins as "⚠️ **stub** (`DeterministicPlugin`)" while its own
  "Reality status" note (and `test_no_deterministic_stub_remains`) say **zero**
  stubs remain. Fixed all 4 markers → "✅ **shipped** (real `run()`; phase 29
  rollout)". A scan confirmed no other live doc carries a false stub claim (the
  one remaining `DeterministicPlugin` mention is a *true historical* phase-16 line
  in the PMO README, kept verbatim).
- **Dead branch header.** `docs/PLAN_INTEL_STREAMING.md`'s `**Branch:**
  feature/intel-streaming` (a branch that no longer exists; the feature shipped) →
  a `**Status:** ✅ shipped` note. No other dead `Branch:` header remains in `docs/`.
- **Retired-TUI/menubar reconciliation** (deferred from HS-32-07):
  - `PLAN_PHASE_WEB_FLAGSHIP_RUNTIME.md` already got a superseded banner in HS-32-07.
  - `PLAN_MEETING_MODE.md` + `PLAN_MEETING_INTEL_PI.md` got a one-line "historical
    plan — the TUI was retired in HS-32-07" banner (they have whole TUI sections).
  - `PLAN_PHASE_MULTI_INTENT_ROUTING.md` (canon) and `RELEASE_HARDENING_CHECKLIST.md`
    are left as-is — their TUI lines are historical *requirements*/a dated
    checklist ("present web flows before TUI", "[x] TUI settings expose…"), not
    false current-state claims.
- **`HANDOVER.md` refreshed.** Its TL;DR was badly stale (PR #7 "not merged",
  Phase 31 "awaiting merge", Phase 32 "0/6 not started"). §1/§2/§3 now state
  reality: Phase 31 **merged**, Phase 32 **DONE (7/7)** on an unpushed stacked
  branch, the TUI/menubar gone, the doc drift guard noted.
- **Root `README.md` positioning** reviewed — already accurate post-HS-32-07
  (lede spans voice-typing + meeting mode + agents + companion; "web dashboard",
  no TUI/menubar; the platform table's "Menu bar mode" row was removed in HS-32-07).
  No change needed.

## Vestigial `config.meeting.web_enabled` removed

Made dead by HS-32-02 (`MeetingSession` stopped reading it) + HS-32-07 (the TUI
Settings toggle was deleted with the TUI). Confirmed **no code reads it**, then
removed:
- `holdspeak/config.py` — the dataclass field.
- `tests/unit/test_config.py` — the 3 assertions/usages (+ cleaned a pre-existing
  unused `Path` import in the file).
- `docs/MEETING_MODE_GUIDE.md` — the config JSON example line and the config-table row.
- `web/scripts/capture-gallery.py` — the `web_enabled: true` key in the screenshot
  mock-state object.
- Left in `docs/PLAN_MEETING_INTEL_PI.md` (a historical code snippet, now bannered).

## The drift guard — `tests/unit/test_doc_drift_guard.py`

- `test_no_live_doc_claims_a_deterministicplugin_stub`: scans every `docs/*.md`
  (excluding `docs/evidence/` snapshots — the PMO record stays verbatim) for the
  `**stub** (`DeterministicPlugin` pattern and fails with the offending file:line.
  Pairs with the code-level `test_no_deterministic_stub_remains`.
- `test_drift_guard_actually_scans_docs`: sanity (sees >5 docs incl. the RFC) so a
  green result isn't vacuous.
- **Verified it catches the rot:** re-introducing one "⚠️ stub" marker turned the
  guard **red**; reverting → green.

## Verification

- `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **1954 passed, 14
  skipped** (+2 drift-guard tests; config tests lost 3 assertions, no tests
  removed). Changed files ruff-clean.
- The drift guard + the existing `test_no_deterministic_stub_remains` together
  lock the zero-stubs reality at both the code and doc levels.
