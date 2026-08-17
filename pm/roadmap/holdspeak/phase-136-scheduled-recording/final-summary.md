# Phase 136 — Scheduled Recording — Final Summary

**Status:** 4/4 done. Counsel recorded. Owner sitting pending.

## The mandate

From the Dashboard Door reflection (2026-08-17), chosen as a focused
standalone build: the Chair should let the owner **schedule a
recording** — set a time (one-shot or recurring) at which HoldSpeak
starts capturing a meeting on its own, and stops it on its own. Zero
corporate access — this is HoldSpeak's own capture, not the
Conditional-Access-blocked external calendar (which stays a deferred
empty connector slot per the arc ruling).

## What shipped

Four stories, each through the gate:

- **HS-136-01 — the spine** (`83f57e7a`). A new `scheduled_recordings`
  table (schema 60→61), a shared `holdspeak/cron.py`, and
  `scheduled_recording_conductor.py`: a 60s hub tick driving
  `idle → arming → recording → stopped` with `cancelled` / `refused` /
  `missed` branches, firing through the existing `_start_meeting` seam
  under a SCHEDULER principal (kernel-admitted, receipted). Ten
  invariants (I1–I10) with 46 tests.
- **HS-136-02 — the verb** (`8eef5289`). One shared service core feeding
  both the HTTP routes (`/api/scheduled-recordings`) and five
  `scheduled_recording.*` MCP tools, so an agent drives scheduling
  exactly as the UI does. Typed refusals, a receipt on every mutation.
- **HS-136-03 — the Chair surface** (`e22545a0`). An in-world DeskWindow
  create control (title + speak-to-fill mic, one-shot/recurring,
  duration), SCHEDULED entries in the Meetings lane with next-fire time,
  and the tap-to-cancel arming countdown on the capture hero with honest
  started/cancelled/refused/missed states.
- **HS-136-04 — docs, walk, close** (this commit). Entry-point docs, the
  surface walk harness, the counsel, and this summary.

## The owner's rulings (implemented, not relitigated)

1. **Auto-start via a visible countdown, tap-to-cancel** — fires on its
   own yet keeps the mic owner visible at the moment of truth (Article
   IV.3), so no Constitution amendment was needed. This reconciled a
   scoping pass that returned two contradictory verdicts (headless start
   possible / not) — they agreed on the mechanics (the hub owns the mic,
   the browser is only a remote control), disagreeing only on canon
   policy, which the countdown ruling settled.
2. **One-shot and recurring from one cron-backed control.**
3. **Auto-stop by duration, default 60 minutes.**
4. **Honest missed/refused receipts** when the hub is down or the mic is
   held — never a silent skip.

## Verification

- **Full suite green** at every landing (final: 5923 passed, 0 failed,
  isolated HOME, `-n auto`).
- **Adversarial verification** of the spine (fresh read-only reviewer):
  every real-bite axis held — restart auto-stop durability (deadline
  persisted before observable + boot reconcile), the manual-capture
  collision gated by the mic floor with graceful refusal, the additive
  schema upgrade of the new table onto an existing DB (no repeat of the
  59→60 P0), bounded catch-up, mic TOCTOU, dedupe. Its findings (honest
  auto-stop receipt, a corrected concurrency comment, a start-failure
  test) were folded into the spine before it shipped.
- **The surface screenshot walk** (`scripts/schedule_walk_hs136.py`,
  1440 + 393) earned its place: it caught four defects the vitest suite
  structurally could not (mocked data hides them) — a seconds-vs-ms
  serialization bug rendering next-fire as a 1970 date, six frames
  registered but invisible to the frame-wiring scanner, a too-terse
  error message failing the product-copy law, and an API-surface
  manifest drift. All four were fixed before HS-136-03 shipped.

## Amendments and deferred items (owner may overrule at the sitting)

- **The real-mic-fire metal walk is deferred** to a documented
  follow-up (owner ruling 2026-08-17: skip firing this machine's mic).
  The phase closes on the surface walk + the ten invariant tests + the
  adversarial pass. The refusal and missed paths are proven by unit
  tests (I4, VI.1), not a live fire.
- **DST fall-back double-hour** is accepted as standard cron semantics
  (a short schedule can fire twice in the repeated hour), noted in
  `holdspeak/cron.py`, not mitigated — per the owner's rigor bar.
- **The external calendar connector** stays blocked (Conditional Access
  / Intune) and out of scope; it ships later as an empty connector slot.
- **Flake ledger:** three concurrency tests surfaced as single-run xdist
  flakes across the phase (`test_inference_runner` deadline test,
  `test_device_recording_tick`, `test_node_link_two_process`), each 2–3/3
  green serially → BACKLOG Candidate Z, not regressions.

## Docs

Written at existing entry points (no orphan page); the doc-drift guard
is green (19 passed):
- **`docs/USER_GUIDE.md`** — a "Schedule A Recording" section (create via
  Chair / HTTP / MCP; the arming countdown and cancel; the
  refusal/missed receipts; where scheduled recordings appear), between
  Meeting Mode and Meeting Intelligence.
- **`docs/SECURITY.md`** — under "Inference authority and bounded
  schedules": the SCHEDULER principal, bounded delegation with
  re-approval on a terms edit, the Article IV.3 countdown as the visible
  fire, the Article VI.1 refusal/missed receipts, and no new egress
  (III.1).
- **`docs/ARCHITECTURE.md`** — a "scheduled recording conductor"
  subsection under the meeting pipeline: the 60s tick, the persisted
  deadline restart reconciliation, and the fire through `_start_meeting`
  under a SCHEDULER principal.

## The counsel

Verdict: **RATIFY-WITH-CONCERNS** (fresh Opus counsel). It verified all
five judgment calls sound (the IV.3/V.1 countdown reconciliation citing
the Phase-107 clarification; the metal-walk deferral as a narrow ~12-line
wiring gap over the already-proven `_start_meeting` path; the DST
acceptance; the flake ledger; the invariant test strength), and checked
every final-summary claim against code/evidence — no unsupported claims.
Three findings, none a merge blocker, ledgered for the sitting:

1. **(should-fix) `pending_title` race.** The conductor→runtime wiring
   lambda (`holdspeak/web_server.py:899-901`) sets `pending_title` with a
   bare `setattr` outside `state_lock`, unlike the API path
   (`meeting_glue.py:510-512`). A manual `POST /api/meeting/start`
   racing a scheduled fire in the sub-ms window could give the scheduled
   recording the wrong title. Consequence: cosmetic (correctable title),
   not data loss; the voice floor gates the destructive case. **Fix
   (deferred per the owner's rigor bar — sub-ms trigger on a one-owner
   product):** pass `title` as an explicit `_start_meeting` argument, or
   wrap both operations in `state_lock`.
2. **(note) SCHEDULED badge truncates at 393px** — the lane `meta`
   column was built for short tokens (`REC`/`OFF`); `SCHEDULED` is the
   longest. Polish: a `SCHED` short form at narrow widths.
3. **(note) `_write_receipt` duplicated** across the conductor and the
   service (different principals: scheduler vs owner) — a refactor
   candidate.

The orchestrator ledgered all three rather than re-open the shipped
spine for a sub-ms cosmetic race, consistent with the owner's rigor bar;
the owner may overrule at the sitting.

## The close

Pushed, PR'd, and merged on green CI per the house watch → read → merge
practice; the counsel's verdict is recorded above for the owner's
sitting.

