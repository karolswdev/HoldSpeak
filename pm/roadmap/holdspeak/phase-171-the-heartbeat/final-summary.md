# Phase 171 — The Heartbeat: final summary (DRAFT — stacked on 170; closes on his word)

## What shipped

- **The design (01):** settled-design-heartbeat.md + twelve boards (the
  shade with PROJECTS · quiet · 393; the notification with the swallowed
  state labelled; the dock badge; ⌘K PROJECTS; Rhythm's cadence row ·
  running · quiet · generating · 393; the hub row). Canvas
  https://claude.ai/code/artifact/82c55045-4a19-4990-a8b5-569b91eb8647.
  Counsel RATIFY-W-C — the rulings: one count everywhere (badge = shade
  caption = notification), muted Rooms dimmed with `MUTED` and out of
  every count; the single aggregate builder; the short caption; the
  click action deferred to the bundle; `Generate now` disabled while
  generating; ⌘K capped at 10.
- **The wire (02 · 03 · 05 · 06):** one setting in `cadence_policies`
  (`heartbeat`: sweep every N min · quiet hours · notify off/edge/every ·
  content · mutes); the scheduler stamps `next_evaluation_at`; a THIRD
  conductor loop `HoldSpeakHeartbeat` with its own failure boundary runs
  `evaluate_due` on the cadence (the seam nothing ever called before),
  refreshes the aggregate and writes one `heartbeat.sweep` receipt;
  `run-now`; the needs-you aggregate behind a stale-while-refresh cache
  (`computedAt · stale · sweepId`; the arrival's read is O(1) — Article V);
  the notifier (count-only body, the edge rule, quiet hours held and
  receipted; macOS via `osascript` from the presence child — the click
  target waits for the bundle; Linux via libnotify); the brief regenerates
  once a day before any push; MCP `heartbeat` family (201 tools / 36
  families).
- **The faces (04 · 07 · 02/06):** the shade's PROJECTS section FIRST
  (caption `PROJECTS · N NEED YOU`; rows name · count · WHY · `Open`;
  muted Rooms dimmed with `MUTED` and uncounted; the brief row; the old
  sections absent at zero — `NOTHING MISSED` when all are; polling only
  while open) + the dock badge from the cached aggregate; PROJECTS in ⌘K
  (needs-you desc then name, capped at 10, the chip only above zero,
  searchable, archived absent); Rhythm (the surface titled `Rhythm`: the
  SWEEP row with the cadence gadget, facts and `Run now`; the MONDAY
  BRIEF row — `DAILY 08:00` a fixed token, `Generate now` disabled while
  `GENERATING`; the NOTIFY row — off / on the edge / every sweep, count
  only / room names, the per-Room mutes, `HELD` in quiet hours; the loops
  below; the hub's Rhythm row `EVERY 15 MIN · NEXT hh:mm`); the arrival
  keeps ONE count with muted items under `MUTED N`. Each bounced once by
  the orchestrator and paid; each with its glass rig; the acceptance of
  02/03/04/06/07 proven box by box (the cache read 1.9 ms).
- **The docs (09, DONE):** README's Heartbeat paragraph; the guide's Rhythm
  section shot from the built faces; ARCHITECTURE's conductor loops +
  the sweep's sequence; SECURITY's notification statement; the sidecar
  prose; POSITIONING's names (the Heartbeat, the sweep, Rhythm, the
  shade) — every claim re-verified against the code; zero markers.
- **The walk (08):** `tests/e2e/live171_walk.py` walked his real desk
  (eight shots + the facts ledger): `run-now` receipted (`held: true` in
  quiet hours, 4.4 ms), Rhythm reading `Every 15 min · HELD · QUIET UNTIL
  08:00 · NEXT 13:20 · LAST 13:05`, his one Room in ⌘K's PROJECTS, the
  brief row on the shade, no badge at a count of zero. A banner at a real
  edge after 08:00 is his to see. Zero face defects; two desk truths
  found (above). The second walk, after the fixes: Rhythm's gadgets read
  `EVERY 15 MIN` · `ON THE EDGE | COUNT ONLY`, his one Room's mute
  toggle enabled, `BRIEF` its own caption on the shade, his Room in ⌘K
  with no chip at zero, `NO BANNER (count=0)`, zero defects again.

## Counsel on the built phase (2026-09-05 09:20): RATIFY-W-C

All earlier conditions PAID; two residues of the one-count rule paid the
same hour (`db49a315`): the deck's badges skipped muted items and the
wire's project list counts only unmuted Rooms. S3 (rig seeding via the
DB for the shade/deck) and S4 (board-level assertions on the Rhythm rig)
noted; N1 the tool counts (201 / 36) fixed.

