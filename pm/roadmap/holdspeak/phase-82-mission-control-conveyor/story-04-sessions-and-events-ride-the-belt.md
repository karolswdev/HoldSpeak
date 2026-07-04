# HS-82-04 — Sessions and events ride the belt

- **Project:** holdspeak
- **Phase:** 82
- **Status:** backlog
- **Depends on:** HS-82-02 (the bridge serves sessions and events).
- **Unblocks:** HS-82-05.

## Problem

The belt without the live layer is a roadmap poster. The
correlation document already says which agent is on which story
and whether it is waiting on a human — OUR registry data, joined
by THEIR correlator, coming back to our Desk — and the event log
already narrates the rails (status flips, evidence captures, gate
verdicts with rule ids). Rendering both is what turns the conveyor
into mission control.

## The design

Sessions: each correlated session renders pinned to its story item
(`on_story`), or in the honest buckets the correlation names
(`ambiguous` lists its candidates, `idle_on_rails`, `off_rails`,
`unreadable`); `awaiting_response` is the loudest signal on the
belt (the agent is blocked on a human), `stale` is visible and
never silently dropped. The declared field list from HS-82-01 is
the whole render surface. Events: a ticker of the last N events
from the bridge, `gate_refusal` rendered first-class with its rule
id verbatim, `gate_pass` and `story_status` as the belt's motion.
No transcript content anywhere — the events carry rails metadata
only, by their consent stance, and the Desk adds none back.

## Test plan

- Vitest: session pinning per correlation outcome from sessions
  fixtures; the awaiting-response emphasis; the stale mark; event
  ticker rendering incl. a `gate_refusal` with rule id.
- Live check on this desk recorded in evidence: a real session in
  the registry appears on the right story.
