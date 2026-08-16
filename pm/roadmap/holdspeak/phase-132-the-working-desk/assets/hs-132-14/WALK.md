# HS-132-14 — The walk

Run 2026-08-15, macOS 15 / Chromium (Playwright), against a real hub booted
by the harness on an isolated `HOME`, at 1440x900 and 393x852.

**Result: 115 assertions passed, 0 failed, 50 screenshots, 3 findings.**
Zero console errors on every walked path, both widths.

## The harness

- `scripts/walk_working_desk.py` — hub lifecycle (boot / seed / populate /
  health / reap), the `Shooter` (screenshot + console-error assertion), the
  CLI.
- `scripts/walk_working_desk_legs.py` — one function per surface; each leg
  owns its shots and its assertions.

Rerun from a clean checkout:

```bash
cd web && npm run build && cd ..
HOME=$(mktemp -d) \
PLAYWRIGHT_BROWSERS_PATH=~/Library/Caches/ms-playwright \
  uv run python -m scripts.walk_working_desk walk
```

`--only <leg>` runs one leg (`desk`, `workbench`, `intelligence`,
`placement`, `live`, `cadence`, `ask`, `write-receipt`); `--hub-url` drives an
already-running hub; `--out` redirects the shots. Exit code is non-zero when
any assertion fails. The harness picks a free port, records the hub PID, and
reaps it in a `finally` — it never touches 8765, 8788 or 8799.

### What the harness stands in for, and what it does not

Honesty note, because two things cannot run headless on this machine:

1. **The capture engine.** A live meeting needs a microphone: the only
   `segment` emitter is `holdspeak/meeting_session/transcribe_loop.py:277`
   and the only `intel_token` emitter is
   `holdspeak/meeting_session/intel_admission.py:456`. There is no HTTP route
   that injects a transcript segment. So the harness plays the desktop
   runtime's role — it starts a REAL meeting through `POST /api/meeting/start`
   and pushes the REAL frame vocabulary through the REAL `server.broadcast`.
   Socket, bus, frame registry, LiveCore, `POST /api/bookmark` and its
   confirmation are all the product. Only audio→text→intel is stood in for.
2. **Two fixtures with no HTTP mint route.** A decision record
   (`DecisionRecordService`, reachable only from MCP) and a recorded meeting's
   action items (`db.meetings.save_meeting`) are written through the
   product's own services in `_populate`, the same code paths the MCP tools
   and the capture pipeline call. Everything else the walk needs — the desk
   seed, the workbench item, the brief, the cadence tick, the destination, the
   settings writes — goes over HTTP.

Screenshots are real PNGs of the live product; there are no DOM fixtures.

## Shot index

