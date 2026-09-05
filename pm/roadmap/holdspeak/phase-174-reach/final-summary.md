# Phase 174 — Reach: final summary (DRAFT — stacked on 173 (#556); closes on his word)

## What shipped

- **The design (01):** settled-design-reach.md + eleven boards. Canvas
  https://claude.ai/code/artifact/5719ec5d-4d70-4acc-9f7a-fbffa2d863a0.
  Counsel RATIFY-W-C on the design, six conditions ruled: the lid-closed
  claim was FALSE (nothing prevents sleep) → `WHILE THIS MAC IS AWAKE` on
  the face and in the docs; the `principals.py` path; one `Run now`;
  hash at rest; the per-route loopback guard; `pipeline_events.origin`
  named; `N CREDENTIALS` all vs `N ACTIVE` non-expired; the REMOTE chip
  the accent outline.
- **The wire (02 · 03 · 04 · 05):** `POST /api/mcp` on the live runtime,
  off by default; OWNER refused off-loopback on this route only;
  credentials `sha256` at rest with palette + TTL (≤ 30 d), revoke,
  last used, listed with epoch times and palette names; receipts carry
  `origin · caller · identity`; MCP-005 palette refusals; MCP-003 on
  the remote path (`run_id` promptly, poll).
- **The third connector (06 · 07):** Confluence as the reversible default
  (his word owed); `acli confluence` read-only allowlist of seven; recent
  blogs + pages by known ID; page listing typed `unsupported_by_cli`
  (confirmed at the binary); four provider routes + three MCP twins; the
  Door defaults `RECENT BLOGS` · `PAGES BY ID`.
- **The runner (08 · 09):** `scripts/reach_runner.py` (stdlib; exit codes
  0/1/2 `HUB ASLEEP OR OFF`/3/4; the token never on argv or stdout),
  proven on this machine against the real hub on loopback with a SWEEP
  credential (receipts `origin=remote`; the owner token 403
  off-loopback); the .43 leg waits for his sitting; the hub-side
  `desk.notification` mesh event for 179.
- **The faces (02 · 03 · 04 · 07 · 08):** Settings → System `This
  device` with `REMOTE OFF|ON`, REMOTE ACCESS (the toggle, the address,
  `N CREDENTIALS`), the CREDENTIALS ledger, the issue well (Name with
  the mic · Palette · TTL · Issue primary · Cancel), the token shown
  once with Copy; the shade's Finished rows and the Room's RECEIPTS
  section wearing `REMOTE · host` on remote-origin receipts with human
  labels (SWEEP · STEWARD RUN · READ <noun>) — `receiptLabel()`; the
  Door's Confluence row (Connect · SIGN IN · the site|email identity ·
  RECENT BLOGS on · PAGES BY ID off) in the fixed GH · Jira · Confluence
  order; Rhythm's `Runs on` (THIS DEVICE | a recorded remote host) with
  `WHILE THIS MAC IS AWAKE`, `LAST RUN`, `NO RUNS YET` and one `Run now`
  on the sweep row. Every face shot beside its board at 1440 and 393.
- **The docs (10):** README, USER_GUIDE "Reach", ARCHITECTURE sequence,
  SECURITY (the remote + Confluence boundaries), MCP_SIDECAR transports,
  docs/REACH_RUNNER.md, POSITIONING names — verified against the built
  product (story 10).
- **The walk (11):** live174_walk.py on the owner's desk 2026-09-05
  15:51 (Denver): remote OFF, so the one guarded write (the probe
  credential) was denied by the guard as designed — **zero writes**,
  8 shots, 0 defects, 0 errors. Facts: System module `THIS DEVICE ·
  MESH OFF · REMOTE OFF`, Streamable HTTP OFF, Issue credential absent;
  shade Finished 4 rows, no chip carrying a time; Rhythm `Runs on THIS
  DEVICE`, one `Run now`, no awake caption when local; Door GH · Jira ·
  Confluence `NOT SET UP · Connect`. Shots + walk-facts under
  assets/story-11-shots/.

## Found in review and paid

- The 171 heartbeat loop never called the notifier (found by this
  phase's runner lane); paid on feat/the-heartbeat and merged forward.
- The settings read returned monotonic times and resolved tool sets;
  fixed to epoch times and palette names.

## Gates

- Counsel on the design: RATIFY-W-C, ruled. Counsel on the built phase:
  RATIFY-W-C — C1 (a token in the URL on /api/mcp) PAID with a test that
  the refusal fires before the principal guards; C2 (the Door's row order
  vs the board) PAID — fixed GH · Jira · Confluence; C3 (the LIKE receipt
  scoping) documented; P1-1 (`NO RUNS YET` on a remote Runs-on with no
  run) and P2-1 (`CREDENTIALS · N ACTIVE`) PAID; every design-stage
  condition verified paid by counsel (C1–C6 and the three P2s).
- Suite (CI shape, -n auto, the built tree): **9814 passed · 98 skipped ·
  27 failed** = 6 inherited (ask grounding ×2, ask runner migration,
  the two broker density fences, product copy — zero diff vs main) +
  11 xdist-only (hs144/152/153/154/163 rigs, the two hs174 rigs before
  the rebuilt bundle, cadence closeout, the delivery campaign pair, the
  one-shot conductor — all green serially) + 10 fences moved by this
  phase and PAID @48c885ed (five connection tools with Confluence; the
  acli confluence effect site ledgered; the per-route loopback guard
  allowlisted in the principal-separation census; the origin columns in
  the canonical schema snapshot; the Room's `receipts` section; the
  drafter provenance classified; two tools.py line anchors).
- Web: vitest 273 passed across the door and cores; the inherited
  baseline run reports 4 HEALED and 1 BRANCH-NEW
  (`ThoughtDocumentPane.test.tsx` "does not fetch or render raw capture")
  that is green twice alone — a timing flake under the full run, not
  this phase's (last touched by 170's sweep); ratchet at its floor.
- The walk: zero writes on his desk (above).

## The owner's questions (in the handover)

Confluence: blogs vs page search · the awake-Mac prerequisite vs a
lid-open V0 · in-memory credentials re-issued after a restart · the .43
leg at his sitting · the listener on for his desk?

## His word

**PR #557** stacked on #556. Merge order stays his: #553 → #554 → #555 → #556 →
174's.
