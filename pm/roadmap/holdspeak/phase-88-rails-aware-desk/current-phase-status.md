# Phase 88 — The Rails-Aware Desk (rails as material, the ambient observer)

**Last updated:** 2026-07-08 (**PHASE CLOSED 5/5** — the walk passed live, docs shipped).

## Goal

The rails become desk-native material. An open phase, a roadmap, a
story, an evidence file are pickable in the grounding picker exactly
like a meeting or a note — hydrated with provenance into ANY agent run
(an ask, a recipe turn, a chain step, a Phase-87 steer) — and a local
model keeps a running journal of what the rails do (story flips, gate
refusals, evidence captures, phase closes), read-only and off by
default. Owner direction (2026-07-08, verbatim): *"having the ability
to natively offer parts of, e.g., open phases, open roadmaps, open
stories, to use as context for any of the agent definitions… and the
ability to construct agent chains so the local model keeps a note of
everything happening with dw in the background."*

## Scope

- In: rails objects as grounding kinds (`hydrate_refs` learns
  phase/story/evidence/roadmap refs, resolved CLI-mediated via
  `dw context` — a receipt, never a markdown scrape); the grounding
  picker gains a rails source, wired into ask AND the Phase-87 steer
  (one hydration truth); the ambient dw observer — a local
  (RuntimeProfile-resolved) model journaling rail events off the one
  bus + `dw events`, the journal a desk primitive (openable,
  groundable in turn), read-only, off by default; a live walk (a real
  open story grounded into a run and demonstrably used; the observer
  journaling a real flip) + docs + close.
- Out: any NEW egress (the rails read is your own `dw`; the journal is
  local); the observer ACTING on its own (anything it wants to do is a
  proposal through the actuator flow); B3 (the factory) and B4
  (DeskOS) per the RFC; cross-machine rail-event RELAY beyond the one
  honestly-scoped reach story (the far node tails its own `dw events`
  and pushes envelopes — the mesh-worker pull precedent).

## Exit criteria (evidence required)

- [x] An open story (and a phase, and an evidence file) hydrates into
      an ask byte-identically to how a meeting does, provenance-headed,
      the content CLI-mediated per repo — a grounded rail object is a
      receipt (HS-88-01).
- [x] The grounding picker offers rails objects from the belt's live
      projects, pickable into an ask AND a Phase-87 steer through the
      one shared hydration; over-cap and unknown refs refuse by name
      (HS-88-02).
- [x] Control vs treatment on a real model: the same question answered
      without and with a grounded open story; the answer demonstrably
      uses the rail content (the Phase-53 proof pattern) (HS-88-02,
      HS-88-05 walk beat 2).
- [x] The ambient observer, running on a local RuntimeProfile, turns a
      real rail-event stream (a story flip, a gate refusal) into a
      journal primitive — read-only, off by default, openable and
      groundable; anything it proposes rides the actuator flow
      (HS-88-03).
