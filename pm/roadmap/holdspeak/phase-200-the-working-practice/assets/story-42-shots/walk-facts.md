# HS-200-42 shot walk — the `Run intelligence` receipt and the drainer

**Re-walked 2026-09-14 21:28** after the counsel conditions (P1-3) and the
first walk's rulings F1–F4. The first walk's finding stands as the reason
this file was rewritten: the drainer fact never reached a pixel, and both
worlds shot identically. It does now.

Walked on a real `MeetingWebServer` booted from the worktree
`feat/hs-200-42-drain-intel-queue`, under an isolated HOME, on a free
loopback port. The owner's desk, DB and hub were never touched. The web
bundle was rebuilt from this worktree before the shots (`npm run build`,
`holdspeak/static/_built/`, built in 5.19s).

Rig: `scratchpad/shots42/walk42.py` (the four worlds). Every button and
badge fact below is read from the live DOM (`textContent`, `.disabled`,
`tagName`, `className`), never from the image.

## Hubs

| world | width | drainer at boot |
|---|---|---|
| absent | 1440, 393 | `absent` — the hub never claims the database, so `start_intel_queue_conductor` refuses ("Intel queue drainer is OFF: this process does not own the database") |
| running | 1440, 393 | `running` — the process takes the real owner claim (`runtime_lock.claim_database`, `held=True`) before the hub starts; the provider engine is stubbed |

## Seed

One meeting per hub through the real meetings/segments tables: `m-budget`
"Quarterly budget review", `intel_status='disabled'`,
`capture_status='finalized'`, 32 MIN, three real transcript segments.
`disabled` is the only state in which the Chair renders the verb
(`intelBadge` maps it to `OFF`; the verb is gated on `isOff && hasTranscript`).

## The receipts the route returned

```
absent : {"state":"queued","host":"local","drainer":"absent","expectedWithinSeconds":null}
running: {"state":"queued","host":"local","drainer":"running","expectedWithinSeconds":0}
```

## Shots, and the DOM behind each

| shot | state | badge (DOM) | verb | tag / class |
|---|---|---|---|---|
| `absent-before-1440.png` | before the click | `OFF` | `Run intelligence`, enabled | `BUTTON` / `btn btn--primary btn--sm` |
| `absent-before-393.png` | before the click | `OFF` | `Run intelligence`, enabled | `BUTTON` / `btn btn--primary btn--sm` |
| `running-before-1440.png` | before the click | `OFF` | `Run intelligence`, enabled | `BUTTON` / `btn btn--primary btn--sm` |
| `running-before-393.png` | before the click | `OFF` | `Run intelligence`, enabled | `BUTTON` / `btn btn--primary btn--sm` |
| **`absent-after-click-1440.png`** | receipt landed | **`NOT DRAINING`** (+ `THIS DEVICE`) | gone (the row is no longer OFF) | — |
| **`absent-after-click-393.png`** | receipt landed | **`NOT DRAINING`** (+ `THIS DEVICE`) | gone | — |
| **`running-after-click-1440.png`** | receipt landed | **`QUEUED`** (+ `THIS DEVICE`) | gone | — |
| **`running-after-click-393.png`** | receipt landed | **`QUEUED`** (+ `THIS DEVICE`) | gone | — |
| **`absent-after-refresh-1440.png`** | next desk refresh | **`NOT DRAINING`** (durable, from the frame) | gone | — |
| **`absent-after-refresh-393.png`** | next desk refresh | **`NOT DRAINING`** (durable) | gone | — |
| `running-after-refresh-1440.png` | next desk refresh | `QUEUED` | gone | — |
| `running-after-refresh-393.png` | next desk refresh | `QUEUED` | gone | — |
| `running-after-drain-1440.png` | after the drainer ran | `FAILED` (server truth) | gone | — |
| `running-after-drain-393.png` | after the drainer ran | `FAILED` | gone | — |
| **`running-verb-returns-1440.png`** | row back to `off`-with-transcript | `OFF` | **`Run intelligence`, enabled** | `BUTTON` / `btn btn--primary btn--sm` |
| **`running-verb-returns-393.png`** | row back to `off`-with-transcript | `OFF` | **`Run intelligence`, enabled** | `BUTTON` / `btn btn--primary btn--sm` |

`cmp` on the two worlds: `*-before-*` are byte-identical (nothing has
happened yet, as expected); `absent-after-click-*` and
`running-after-click-*` **differ at both widths** — the finding that
reopened this walk is paid.

## The four rulings, in pixels

- **F1 — the badge carries the drainer fact.** `NOT DRAINING` (danger tone)
  vs `QUEUED` (accent) at both widths. Existing badge species, one token,
  no sentence. The in-flight label stays `Run intelligence` with the Button
  disabled: nothing is queued before the 2xx.
- **F2 — one truth on the screen.** The receipt is dropped the moment the
  server's `intelStatus` for that meeting leaves `off`, so the Chair follows
  the server (`QUEUED` → `FAILED`) instead of pinning its own optimistic
  state. `running-verb-returns-*` shows the same mechanism putting the verb
  back on an `off`-with-transcript row, with no stale badge.
- **F3 — the species defect.** No after-click shot has a Meetings window over
  the Chair any more (compare the first walk, where every one did). The
  ledger line is now `role="button"` + `tabIndex`, so a trailing verb is no
  longer a button nested in a button, and the trailing slot swallows its own
  clicks.
- **F4 — the 393 overlap.** `absent-after-click-393.png` shows the `1 QUEUED`
  chip at the right margin, clear of the `Nothing needs you` headline it used
  to be drawn over. Cause: `.ambient-queue` is `position: fixed; top: 76px;
  left: 50%; transform: translateX(-50%)` — dead centre of the headline band.
  Fixed inside the existing `max-width: 560px` block only, so the 1440 shots
  are unchanged (`running-after-click-1440.png` still shows the chip centred).

## N1 — the badge is durable now

The first re-walk's residue is paid. `build_runtime_queue_frame`
(`intel_queue.py`) carries `drainer: "running" | "absent"`, and the Chair and
the History catalog read it from the same `runtime_queue` frame the ambient
HUD chip already consumed. A row whose server status is `queued` while the
frame says `absent` reads `NOT DRAINING` **durably**, not for a second:
`absent-after-refresh-{1440,393}.png` were re-shot on 2026-09-14 21:51 and
read `NOT DRAINING` from the DOM after a full reload. The click receipt now
covers only the sub-second window before the first frame arrives.

No frame yet is UNKNOWN and is never reported as absent — a fresh page load
with a pre-existing queued job and no broadcast still reads `QUEUED`.

## Console / page errors

No `pageerror` in any of the four runs. No horizontal overflow at either
width in any run. One `404` console error in the two runs where the rig
navigated to `/cores/history` — a wrong URL the rig tried, not a product
route; those two screenshots were of the 404 JSON page and have been deleted
rather than kept as evidence. The `HistoryCore` change (P1-3: stop polling
for 120s when `drainer !== "running"`) is covered by `tsc` and the touched
specs, not by a shot.

## Not achieved

The stub-provider drain reaches the engine and writes a real
`intel_snapshots` row (1 per running world) and a real action item ("Send the
deck", visible in `running-after-drain-*`), but the routed plugin chain
refuses because the rig assigns plugin routes without supplying a plugin
host, so the meeting settles `error` / `FAILED`. A clean `RAN` shot was
therefore not captured — the same rig artifact the first walk recorded.
