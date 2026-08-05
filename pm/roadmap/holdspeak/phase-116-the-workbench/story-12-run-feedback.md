# HS-116-12 — Run feedback

- **Project:** holdspeak
- **Phase:** 116
- **Status:** done
- **Depends on:** HS-116-07, HS-116-11
- **Unblocks:** HS-116-15
- **Owner:** unassigned

## The thesis (the bar)

When a workbench runs, you SEE it happen. The workbench window is
a live mission-control surface for the agent's work: items flip
states in real time, results appear as they complete, the thinking
indicator breathes on the active item, and a receipt lands when the
run finishes. Past runs are browsable in a run history wing with
receipts showing what the agent received, what it produced, and
where it ran. The workbench is ALIVE when the agent is working.

This is the DW Phase 34 multi-agent command center and Phase 36's
live session stream, distilled for the workbench surface.

**Articles served:** VI (honest by construction — progress is real,
not a spinner over a void), IX (proof — the receipt is visible,
the prompt stack is inspectable).

**UI/UX direction:** Study DW Phase 36's live session stream:
tool calls, edits, questions appear in real time. The workbench
doesn't need that granularity (we're not streaming individual
tokens), but the FEELING should be the same: something is
happening, you can see it, you could close your laptop and come
back and it's still there (reconnect-safe). The key visual:
when a run is active, the workbench window's HEAD gets a subtle
scanning indicator (a thin amber bar beneath the title, the same
`LedMeter` treatment used in PersonaChat). Items animate their
state transitions — pending→claimed gets the pulse, claimed→done
gets a brief green flash on the left border.

## Deliverables

1. **Conductor SSE integration.** The conductor needs access to
   the hub's broadcast system. Implementation: the conductor
   module exposes a `set_broadcast(fn)` function. The hub's
   `_startup` hook calls it with the SSE broadcast callback.
   The conductor emits events:

   | Event | Data | When |
   |-------|------|------|
   | `workbench.run_start` | workbench_id, run_id | Run begins |
   | `workbench.item_claimed` | workbench_id, item_id, title | Item picked up |
   | `workbench.item_done` | workbench_id, item_id, result_preview (first 200 chars) | Item completed |
   | `workbench.item_failed` | workbench_id, item_id, error | Item failed |
   | `workbench.run_complete` | workbench_id, run_id, receipt summary | Run finished |

2. **WorkbenchWindow SSE subscription.** The window uses the
   existing RuntimeBus SSE connection (same as the mission
   control conveyor). It filters events by `workbench_id` and
   updates the local state incrementally — no full reload per
   event. The `detail` state gets a `running` flag that drives
   the head scanning indicator.

3. **Head scanning indicator.** When a run is active, the window
   head shows a thin `LedMeter` bar in scanning mode beneath the
   title — the same visual language PersonaChat uses when the
   agent is thinking. When idle, the bar disappears. This is the
   single strongest "alive" signal.

4. **Item state animations.** CSS transitions on the left-border
   color: `transition: border-color 300ms ease`. When an item
   flips from pending to claimed, the border animates from
   transparent to amber. When claimed→done, amber→green with a
   brief glow (`box-shadow: inset 2px 0 8px var(--color-ok)` for
   500ms, then fade). When claimed→failed, amber→red. These are
   compositor-only animations (border-color + box-shadow), well
   within the 60fps budget (Article VIII).

5. **Run history wing.** A SurfaceWings tab "Runs" on the
   workbench window. Content: a `SurfaceLedger` with one row per
   run, most recent first:

   ```
   ┌─────────────────────────────────────────────────────┐
   │ 2h ago  3/3 done  LOCAL  llama-3.3  [completed ●]   │
   │ ↳ constitutional rev 4 · 2 skills · 0 tokens        │
   ├─────────────────────────────────────────────────────┤
   │ 26h ago  2/3 done 1 failed  LAN  gpt-4o  [failed ●] │
   │ ↳ constitutional rev 3 · 1 skill · 1,200 tokens      │
   └─────────────────────────────────────────────────────┘
   ```

   Each row is expandable to show the full receipt: per-item
   results, egress boundaries, error messages, skills injected,
   and the prompt stack snapshot (if saved to disk).

6. **Run button progress.** During a run, the "▸ Run" button
   transforms into a progress indicator: "Running 2/5" showing
   which item is being processed. Uses the same mono typeface,
   same chip shape, amber tone. Disabled during a run. After
   completion, reverts to "▸ Run" with a brief green flash.

7. **Desk notification on scheduled runs.** When the conductor
   completes a scheduled run (not manual), it broadcasts a
   notification event. The Attention drawer shows: workbench
   name + agent avatar, "3/3 items done", egress badge, timestamp.
   Clicking the notification opens the workbench window.

8. **Reconnect-safe state.** If the user closes the browser during
   a run and reopens, the workbench window loads the current state
   from the API (items in claimed state = run in progress). It
   reconnects to SSE and picks up where it left off. The DW
   pattern: "disconnected → retrying → caught up" state announced
   honestly.

## Test plan

- Visual: trigger a manual run on a workbench with 5 items. Watch:
  head scanning indicator appears, items flip pending→claimed→done
  with color transitions, Run button shows "Running 2/5", receipt
  appears in the Runs wing. Total time under 30s for local model.
- Visual: trigger a scheduled run, verify desk notification appears
  in the Attention drawer with the workbench name and result count.
- Reconnect: start a run, close the tab, reopen, verify the window
  shows the correct in-progress state.
