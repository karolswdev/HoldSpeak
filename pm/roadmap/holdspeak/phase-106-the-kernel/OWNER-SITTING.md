# HS-106-10 owner sitting

## Open

`http://127.0.0.1:8765?token=beef7b5e`

Hub PID `73454`, running from **main** (includes the beat-7 rider).
Stop: `kill 73454`. Restart from the repo root:
`nohup env HOLDSPEAK_WEB_PORT=8765 .venv/bin/holdspeak web --no-open >/dev/null 2>&1 &`

Desk path: **HoldSpeak → List view → Pull requests → Refresh → #387**.

## Beats

1. **Agent cannot decide**
   - `uv run pytest -q -s tests/integration/test_kernel_real_hub.py::test_real_http_executor_receipt_and_sigkill_cursor_replay`
   - See: `"agent_decide": "principal_right_required"`.

2. **Census names drift**
   - `uv run pytest -q tests/unit/test_kernel_effect_fence.py`
   - See: `7 passed`. Mutation capture in `evidence-story-10.md`.

3. **Operation lifecycle + journal replay**
   - Same command as beat 1.
   - See: submitted `awaiting_decision`; claimed; receipt `succeeded`;
     `cursor_replay_same: true`.

4. **Real pane + gate**
   - #387 → **Send agent**. Instruction:
     `Run printf HS10610_OWNER_APPROVE once, then stop.`
   - Type into the opened session: `Proceed.`
   - **Needs you** → read the full command → **Approve**.
   - Repeat with `...HS10610_OWNER_DENY...` → **Deny**, reason
     `owner sitting deny reason`.
   - See: approved output ran; denied effect absent; the agent receives
     your reason **verbatim**.

5. **Actuator egress**
   - #387 → **Post comment**: `HS-106-10 owner sitting approved egress.`
     → **Propose** → read the full card + `GitHub` badge → **Approve**.
   - Repeat with `...denied egress.` → **Propose** → **Deny**.
   - See: first comment on #387 with a receipt; second absent.

6. **Child operation**
   - #387 → **Send agent**. Instruction:
     `Run git diff --stat origin/main...HEAD exactly once; report and stop.`
   - Type `Proceed.`, then approve the held Bash card.
   - See: a `tool.call` child under the `process.spawn`, with its own
     receipt.

7. **Full PR loop**
   - #387 → **Diff** → **Send agent** (beat 6's instruction) → after the
     work receipt, **Draft review** → **Post comment** → paste the draft
     → **Propose** → read → **Approve**.
   - Open the PR on GitHub.
   - See: the comment landed once; its receipt; spawn/input/tool-child
     receipts all present.

8. **SIGKILL + unknown**
   - `uv run pytest -q tests/unit/test_inference_kernel.py::test_hub_restart_projects_claimed_run_and_desk_state_as_unknown`
   - See: `1 passed`. Machine capture: `sigkill: -9`; kernel receipt
     `indeterminate`; wire state `unknown`; the Desk renders the literal
     word at 1440 and 393.

## Known before you start

- **Beat 7 was broken and is fixed** (PR #397). A kernel-spawned agent is
  now brokered or it does not launch: `process_spawn_not_gated` refuses
  before a worktree, process, or launch record exists. The row carries a
  `GATED` / `UNGATED` badge so the state is never invisible. Beats 4, 6
  and 7 were blocked on that split; they are not now.
- **#387 renders `needs_you=false`** — it is open and passing. All four
  verbs are still available on the row.
- **Two rider receipt comments already sit on #387** (00:12 and 00:16
  from the proof runs). Real noise on a real PR, not something you did.
- **Beat-4 machine latency measured 772.55 ms**, against the Phase-104
  unarmed budget of 250 ms. HS-106-05 measured 84.76 ms on an unloaded
  machine; the closeout ran with eight hubs live. Unresolved — worth
  your eye on whether the send *feels* slow.
- Vitest prints jsdom canvas `Not implemented` diagnostics while green;
  the build prints chunk-size warnings. Both cosmetic.

## The number

Census at phase start: **4 covered of 40**. At close: **4 of 40**.
This phase built the kernel and closed no doors — that was the ladder's
design, and Phase 107 is chartered to move it.
