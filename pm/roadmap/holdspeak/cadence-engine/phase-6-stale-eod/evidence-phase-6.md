# Evidence — Cadence Phase 6 (stale-loop escalation + EOD closure)

**Date:** 2026-06-28. **Branch:** `holdspeak/cadence-phase6-closeout`.

## What shipped

| Story | Files | Proof |
|-------|-------|-------|
| CAD-6-01 | `cadence/closeout.py` (`escalation_severity`) | `test_cadence_closeout.py` |
| CAD-6-02 | `build_closeout` + `_recommend` + `render_closeout_text` | closeout recommendation tests |
| CAD-6-03 | `apply_decision` (+ delegate) + `POST /closeout/apply` | apply + route tests |
| CAD-6-04 | `db/cadence.py` `list_nudges` + `GET /history` | `test_history_lists_nudges` |
| CAD-6-05 | CLI `closeout`, Telegram `/closeout`, page Closeout + History sections | CLI test + bundle builds |
| CAD-6-06 | `test_cadence_closeout.py` + route additions | 171 green |

## The ritual

A sample `holdspeak cadence closeout` (a fresh owned loop, an old unowned loop, a proposal):

```
End-of-day closeout — 2026-06-28

3 open · recommended: approve×1, kill×1, snooze×1

      approve  Approve me   — A proposal is ready for your approval.
      snooze   Owned fresh  — Not today — snooze until it matters.
  [E] kill     Unowned old  — Open for days, still unowned — kill it or own it.
```

- **Escalation** (`escalation_severity`) raises a loop to `persistent` (≥3 nudges / ≥2 days) then
  `escalated` (≥6 / ≥4); `needs_review` stays `quiet`.
- **Recommendations** are deterministic per loop; **batch-apply** (`POST /closeout/apply`) mutates
  the lifecycle (snooze/kill/close/delegate) in one call and skips non-applyable actions
  (file/approve/reply open a draft elsewhere). `apply_decision` refuses unknown actions / missing loops.
- **History** (`GET /api/cadence/history` via `list_nudges`) lists recent nudges; the page renders a
  Closeout section (recommended-action badge + severity ring + one-tap apply) and a History list.

## Trust boundary held

`apply_decision` and the closeout builder are pure cadence-core operations (lifecycle writes only);
the cadence-core no-external-side-effects guard still passes.

## Proof

- `uv run pytest -q tests/unit/test_cadence_*.py tests/integration/test_cadence_*.py
  tests/integration/test_web_server.py` → **171 passed.** `cd web && npm run build` → 15 pages.