| File (`-1440` / `-393`) | What it proves | Story |
|---|---|---|
| `desk-floor-seeded` | The desk floor + system bar on a seeded hub; quiet means no receipt | baseline |
| `write-receipt-before-hub-stop` | Before: hub alive, nothing failed | HS-132-06 |
| `write-receipt-hub-down-create-failed` | **The mandatory error leg.** Hub killed mid-walk, then a create verb: `CREATE NOTE FAILED · HUB UNREACHABLE  Retry  OK` in the menubar's own seat, in-flow, nothing overlapping, no dialog | HS-132-06 |
| `workbench-open` | The workbench window on the desk | HS-132-07 |
| `workbench-run-chip-disabled-reason` | RUN names WHY: `aria-label="Run: No agent bound · bind one in Configure"` | HS-132-07 |
| `workbench-item-body-held-draft` | A 57-char sentence typed at 8 ms/key, held intact inside the 450 ms save debounce and after the flush — zero keystrokes lost | HS-132-07 |
| `workbench-drop-overlay-verbs` | `DROP TARGET · ADD ITEM` on drag-over — the drop target says what it will do | HS-132-07 |
| `intelligence-brief-open` | The Brief view, populated | HS-132-08 |
| `intelligence-brief-acknowledged-badge` | Acknowledge writes a persisted `ACKNOWLEDGED` badge (the 393 pass also proves Defer, then Acknowledge) | HS-132-08 |
| `intelligence-brief-acknowledged-after-reload` | The badge survives a full reload — server state, not local | HS-132-08 |
| `intelligence-followthrough-all-lanes` | Before: the board, all lanes | HS-132-08 |
| `intelligence-followthrough-overdue-filter-token` | The overdue drill renders `FILTER · OVERDUE ONLY ✕`, and the empty lane reads `No overdue follow-through. Other lanes hold work.` + `Show all lanes` — **never a bare ALL CLEAR** | HS-132-08 |
| `intelligence-followthrough-tabbed-back` | Tabbing away and back: the filter is navigation-owned, the board still tells the truth | HS-132-08 |
| `intelligence-receipts-list` | The Decisions/receipts list | HS-132-08, HS-127 |
| `intelligence-receipts-detail-supersession` | An opened receipt carries its `Supersession history` section | HS-132-08, HS-127 |
| `settings-models-no-destination-provider-decides` | **Phase-130 Article IX.2 IOU, part 1.** No destination adopted: `NONE · PROVIDER DECIDES`, `DESTINATION WINS · PROVIDER DECIDES WHEN NO DESTINATION`, exactly one `DECIDES PLACEMENT` on screen | HS-132-10 |
| `settings-models-destination-decides-provider-overridden` | **Phase-130 Article IX.2 IOU, part 2.** Destination adopted: `DECIDES PLACEMENT`, provider dial `OVERRIDDEN` **and disabled**, `PROVIDER SELECTION IGNORED · DESTINATION HOMELAB .43 DECIDES`, `RUNS ON · HOMELAB .43 · PRIVATE_NETWORK · QWEN3.6-35B-A3B-UD-Q5_K_XL.GGUF` | HS-132-10 |
| `live-meeting-idle` | Before: the Live meeting window, idle | HS-132-03 |
| `live-meeting-intelligence-stream` | After: `INTELLIGENCE` section with its `READY` lamp, the summary and topic tokens rendered from `intel_token`/`intel_complete`, transcript of 3 live segments — no manual refetch | HS-132-03 |
| `live-meeting-bookmark-confirmed` | A bookmark dropped through the UI confirms live: `✓ The walk was here · …` | HS-132-03 |
| `cadence-loops` | The cadence loop board with a projected `agent_question` | HS-132-11 |
| `cadence-reply-pad-ready` | The reply pad with **Send reply** enabled once text is typed | HS-132-11 |
| `cadence-reply-sent` | The reply's receipt after Send | HS-132-11 |
| `ask-panel-destination-selected` | Ask pointed at the `.43` destination through the `Runs on` picker | HS-132-09 |
| `ask-panel-ran-on-lan43-footer` | **On glass:** `RAN ON Homelab .43 · Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf`, and in the turn `ran on ▪ LAN · 192.168.1.43 · Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf` | HS-132-09 |
| `ask-receipt-lan43.json` | The API receipt for the real `.43` Ask | HS-132-09 |
| `ask-receipt-this-machine.json` | The `this_machine` control's honest refusal | HS-132-09 |

Additional assertions that carry no shot of their own: stopping a live
meeting succeeds, stopping again answers **409 `No active meeting`** and the
hub survives (HS-132-01); the cadence reply route is mounted and refuses an
unknown loop by name (HS-132-11); `placement_source` rides the
`/api/settings` payload (HS-132-10).

## The `.43` proof (control vs treatment)

LAN precondition, live: `http://192.168.1.43:8080/v1/models` →
`Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf`.

**Treatment — a real Ask on the LAN destination** (`ask-receipt-lan43.json`):

```json
{
  "output": "{\"line\": \"HOLDSPEAK WALK OK\"}",
  "model": "Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf",
  "profile_id": "walk-lan43",
  "actual_placement": {
    "target_id": "walk-lan43",
    "target_name": "Homelab .43",
    "target_kind": "private_endpoint",
    "boundary": "private_network",
    "engine": "cloud",
    "model": "Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf",
    "fallback_reason": null
  },
  "egress": { "host": "192.168.1.43", "scope": "private_network" },
  "invocation_id": "ask_9bab09919897490f970cf6faf83712ee",
  "receipt_id": "rcpt_f63638bfaede4076a7454576a511c24b"
}
```

Chain asserted equal, end to end:
`readiness.model == executed == receipt.model == actual_placement.model ==
/api/models advertised name == AskPanel footer` =
`Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf`. Egress is `private_network`, never cloud.

**Control — `this_machine` in the fresh `HOME`** (`ask-receipt-this-machine.json`):
an honest refusal with its shot, not a fabricated run.

```json
{
  "error": "model file not found: ~/Models/gguf/Qwen3.5-9B-Instruct-Q6_K.gguf",
  "code": "inference_target_unavailable",
  "inference_target": {
    "id": "this_machine", "name": "This device", "kind": "this_device",
    "boundary": "same_device", "engine": "configured_local_engine",
    "model": "Qwen3.5-9B-Instruct-Q6_K"
  },
  "readiness": {
    "state": "unavailable", "available": false,
    "reason": "model file not found: ~/Models/gguf/Qwen3.5-9B-Instruct-Q6_K.gguf",
    "recovery": { "action": "choose_alternate_target" }
  }
}
```

