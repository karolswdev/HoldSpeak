# HS-116-13 — Hardening

- **Project:** holdspeak
- **Phase:** 116
- **Status:** done
- **Depends on:** HS-116-03, HS-116-06, HS-116-07
- **Unblocks:** HS-116-15
- **Owner:** unassigned

## The thesis (the bar)

The workbench system handles edge cases honestly: oversized
constitutional context warns before it blows the context window,
concurrent saves don't lose data, skills that exceed budget are
reported not silently dropped, dead inference targets refuse at
the right moment, and the cron weekday mapping is correct. When
this ships, the system is trustworthy — Article VI honest,
Article IX provable.

**Articles served:** VI (honest by construction — limits are stated
where the user meets them), IX (proof — the test suite locks these
claims).

## Deliverables

1. **Constitutional context in the database.** Move from
   `~/.config/holdspeak/constitutional-context.json` to a
   `constitutional_context` table in SQLite (single-row,
   content + revision + hash + updated_at). Benefits:
   transactional consistency, backed up with the DB, no race
   condition on concurrent writes.

2. **Constitutional context size limit.** Refuse content longer
   than 32,768 characters (roughly 8K tokens). The API returns
   400 with the limit stated. The editor shows a live character
   count with a warning above 80% of the limit.

3. **Skill budget visibility.** When skills are injected and some
   are dropped due to the 8KB budget, log a warning with the
   dropped skill names. In the workbench window's skills section,
   show which skills will be injected at the current budget and
   which won't fit.

4. **Skill validation at creation.** Refuse a single skill whose
   body exceeds 8KB at creation time (API returns 400). The user
   learns the limit before the skill is silently ignored at
   runtime.

5. **Constitutional context version history.** Store the last 10
   revisions (content + revision + hash + timestamp) in the DB.
   The editor shows a version dropdown to view (read-only) and
   restore previous versions.

6. **Conductor error reporting.** When a scheduled run fails
   (target unavailable, recipe missing, build error), the error
   is stored as a run receipt with status "failed" and a clear
   error message. The workbench window shows the failed run in
   the run history with the error — not a silent skip.

7. **Test suite.** Backend tests for: constitutional context CRUD
   in DB, size limit enforcement, skill budget drop logging,
   skill size validation, conductor error receipt on dead target,
   cron weekday mapping (Monday=1 in cron, Sunday=0).

## Test plan

- `uv run pytest -q` — all new hardening tests pass.
- Manual: write constitutional context at 80% of limit, see the
  warning. Exceed the limit, see the refusal. Create a 9KB skill,
  see the refusal. Run a workbench against a dead target, see the
  failed receipt.
