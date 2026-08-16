# Evidence - HS-132-14

- **Story:** HS-132-14 - The walk
- **Status:** done
- **Date:** 2026-08-15

## Proof

### Captured run — 2026-08-16T03:38:35Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d /tmp/hs132walkcap.XXXX) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run python -m scripts.walk_working_desk walk 2>&1 | tail -40; rc=$?; rm -rf /tmp/hs132walkcap.*; exit $rc`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 56f4b43773c9f5057e1fa137c00faca04d2888bd

```text
  SHOT  cadence-reply-sent-393.png — HS-132-11: the reply's receipt
  PASS  GET /api/cadence/loops answers
  PASS  the reply route is mounted and refuses an unknown loop BY NAME (HS-132-11: it used to 404 as an unmounted route) — 404 {"detail": "loop not found"}
  PASS  zero console errors — cadence @393 — []

== HS-132-09 receipt honesty @393 ==
  PASS  the LAN endpoint answers (live metal precondition) — 1 model(s): ['Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf']
  PASS  the .43 destination is created (or already exists) — 201
  PASS  the .43 destination is advertised under its real model name — 'Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf' vs 'Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf'
  PASS  the .43 Ask executed — {"actual_placement": {"boundary": "private_network", "data_classes": ["instruction", "selected_context", "grounding", "generated_output"], "engine": "cloud", "f
  PASS  the .43 receipt names the model that executed — model=Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf actual=Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf
  PASS  readiness == executed == receipt == advertised
  PASS  the .43 egress is private_network, never cloud — {"host": "192.168.1.43", "scope": "private_network"}
  PASS  this_machine REFUSES honestly (no local model in the fresh HOME) — model file not found: ~/Models/gguf/Qwen3.5-9B-Instruct-Q6_K.gguf
  PASS  the refusal still names the model it would have loaded — Qwen3.5-9B-Instruct-Q6_K
  SHOT  ask-panel-destination-selected-393.png — HS-132-09: Ask pointed at the .43 destination
  PASS  the AskPanel footer says RAN ON and names the executed model — RAN ON HOMELAB .43 · QWEN3.6-35B-A3B-UD-Q5_K_XL.GGUF
  SHOT  ask-panel-ran-on-lan43-footer-393.png — HS-132-09 on glass: RAN ON Homelab .43 · <the model that executed>
  PASS  zero console errors — ask panel @393 — []

== HS-132-06 write-receipt backstop (hub stopped) @393 ==
  SHOT  write-receipt-before-hub-stop-393.png — HS-132-06 before: no receipt, hub alive
  PASS  hub is actually down before the create verb
  FINDING  the Desk-menu route to New Note produced no write receipt at 393px; falling back to the palette verb
  PASS  a failed create names itself in a write receipt — CREATE NOTE FAILED · HUB UNREACHABLE
Retry
OK
  PASS  the receipt names the unreachable hub (not a silent no-op) — CREATE NOTE FAILED · HUB UNREACHABLE
Retry
OK
  PASS  the receipt is in-flow (menubar seat or floor row), not an overlay — menubar=True floor=False
  PASS  no modal/dialog overlaps the desk for the error
  SHOT  write-receipt-hub-down-create-failed-393.png — HS-132-06 after: CREATE NOTE FAILED named in-flow, nothing overlapping
  PASS  zero console errors — write-receipt backstop @393 — []
  hub pid=95494 home=/tmp/hs132walkcap.cSVz port=54066
  PASS  hub came back up for the rest of the walk

============================================================
115 passed, 0 failed, 1 finding(s), 50 shot(s)
  FINDING  the Desk-menu route to New Note produced no write receipt at 393px; falling back to the palette verb
```

## Orchestrator notes

- Verified on glass by the orchestrator (not just the worker's word):
  the .43 treatment shot shows the printed turn, `ran on LAN ·
  192.168.1.43 · Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf`, the model chip, and
  the footer receipt all naming the executed model; the hub-down shot
  shows `CREATE NOTE FAILED · HUB UNREACHABLE · Retry · OK` seated
  in-flow in the system bar beside RECONNECTING. Control leg: honest
  this_machine refusal naming the missing model file (fresh HOME has no
  GGUF) — the refusal branch, shot included.
- First walk pass returned three findings; all three were FIXED before
  this capture and the walk re-run green (115/0, 50 shots):
  (1) pipeline-persisted "pending" items can now reach the Overdue lane
  (follow_through_service.py + a kept regression test — the walk's live
  repro of a 6-day-overdue item classified "now" was the proof);
  (2) the live bookmark receipt renders m:ss instead of a raw float
  (LiveCore); (3) the Ask footer receipt ellipsizes via the kit's
  receipt-line class instead of colliding with Bin/Keep at 1440.
- e2e against the live hub: 17 passed, 2 skipped (named fixture skips) —
  the 14 workbench-walk shots ran for real for the first time since the
  hub-preflight skip landed.
- Honest limits recorded in WALK.md: headless walk plays the capture
  runtime through the real broadcast/socket/LiveCore path (no mic);
  decision-record and meeting action-item fixtures are written through
  the product's own services (no HTTP mint routes exist).
- Residual finding, ledgered for the sitting: at 393px the Desk-menu
  route to New Note produced no write receipt (the palette verb route
  does; harness fell back to it). Narrow-menu wiring, one lane wide.
- The Phase-130 Article IX.2 screenshot IOU is discharged: Settings >
  Models and the placement labels shot at both widths in both dial
  states.
- Tree-integrity note: 14 historic Phase-116 walk PNGs were found
  rewritten during this story (the worker's exploratory run of the old
  desk_walk harness, whose default output was that assets dir). All 14
  restored byte-identical from HEAD before shipping; the committed
  walk_working_desk harness writes only to hs-132-14 assets.