- [x] The walk: a rail object grounded into a live run and used; the
      observer journaling real motion; the suite + guards green; docs
      shipped (HS-88-05).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-88-01 | Rails objects as grounding kinds — the hub hydration seam | done | [story-01-rails-grounding-hub](./story-01-rails-grounding-hub.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-88-02 | The grounding picker learns the rails | done | [story-02-rails-picker](./story-02-rails-picker.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-88-03 | The ambient dw observer — the local rail journal | done | [story-03-ambient-observer](./story-03-ambient-observer.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-88-04 | Reach: rail events from another machine (scoped) | done | [story-04-cross-machine-reach](./story-04-cross-machine-reach.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-88-05 | The walk, the docs, the close | done | [story-05-walk-docs](./story-05-walk-docs.md) | [evidence-story-05](./evidence-story-05.md) |

## Where we are

Rails hydrate as receipts (HS-88-01): `holdspeak/grounding_rails.py`
resolves a `{repo, project, kind, id}` ref (`kind ∈ phase/story/
evidence/roadmap`) through `dw context` — the CLI NAMES the trace
path, the read is contained to that file, and the block is the SAME
`GroundingBlock` the meeting/artifact path returns (`kind="rails:*"`,
provenance subtitle `repo/project`, cap+cut). Unknown/unreachable/
bad-kind refs refuse by name; one context fetch per repo (cached). The
ask AND steer routes fold `grounding.rails: [refs]` in after the desk
objects, one ordered list, capped at 16 refs total. A no-scrape census
(`test_rails_no_scrape.py`) forbids parsing rail STATE from markdown.
Proven live: real `dw context` against this repo grounds story-01 and
the roadmap; control-vs-treatment on .43 — asked what kind string a
hydrated story ref carries, the bare model guessed "GroundingBlock",
the grounded run answered `kind="rails:<kind>"` (the story's own
words).

The picker learns the rails (HS-88-02): `RailsPicker` (a
`GroundingSection` sibling) flattens the belt's live projects from the
mission-control store — the roadmap, the current phase, its stories —
into pickable rail objects, mounted beside `GroundingSection` in BOTH
the ask panel and the Phase-87 steer composer. `buildGrounding(sel,
rails)` merges desk objects + rails into ONE wire object (null only
when both empty), so ask and steer send byte-identical grounding —
one hydration, both surfaces (a parity test pins it). The gauge is
honest: `POST /api/missioncontrol/rails/size` hydrates the picked refs
(the dw-named file) and returns SIZES only, never content; over-budget
warns in the composer. Control-vs-treatment on .43: asked (from a
grounded open story) the wire key rail refs ride under, the bare model
could not answer, the grounded run said `rails`.

The ambient observer is real (HS-88-03): `holdspeak/rails_observer.py`
is the pure core (event diffing by stable signature, batch summary,
journal body) with an injectable summarizer; `web_server.
_rails_observer_loop` drives it — OFF BY DEFAULT
(`RailsObserverConfig`, re-read each tick), tailing a bounded
`dw events` (the receipt posture), the first observation a baseline,
each NEW batch summarized by a RuntimeProfile model
(`build_profile_summarizer`, off the event loop) into a journal note
tagged `rails-journal`. Model-unavailable degrades to an honest
event-only entry (never a fabricated summary). READ-ONLY: the only
write is the journal — a census (`test_rails_observer.py`) forbids any
rails-write path in the module. `GET /api/missioncontrol/rails/journal`
reads it back. Proven live on .43: the observer tailed 16 real rail
events and journaled them accurately ("HS-88-02 moved from backlog to
done… HS-88-03 pulled into in-progress… a contract-missing refusal
resolved by regenerating the contract and passing the gate").

The reach is real (HS-88-04): a far node's worker POSTs `{node, ts,
events}` to `POST /api/missioncontrol/rails/remote-events`; the
observer merges the buffer each tick with the origin node STAMPED,
honest liveness drops a quiet node's stream (never fabricated), and
the envelope carries EVENTS ONLY — a body-carrying event is refused
(no repo file contents cross the wire). A remote and a local flip
never collide in the diff (the signature includes the origin). Proven
in-process (route → buffer → drain → journal, `@node` named); the
mesh_relay job queue is prompt/result-shaped, so events ride their own
thin push wire, and the pushing WORKER daemon is a deferred rider
(lands when a second rails machine is real).

**CLOSED (HS-88-05).** The seven-beat walk ran live against the real
`dw`, the real `.43` model, and a real tmux pane: ground THIS phase's
open story into an ask (control vs treatment — the bare model can't
name `steer_walk_hs87.py`, the grounded run does); ground the same
story into a steer that lands the rail block in a real pane; the
receipt/refusal check (the block IS the dw-named file; a bad ref
refused); the observer journaling real rail motion on .43; the
read-only census; the reach (a remote envelope named `@walk-remote`,
then read stale and dropped); the journal grounds in turn. Docs
shipped: USER_GUIDE "Ground a run on the rails" + "The rails journal",
the SECURITY.md rails-as-material trust boundary, the ARCHITECTURE.md
rails-as-material paragraph. The one deferred rider (the remote-events
worker daemon) and the B3/B4 handoff are in the
[final summary](./final-summary.md).

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| A grounded rail object is a scrape, not a receipt (state re-parsed from markdown) | the reason the CLI seam exists | `dw context` NAMES the path; the read is contained to that file; state (status, correlation) never re-derived from the markdown | any rail-grounding path that parses status out of a `.md` body |
| The observer acts on its own | the consent line of this phase | the observer is read-only; anything it wants to DO is an actuator PROPOSAL; off by default | any observer write that is not a human-approved proposal |
| The observer melts the event loop or the LAN | medium | it consumes the EXISTING bus frames + a bounded `dw events` tail, summarizes via `asyncio.to_thread`, RuntimeProfile-resolved; off by default | hub p95 degrades with the observer on |
| Rail content bloats a run past the cap | medium | the Phase-87 8 KB steer cap + the ask material cap already bound it; a rail object is capped like any block, cut marked | a run truncated silently by a huge evidence file |
| Cross-machine reach over-reaches | medium | ONE scoped story; the far node tails its OWN `dw events` and pushes envelopes (the pull-worker precedent), honest liveness; typed absence otherwise | a rail relay that reads a repo the far node cannot prove it holds |

## Decisions made (this phase)

- 2026-07-08 — A grounded rail object is a RECEIPT: `dw context` (the
  `missioncontrol_bridge` posture) names the file path per repo, the
  hydration reads that contained file, and rail STATE is never
  re-parsed from markdown — the Phase-82 §5 client contract, extended
  to grounding.
- 2026-07-08 — One hydration truth: rails refs land in the SAME
  `hydrate_refs`/`GroundingBlock` seam Phase 87 factored, so ask,
  recipe, chain, and steer all ground rails identically.
- 2026-07-08 — The observer is read-only and off by default; anything
  it wants to do is an actuator proposal (the standing off-by-default
  actuator rule); it runs on a RuntimeProfile the owner chose.
- 2026-07-08 (HS-88-04) — The cross-machine reach is a PUSH envelope,
  not the mesh relay queue: the `mesh_relay` job queue is
  prompt/result-shaped, so events ride their own thin wire — a far
  node's worker POSTs `{node, ts, events}` to
  `POST /api/missioncontrol/rails/remote-events`, the observer merges
  the buffer each tick with the origin node stamped, honest liveness
  drops a quiet node's stream, and the envelope carries EVENTS ONLY (a
  body-carrying event is refused). The full mesh-worker daemon that
  tails a remote `dw events` and calls this route is a deferred rider
  (below) — the wire is proven in-process (route → buffer → drain →
  journal, node named).

## Decisions deferred

- Whether the journal is a new primitive kind or a specialized note —
  trigger: the picker/lineage needs a distinct glyph — default: reuse
  the note primitive with a `rails-journal` tag until it earns a kind.
- The remote-events WORKER daemon (a `holdspeak mesh serve`-style loop
  that tails a far node's `dw events` and POSTs the envelope on a
  cadence) — trigger: the owner runs two live rails machines —
  default: the receiving wire is shipped and proven; the pushing
  daemon lands when a second machine is real.
- Grounding a CLOSED phase's whole roadmap (vs a single story) —
  trigger: a run that needs the portfolio — default: per-object refs;
  a roadmap ref hydrates the README, not every phase.
