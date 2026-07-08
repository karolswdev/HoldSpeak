# AGENT-BRIEF — Phase 88: The Rails-Aware Desk

Read this, then the Phase-87 final summary
(`../phase-87-steering-desk/final-summary.md`), then
`docs/internal/MISSION_CONTROL_DESK.md` (the §5 client contract this
phase extends to grounding). This phase consumes the seams Phase 87
just shipped — do not rebuild them.

## The owner's direction (verbatim, 2026-07-08)

> "having the ability to natively offer parts of, e.g., open phases,
> open roadmaps, open stories, to use as context for any of the agent
> definitions, and so on, and the ability to construct agent chains so
> the local model keeps a note of everything happening with dw in the
> background, happening on another computer, for example."

Decode: two capabilities, one thesis — **the rails are desk-native
material.**

1. **Rails objects as grounding kinds.** A phase, a roadmap, a story,
   an evidence file — pickable in the grounding picker like a meeting
   or a note, hydrated with provenance into ANY run (ask, recipe,
   chain step, Phase-87 steer).
2. **The ambient dw observer.** A local model keeps a running journal
   of what the rails did — including, eventually, repos on another
   machine — read-only, off by default.

## What already exists (do not rebuild)

| Capability | Where | State |
|---|---|---|
| Factored grounding hydration | `holdspeak/grounding.py` — `hydrate_refs(db, meeting_ids, artifact_ids, expand) -> ([GroundingBlock], unknown)`, `GroundingBlock(kind, ref, title, subtitle, text)`, `compose_steer`, caps | production (Phase 87) |
| The grounding picker + gauge | `web/src/desk/components/GroundingSection.tsx`, `web/src/desk/grounding.ts` (`hubGrounding`, `fetchGroundingMeeting`, the token gauge) | production (Phase 83) |
| The rails bridge (CLI-mediated, receipt posture) | `holdspeak/missioncontrol_bridge.py` — injectable runner, `dw_argv_base(repo)`, `state_payload`, `sessions_payload`; `dw context` names per-story `trace` paths | production (Phase 82/86) |
| The one bus + belt/coder frames | `web_server.broadcast`, `scope:"belt"` (Phase 86) + `scope:"coder"` (Phase 87) frames; client `runtime-bus.js` | production |
| Chains / workflows primitives | `db.chains`, `db.workflows`, the run seam (`runCapability`) | production |
| RuntimeProfile + mesh relay | `db.profiles` (kind on-device/endpoint/meshNode), `intel/mesh_relay.py`, the pull-worker + liveness | production (Phase 84/85) |
| The steer + audit seam | `holdspeak/coder_steering.py` (`deliver`, `steering_audit`), `coder_steering_routes.py` | production (Phase 87) |
| The actuator proposal flow | `db.actuators`, `actuator_shared.decide_proposal`, off by default | production |

## The receipt rule (pinned, not optional)

A grounded rail object is a **receipt, not a scrape.** `dw context`
(the `missioncontrol_bridge` posture) names the file path per repo; the
hydration reads that contained file and headers it with provenance.
Rail STATE — a story's status, a session's correlation — is NEVER
re-parsed out of a markdown body; if a run needs the status, it comes
from `dw state`/`dw sessions`, the same three-document contract the
belt already honors (their `docs/mission-control.md` §5). A rail
grounding path that greps `Status:` out of a `.md` fails the phase.

## The consent rule (pinned)

The observer is **read-only and off by default.** It consumes the
existing bus frames plus a bounded `dw events` tail, summarizes on a
RuntimeProfile the owner chose, and writes ONE thing: a local journal
primitive. Anything it wants to DO — flip a story, file an issue — is
an actuator PROPOSAL through the existing propose→approve→execute
flow. Nothing here egresses that your own `dw`/model doesn't already.

## Implementation directions already decided

- **Rails refs vocabulary:** extend the grounding wire with
  `rails: [{repo, project, kind, id}]` where `kind ∈
  {phase, story, evidence, roadmap}`; the hub resolves each to a path
  via `missioncontrol_bridge` + `dw context`, reads it, and returns a
  `GroundingBlock(kind="rails:<kind>", ref, title, subtitle, text)`.
  Unknown/unreachable refs refuse by name (the ask seam's posture).
- **One hydration seam:** rails refs flow through the SAME
  `hydrate_refs` the meeting/artifact refs use (extend it or add a
  sibling that returns the same block type); ask, steer, recipe, and
  chain all ground rails identically — a parity test pins it.
- **The picker:** `GroundingSection` (or a rails-aware sibling) offers
  the belt's live phases/stories from the `/api/missioncontrol/state`
  feed the conveyor already fetches — no new catalog if the feed
  suffices; the token gauge already prices any block.
- **The observer:** a chain/workflow (or a small runtime loop)
  subscribed to `scope:"belt"`/`scope:"coder"` frames + a `dw events`
  tail; each event batch is summarized by the RuntimeProfile model via
  `asyncio.to_thread`; the journal is a note primitive tagged
  `rails-journal` (the deferred-decision default). Off by default
  behind a config flag, the actuator posture.
- **Cross-machine reach (ONE story, scoped):** the far node's worker
  tails its OWN `dw events` and pushes envelopes over the mesh relay
  (the Phase-85 pull-worker precedent, honest liveness); the observer
  merges them. Typed absence when the node is offline.

## Gotchas from the trenches (Phase 87 + earlier)

- api-surface regen AFTER web call sites; the web bundle rebuilt from
  `web/src`; screenshots get looked at, not just taken.
- The suite lands in a file and is READ before any story flips
  (memory: read-output-before-flip).
- Evidence files are write-once (append), and the `--tests-capture`
  contract pointer must name the GREEN full-suite run's timestamp.
- Prove LLM features on real metal (control-vs-treatment on `.43`);
  a no-LLM pass hides a broken grounding feature.
- `dw context`/`dw state` reads go through the injectable runner so
  tests fake them — never shell out un-injected.
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
