# HS-104-05 - Session receipts — honest numbers on the card

- **Project:** holdspeak
- **Phase:** 104
- **Status:** done
- **Depends on:** HS-104-01
- **Unblocks:** HS-104-06, HS-104-07
- **Owner:** unassigned

## The research finding (the bar)

AgentGlass computes per-session USD from token deltas and a pricing
table, plus per-tool p50/p95 from hook span pairing. The council's
verdict: supporting instrumentation, not load-bearing, and
frequently *fictional* — local models have no price, subscriptions
decouple tokens from spend, cache reads price differently, and p95
over a dozen unlike tool calls is statistical theater. HoldSpeak
ships the honest subset: numbers whose provenance the HS-104-01
ledger can vouch for, each labeled, none dashboarded.

## Problem

A steering session's pull-out and a delivery attempt's card say
nothing about what the session took: no elapsed, no call count, no
tokens, no cost. The owner budgets blind. But the fix must not
import the dashboard lie — a number without provenance on this desk
would violate Article VI the day it ships.

## Recipe

1. **One receipt line, not a panel.** The deliverable is a single
   composed line (existing kit vocabulary; no new chart, meter, or
   drawer) on the session pull-out (`SessionPullout`) and the
   delivery attempt card, in the egress-badge tradition: maximal
   honesty, minimal ink.
2. **The always-true tier.** Elapsed wall time and delivered-steer /
   command count come from records the hub itself wrote
   (`steering_audit`, the delivery command envelope) — authoritative
   by construction, always shown.
3. **The reported tier.** Token counts appear ONLY when the adapter's
   ledger row says `usage_tokens: authoritative` (Claude Code hook
   events carry usage; a bare tmux pane does not). Cache read/write
   tokens kept as separate figures, never summed into one number.
   Call through `require_capability` — the census pins it.
4. **The estimated tier.** Cost renders only when tokens are
   reported AND a price entry exists in a small, user-editable
   pricing table (config, not code), and always as
   `≈ $X.XX (price table, YYYY-MM-DD)` — the estimate marker, the
   source, the date. No price row → no cost line (an absent number,
   not a zero; zero is a lie).
5. **Latency percentiles, sample-floored.** Per-tool p50/p95 only
   when that tool has ≥ 20 paired observations in the session;
   below the floor, show count and max only. Never blend tools into
   one percentile.
6. **Storage.** A per-session rollup accumulated in the existing
   session/attempt records (schema ride-along if a column is
   needed) — computed at write time from events the hub already
   handles (gate/hook events from HS-104-02, steering audit rows,
   command receipts). No new collector, no polling.

## Out of scope

- Any aggregate view across sessions (spend-per-week is a dashboard;
  parked with the census candidates if ever wanted).
- Anthropic plan-window meters (AgentGlass reads
  `~/.claude/.credentials.json` for this; reading another app's
  credentials is off-posture here, full stop).
- Alerting/thresholds.

## Acceptance

- A real steered session's pull-out shows the always-true tier;
  after a gated Claude Code session (HS-104-02 rig), the reported
  tier appears with cache tokens separate; with a price entry the
  estimate renders with source + date, and with the price row
  removed the cost line disappears rather than reading $0.00.
- A tool below the sample floor shows count/max, never a percentile.
- Census: every reported/estimated figure's call site goes through
  `require_capability`; grep-pinned.
- Voice guard green on every new string (no prose, no dashes in
  glass).

## Test plan

- **Unit:** rollup math (elapsed, counts, token accumulation, cache
  separation); pricing-table resolution incl. the absent-row path;
  the sample floor boundary (19 vs 20).
- **Integration:** rollup written from a scripted session's event
  stream; the route serving the card's payload.
- **Live (evidence):** the real-session receipt line screenshotted
  at 1440 + 393, read before claiming done.

## Chef's notes

- The three tiers are the whole design. If a reviewer can't tell
  from the glass which tier a number belongs to, the story is not
  done — that legibility IS the feature, not the numbers.
- Fight the urge to backfill history. Receipts begin when the
  recording begins; an estimated backfill would be a fabricated
  receipt, the worst object this project could mint.