The refusal still names the model it would have loaded and the reason it
could not — Article XI.3 holds on the failing branch too. No local GGUF is
installed in a fresh `HOME`, so this is the leg that was reachable; a machine
with the model present would take the run branch instead.

## The e2e net, run live against the walk hub

```
$ HOLDSPEAK_HUB_URL=http://127.0.0.1:8795 HOME=<walk home> \
  PLAYWRIGHT_BROWSERS_PATH=~/Library/Caches/ms-playwright \
  uv run pytest -q tests/e2e/test_workbench_walk.py tests/e2e/test_live_bus.py --tb=short

..............ss...                                                     [100%]
=========================== short test summary info ============================
SKIPPED [1] tests/e2e/test_workbench_walk.py:149: requires the production app fixture and deployment-adapter fake
SKIPPED [1] tests/e2e/test_workbench_walk.py:158: requires the production app fixture and deployment-adapter fake
17 passed, 2 skipped in 96.89s (0:01:36)
```

The 14 `test_workbench_walk.py` screenshot tests, previously module-skipped
with "no hub listening", ran for real against the live hub. The two remaining
skips are the reserved production-adapter fixtures, unchanged.

## Findings

Reported, not fixed (none are walk-harness bugs; the one harness bug found —
a `New Note` menu item whose accessible name carries its keycap — was fixed
in the harness).

### F1 — A past-due meeting commitment can never reach the Overdue lane

`holdspeak/services/follow_through_service.py:447`

```python
if due_date < today and status.lower() == "open":
    return "overdue"
```

Two vocabularies write the same column. `FollowThroughService.commit_decision`
inserts action items with `status = 'open'` directly
(`follow_through_service.py:183,197`), but everything the capture pipeline
persists goes through `MeetingsRepository._normalize_action_item_status`
(`holdspeak/db/meetings.py:35-43`), whose `VALID_ACTION_ITEM_STATUSES` are
`{pending, done, dismissed}` — `open` is not among them.

Reproduced live in this walk: a meeting action item due `2026-08-09`
(six days past, owner set, review_state accepted) is classified `now`, not
`overdue`, by `GET /api/follow-through/board`. Consequence: the Overdue lane,
the overdue drill, and the dock's `Intelligence, N overdue` badge all
under-report meeting commitments. This is the same class of defect HS-132-08
closed on the ALL-CLEAR path, one layer down — the board no longer *lies*
about being clear, but a past-due meeting commitment still never arrives in
the lane that would say otherwise. Shot:
`intelligence-followthrough-overdue-filter-token-*.png` (honest empty state,
with an overdue commitment sitting in `now`).

### F2 — The live bookmark confirmation prints a raw float, not a time

`web/src/pages/cores/LiveCore.tsx:200-207` builds the confirmation from
`data?.formatted_time ?? data?.timestamp ?? data?.time`. Nothing in
`holdspeak/` ever emits `formatted_time` (grep: zero hits), and the runtime's
own bookmark payload (`holdspeak/runtime/meeting_glue.py:485`) carries
`timestamp` as raw seconds-into-the-meeting. The user therefore always sees
something like `✓ The walk was here · 6.22566032409668`. Shot:
`live-meeting-bookmark-confirmed-*.png`. Cosmetic, but it is a receipt, and
receipts are read.

### F3 — The AskPanel footer receipt collides with the footer verbs

At 1440, with a long model name, `RAN ON Homelab .43 ·
Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf` overruns into the `Bin` / `Keep` verbs at the
footer's right edge (visible as overlapping glyphs). Shot:
`ask-panel-ran-on-lan43-footer-1440.png`, bottom-right. The receipt is
correct; the footer does not reserve room for it.

### Non-findings, recorded so they are not re-investigated

- `actual_placement.engine` reads `"cloud"` for a private LAN endpoint while
  `inference_target.engine` reads `"openai_compatible"` and the boundary is
  correctly `private_network`. The *boundary* vocabulary — the one the badge,
  the lamp and Article IX.2 use — is right everywhere; `engine` here is the
  adapter family, not an egress claim. Noted only because it reads oddly next
  to `boundary`.
- The Desk-menubar route to `New Note` is unavailable at 393 (the verb bar
  collapses); the walk uses the identical palette verb at that width and says
  so in its own output.
