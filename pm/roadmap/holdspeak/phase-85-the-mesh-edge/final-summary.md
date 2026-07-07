# Phase 85 — The Mesh Edge: final summary

- **Phase opened:** 2026-07-07 (candidate T graduated same-day from the
  post-84 conversation)
- **Phase closed:** 2026-07-07 (scaffolded and shipped the same day)
- **Stories shipped:** 5/5

## Goal — was it met?

*"A profile can name a NODE, and a run against it executes on that node's
own provider — relayed through the hub, refused fast when the node is not
there, and badged as exactly what happened."* **Yes, proven live.** A
second local process (`holdspeak mesh serve`, node `walk-edge`, its own
HOME pointing at the `.43` llama.cpp) served an agent chat, a meeting-intel
reroute, and a dictation rewrite authored from ONE editor-born profile;
every badge read `⇄ mesh · walk-edge`, the worker's own log proved where
each run executed, and killing the worker read offline on every surface
with a forced run refusing in 0.00s, by name. The request moves; the model
and the key never do.

## What the phase shipped

- **HS-85-01 — The relay queue + the node wire:** `mesh_relay_jobs` +
  `mesh_workers` @ schema v10; enqueue (120s deadline) → per-node
  oldest-first claim (every poll stamps liveness — the mesh's only
  heartbeat) → complete/fail verbatim; lazy deadline enforcement with both
  abandonment shapes failing by name; late completions refused 409; three
  token-guarded routes (enqueue deliberately has no route).
- **HS-85-02 — The meshNode profile kind + the relay provider:** `kind:
  meshNode` + `node` mirrored three ways (JSON schema / Python @ v11 /
  Swift — where the pre-edit read caught the throwing Kind decode);
  `MeshRelayIntel` refuses an offline node immediately by name and
  enqueues nothing; dictation adopts meshNode too (mid-story owner call);
  egress scope `mesh` end to end.
- **HS-85-03 — `holdspeak mesh serve`:** any machine becomes an edge with
  one command (running it IS the consent): claim on the ~3s cadence →
  execute on THIS node's own provider → report verbatim; exponential
  backoff on hub outage; SIGINT-clean; `--once`; token via env var only.
- **HS-85-04 — Liveness on every surface:** models rows carry
  live/last-seen; an offline meshNode ask refuses 400 by name BEFORE
  anything queues; the profiles list carries a liveness envelope sidecar;
  the `/profiles` editor authors the Mesh kind; the rail dims dead edges;
  doctor's "Mesh edges" check.
- **HS-85-05 — Docs + the live walk:** the six-beat walk on the real hub
  (all beats asserted, worker log + three screenshots committed; offline
  refusal 0.00s < the pinned 5s); MODELS.md's mesh-edge section, the
  README bullet, SECURITY's Mesh relay egress row; and the walk's three
  runtime finds fixed + locked (below).

## The finds of the phase

1. **The event-loop deadlock (the risk table called it).** Every
   LLM-running route was `async def` calling the blocking engine inline; a
   mesh run WAITS on the relay queue while that same loop must serve the
   worker's claim polls — the job died at its deadline as "never claimed"
   with the worker demonstrably polling. `asyncio.to_thread` at all nine
   call sites; `test_engine_off_the_loop.py` locks the property (no
   running loop observable from the engine's thread).
2. **The mesh-blind capability gate.** `resolve_llm_capability` judged
   only `base_url`, so a mesh-adopted config silently skipped every LLM
   plugin while the reroute still said `executed: true`. A named node now
   short-circuits to capable; liveness stays a run-time question.
3. **The de-facto second seam.** The 14 builtin plugins call
   `MeetingIntel._chat_completion_text(messages, …)` directly — the "tiny
   `run_prompt` seam" was never the whole engine interface. `MeshRelayIntel`
   adapts it by folding messages onto the one relay wire.
4. **The upgrade hole.** v10→v11 stamped the version but `CREATE TABLE IF
   NOT EXISTS` cannot add a column to an existing table — `profiles.node`
   was silently missing on upgraded databases. Explicit `ALTER TABLE`
   guard, test-pinned.
5. **The recursion guard.** A serving node whose own engine resolves to a
   mesh profile would relay onward (or back to itself); it now fails the
   job by name.

## Stories shipped

| ID | Title | PR |
|----|-------|----|
| HS-85-01 | The relay queue + the node wire | #293 |
| HS-85-02 | The meshNode profile kind + the relay provider | #294 |
| HS-85-03 | `holdspeak mesh serve` — the edge worker | #295 |
| HS-85-04 | Liveness on every surface + the honest doctor | #296 |
| HS-85-05 | Docs + the live walk | the closing PR |

(The phase scaffold merged as #292.)

## Decisions

- Relay-through-hub, pull-only; nothing ever dials INTO a node.
- Relay jobs are hub-local rows, never a synced kind; prompts move only
  hub ⇄ executing node.
- The executing node resolves runs through its OWN config/keys — no
  credential ever transits the mesh.
- Serving is consent: running `holdspeak mesh serve` is the consent; the
  Apple devices' worker + per-device toggle is the HSM follow-up.
- v1 relay is blocking request/response; streaming relay is a future
  contract change (deferred, trigger recorded in the phase status).

## Numbers

Five PRs + the scaffold; 44 new tests across seven files; schema v9 → v11;
docs/voice guards 107; three walk screenshots + four liveness screenshots
committed; two rigs stay in `scripts/`
(`screenshot_hs85_liveness.py`, `walk_hs85_live.py`).

## Handoff — the explicit follow-up

**The Apple worker + the consent toggle (HSM track).** The wire is proven;
the iPhone/iPad side needs: a Swift pull worker speaking the three relay
routes on the `ILLMProvider` seam, and a per-device "serve my models to
the mesh" toggle (off by default) in Settings — the exact HS-85 posture
(polling is liveness; running is consent). Until then, any Mac/Linux
machine already serves with `holdspeak mesh serve`.

Ops notes for live proofs (standing): restart the hub on merged code with
`HOLDSPEAK_WEB_PORT=8765` pinned; the walk imports a fresh throwaway
meeting per run (reroute dedup keys off the transcript hash); the worker
runs `-v` so its log lines reach the captured stderr.
