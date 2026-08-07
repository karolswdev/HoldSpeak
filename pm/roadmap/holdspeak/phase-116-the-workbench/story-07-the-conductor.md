# HS-116-07 — The conductor

- **Project:** holdspeak
- **Phase:** 116
- **Status:** done
- **Depends on:** HS-116-01, HS-116-03, HS-116-06
- **Unblocks:** HS-116-08
- **Owner:** unassigned

## The thesis (the bar)

Workbenches wake up on schedule, run through their items, and
produce receipts — without the owner touching anything. Each
scheduled run is a fresh, isolated session (the Hermes pattern:
no history inheritance, explicit context only). The conductor
handles scheduling, item claiming, agent invocation, result
persistence, and receipt generation. When this ships, a workbench
set to `0 2 * * *` wakes at 2 AM, works its pending items, and
leaves the owner a morning receipt.

**Articles served:** V (consent — overnight runs produce proposals,
never fait accompli; anything that types/sends/files requires a
pending approval), XI (kernel — every scheduled run is admitted,
every item attempt is a child operation with a terminal receipt),
III (egress — the receipt records where inference actually ran).

## Deliverables

1. **Scheduler.** A lightweight scheduler that runs inside the
   HoldSpeak hub process. On hub start, it loads all workbenches
   with `schedule_enabled = true` and registers their cron
   expressions. Every 60 seconds it checks for due workbenches
   (Hermes gateway pattern). The scheduler claims a workbench run
   (prevents concurrent runs of the same workbench), invokes the
   conductor, and releases the claim on completion.

2. **Conductor loop.** For each due workbench:
   - Load the workbench config (recipe, target, schedule).
   - Assemble the prompt stack: constitutional context (revision +
     hash) → recipe system prompt → active skills → item.
   - For each pending item (by priority order):
     - Claim the item (status → claimed).
     - Invoke the recipe's chat endpoint with the assembled prompt
       and the item's body + grounding as the user message.
     - Persist the result on the item (result markdown, result
       egress, tokens consumed).
     - Flip the item status (done or failed).
   - Generate a run receipt: items attempted, completed, failed,
     total tokens, egress boundary, model used, duration, timestamp.

3. **Fresh session isolation.** Each scheduled run is a fresh
   session. No chat history from previous runs or manual
   interactions. The only context is the prompt stack + item
   grounding. This matches Hermes's explicit design: a cron run
   starts clean. Mid-session memory writes (skill proposals) are
   persisted to disk but do not mutate the current run's prompt.

4. **Wake gate.** Before invoking the model, the conductor checks
   whether work exists (pending items with status = pending). If
   no pending items, the run is skipped with a no-op receipt
   (Hermes `wakeAgent: false` pattern). No tokens consumed for
   an empty workbench.

5. **Run receipt persistence.** Receipts are stored in a
   `WorkbenchRunRecord` table: `id`, `workbench_id`, `started_at`,
   `completed_at`, `items_attempted`, `items_completed`,
   `items_failed`, `total_tokens`, `egress_boundary`, `model`,
   `constitutional_context_revision`, `constitutional_context_hash`,
   `skills_injected` (JSON array of skill IDs + versions).

6. **Run receipt surface.** The workbench window shows a "Last run"
   section in the footer that expands to the full receipt. The
   receipt is also available as a desk notification (RuntimeBus
   SSE event).

7. **Manual trigger.** The "Run now" verb in the workbench toolbar
   invokes the same conductor loop immediately, outside the
   schedule. Same isolation, same receipt.

## Test plan

- `uv run pytest -q` — scheduler fires on cron match, conductor
  processes items in priority order, fresh session (no history
  bleed), wake gate skips empty workbenches, receipt records all
  fields, concurrent run prevention.
- Integration: create a workbench with two items and a manual
  trigger, run it, verify both items have results and the receipt
  is complete.
