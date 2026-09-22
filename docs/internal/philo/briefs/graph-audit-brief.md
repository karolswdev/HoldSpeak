# The graph audit — the one brief (Philo Phase 2)

**Status:** DRAFT for Astra's check (TWO-BRAINS §3). Both brains run this brief verbatim, twice each: once static (from the tree), once live (from a hub). Ratified when both have checked it.

## 0. The roots

The owner, 2026-09-22: "we're actually intended to work 90% of our time on the desk, with beautiful, cohesive interfaces that guide us, and all of this grounded in the ideology of Workbench 2.0+ on steroids." Read everything below through that, and through the Seven Tenets (CONSTITUTION.md). A dead verb is not a plumbing fault; it is a face that stopped guiding. The finding that matters is the one that costs him on a Tuesday.

## 1. Four definitions

- **Edge** — where something enters the platform: a click or key on a face, the voice-typing hotkey, a timer (the heartbeat, the intel drainer, a schedule), a WebSocket frame, an MCP tool call, a CLI verb, a connector webhook, an engine reply.
- **Interface** — where an edge surfaces: a face branch, an API route, a tool schema, a CLI command.
- **Connection** — the wiring: handler → route → service → table → projection → face.
- **Action** — a verb and what it changes, with its receipt (Article III).
- **State** (the fifth node kind) — a shape a connection can produce that a face must render.

Examples from the sitting of 2026-09-21: the sweep receipt's Open was an edge → interface → connection that ended in `openPrimitive(event_id)`, which resolves nothing: an edge with no action. The empty brief after a reload was a state with no face.

## 2. Four questions

1. Does every edge reach an interface?
2. Does every interface connect through to an action?
3. Does every action leave a visible consequence where the click left the user?
4. Does every state a connection can produce have a face?

Orphans count both ways: verbs with no effect, effects with no verb (a capability with no interface), faces with no state, states with no face.

## 3. The zero-diff law

After an edge fires, the live pass records the diff: DOM text, URL, open window set, requests fired, DB rows, receipt line. **Zero diff is a finding.** There is no allowlist of quiet verbs; Article III says every verb leaves a receipt.

## 4. The state atlas

States are minted through the REAL producer (the real API on a real hub in an isolated HOME), never through a double (the HS-200-05 scar). Atlas, first cut:

- projections: every `projection_kind` × `attention_state` (needs_attention, resolved, quiet), incl. a pipeline receipt with a door and one without;
- brief: none / empty (headline, zero items) / full / shelved;
- meeting: recording / stopped-no-transcript / imported / no-summary / summary-ran / summary-failed;
- engine assignment: none / missing profile (`legacy-intel`, the fresh-desk state) / ready;
- first value: no_speech / no_microphone / microphone_unavailable / kept;
- the clock: t0 (fresh desk), +1 sweep (15 min), +1 day (brief stale), +1 week boundary (calendar), +14 days (continuity horizon).

Each state at 1440 and 393.

## 5. The first-use twenty (walked first, with the real LAN engine)

arrival · the SETUP row · Choose an engine · Add an engine · Check · Use this for summaries · Record · Stop · Import · open the meeting · Run summary · Desk memory · a receipt's Open · Generate brief · Generate again · Write a thought · Kept · restart and find the summary · voice typing (⌥R) · Continue later.

Every other edge is walked with a recorded engine reply.

## 6. The static pass

From the tree alone, no hub: enumerate every edge (verbRegistry, applications.ts, every library Button `onClick`, keyboard maps, `holdspeak/runtime/*` timers, WebSocket frame kinds, MCP tool list, CLI, connectors); link each through its interface, connection and action with evidence `path:line`; read the Phase 1 inventories (`docs/generated/*`) and mark each claim verified or contradicted. Output the graph (schema §8) and the report (§9).

## 7. The live pass

`scripts/graph_walk.py` (or Astra's equivalent) presses every edge in every atlas state and writes the consequence record per edge per state, with a shot. Laws: `HOME=$(mktemp -d)`; `PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright`; never the microphone (fixture WAV `tests/fixtures/core_path_smoke_16k.wav`); never the owner's data dir or keychain; restore only tracked (` M`) shots, never `??` files; `set -o pipefail` on captures; one state per run on this machine.

## 8. The graph schema (`docs/generated/graph.json`)

```
{ "nodes": [ {"id","kind": "edge|interface|connection|action|state", "label", "path", "line"} ],
  "links": [ {"from","to","evidence": "path:line | shot | db row",
              "consequence": {"state","width","dom","url","windows","requests","rows","receipt"} | null} ],
  "orphans": {"edges_without_action": [], "actions_without_edge": [], "states_without_face": [], "faces_without_state": []} }
```

## 9. The report shape (every pass)

```
PASS: static | live      BRAIN: …      TREE: <sha>      HUB: <pid or none>
GRAPH: <path>            COVERAGE: edges N / states M / twenty K of 20
FINDINGS (ranked by cost to the owner on a Tuesday):
  bin=product-defect | doc-drift | tooling-debt ; evidence ; state ; shot
ORPHANS: …
UNKNOWN: what could not be verified, and why
```

Counts are diagnostics, never exits. The council (PHILO-2-06) merges four reports; the owner rules dissents; the engineering goes to Phase 3.
