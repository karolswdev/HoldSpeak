# Phase 82 — Mission Control (the Desk conveyor)

**Status:** OPEN — 4/5.

**Last updated:** 2026-07-04 (HS-82-04 done: the live layer —
on_story sessions pin to their story chips with awaiting-response
pulsing loudest and stale dimmed never dropped; every other
correlation bucket stays off the belt honestly; the event ticker
renders gate refusals first-class with rule ids verbatim; 28 desk
tests. HS-82-05 is the one story left: the approval leg + the
joint proof.)
pins the bridge, the belt, the 15 s single-flight poll, and the
approval leg riding the native `decide_proposal` + gated-connector
machinery; schema claims verified live against dw 1.9.0
(feed_schema 1, sessions_schema 1); stories 02–05 re-pinned to
their sections.)

## Why this phase exists

Delivery Workbench finished its half of mission control (their
Phase 13, five of six stories): a frozen state feed (`dw state
--json`, `feed_schema` 1), a correlation document (`dw sessions
--json`, `sessions_schema` 1) that joins OUR agent-session registry
to their in-progress stories, an append-only event log (`dw events
--json`), and a Telegram interface consuming all three from a
phone. The contract for what a client may consume is written and
pinned (their `docs/mission-control.md` §5): exactly the three
documents, via the dw CLI, no scraping of `pm/roadmap`, no reading
dw internals — and every client declares the schema versions it was
proven against, the way our pack MANIFEST declares its range.

The Desk owes the other window. Their WLA-13-05 ("prove mission
control end-to-end with the Desk") is blocked on exactly this
phase: a real conveyor on our web Desk rendering their live phase
state, a real approval flipping a story through the actuator pack
we already ship, and the dw gate refusing a dishonest flip in
front of the UI that proposed it.

What already exists on our side and is load-bearing here:

- The **agent-session registry** (`holdspeak/agent_context/`,
  `STATE_VERSION` 1) — their correlator reads it read-only and
  returns the join; the Desk never re-derives correlation.
- The **actuator pack + gated connector** (`dw_story_writer`, two
  allow-listed `dw story` argv shapes) installed on this desk —
  the only write path, human approval + dw gate in front.
- The **Desk island** (`web/src/desk/`, React 19 in the Astro
  shell) whose rule is: every read is a same-origin `/api/*`
  route. The feed therefore enters through the FastAPI runtime,
  not through the browser.

## The load-bearing design call

**The Desk stays a pure client of three documents.** A small
FastAPI bridge (`/api/missioncontrol/state|sessions|events`) shells
to the dw CLI of each configured rails repo (the existing
`~/.holdspeak/delivery_workbench.json` project map names them),
read-only, allow-listed argv, schema-checked at ingress — and the
React island renders what the bridge relays. Correlation stays
theirs, certification stays human, and the one write path stays the
Phase-12 connector. If their schemas move, the bridge refuses
politely and the Desk shows the compatibility note instead of
guessing — the pack precedent, now in a second client.

## Stories

| Story | Title | Status | Depends on |
|---|---|---|---|
| HS-82-01 | Design: the conveyor and its consumption seam — **leads** | **done** ([evidence](./evidence-story-01.md): doc + live schema verification) | none |
| HS-82-02 | The bridge: `/api/missioncontrol/*` relays the three documents | **done** ([evidence](./evidence-story-02.md): 11 route tests; unit tier 2422 green) | HS-82-01 |
| HS-82-03 | The conveyor renders: phases as the belt, stories as the items | **done** ([evidence](./evidence-story-03.md): 25 desk tests; astro build clean) | HS-82-02 |
| HS-82-04 | Sessions and events ride the belt | **done** ([evidence](./evidence-story-04.md): 28 desk tests; awaiting-response loudest, ambiguous never pinned) | HS-82-02 |
| HS-82-05 | The approval leg and the joint proof | ready | HS-82-03, HS-82-04 |

## Where we are

Opened. Scope notes kept honest up front: the iOS leg is a
documented compatibility note, not phase scope — their WLA-13-05
already records that the web Desk carries the joint proof if
mobile slips (holdspeak-mobile picks up the conveyor in its own
phase when its turn comes). And the registry's `SUPPORTED_AGENTS`
is `{claude, codex}` today — pi sessions appear on the belt the day
the registry learns to write them, and the conveyor's rendering is
agent-name-agnostic on purpose.