## Found live, paid in the phase

- **His Monday brief is the kernel ledger** — `1839 THINGS · AUG 19` on
  his shade, seventeen days stale. The brief's collectors emitted kernel
  operations as owner items (170 filtered them client-side); 06 pays it
  at the source: only human items count, the ledger a separate summary.
- **A caption over nothing** — with no Room needing him, his shade showed
  `PROJECTS` over just the brief row; the brief gets its own `BRIEF`
  caption and PROJECTS is absent (the quiet board).
- **Quiet hours held the walk's sweep** at 07:05 (`held: true`,
  `HELD · QUIET UNTIL 08:00` on Rhythm) — honest; his banner's edge is
  after 08:00.
- The presence child's notification path is `osascript` (no PyObjC
  bridge in the venv; UNUserNotificationCenter refuses an unbundled
  process) — the click target waits for the bundle (BACKLOG).
- The 170 hub rig's cold assertion learned the default sweep
  (`EVERY 15 MIN`, never `NO LOOPS` on a fresh install).

## The suite

- Full suite, CI shape (-n auto), after everything (10:30): **9501 passed /
  98 skipped / 14 failed → 6 inherited** (unchanged since 170: ask
  grounding ×2 + the ask runner need his real gguf under an isolated HOME;
  the kernel broker's two density fences; the product-copy drift at 27) +
  4 xdist-only (141 thought workbench, 144 deep link, 153 slash, 4/4 green
  alone) + 4 branch-new, paid: the allow-list sizes (+ `heartbeat.status`),
  web_runtime's density budget (the heartbeat thread's start carved into
  its mixin), the effect census (the receipt writers classified), the
  cadence smoke test's `/status` read restored on Rhythm.
- vitest green; web baseline zero branch-new; the ratchet at its floor
  (A8 26 ≤ 28); product-copy 27 (the parked faces skipped).
- Rigs green serially: rhythm (7) · shade (12) · command deck (6) + 170's
  arrival/settings/concierge/speak/meetings + 144 + 169 Room.

## What the owner owes the phase

1. His word on 170 (PR #553) — this phase is stacked on it.
2. His word on this canvas and his walk: a notification he receives.
3. His three answers: the notification's click target; one flat interval
   or active/idle; whether mute hides a Room from the shade (ruled for V0:
   dimmed and shown, out of every count — his to overrule).

## Found after the close (2026-09-05, by the 174 runner lane) and paid here

`heartbeat_notify` — the notification decision (count-only body, the
edge rule, quiet hours held) — had no caller in the conductor loop; only
the MCP `heartbeat.notify_test` reached the OS notifier. The phase's
promise (a banner on the edge of the count) never fired from a sweep.
Paid: `run_sweep` now runs the decision in its own failure boundary
after the sweep receipt (`heartbeat_service.py` `_run_notification_
decision`), receipts `heartbeat.notify` as `sent | held_quiet_hours |
held_no_edge | off | error`, and persists `last_notified_count` on the
heartbeat settings row so a restart never re-notifies the same count;
`every_sweep` fires on any non-zero count. Six tests. **Law (from 172):
a new entry point needs a production call site and one test through
the real seam — the 171 rigs tested the notifier directly and missed
the loop.**
