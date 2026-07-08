# Phase 88 — The Rails-Aware Desk (rails as material, the ambient observer)

**Last updated:** 2026-07-08 (HS-88-01 done — rails hydrate as receipts; 1/5).

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

- [ ] An open story (and a phase, and an evidence file) hydrates into
      an ask byte-identically to how a meeting does, provenance-headed,
      the content CLI-mediated per repo — a grounded rail object is a
      receipt (HS-88-01).
- [ ] The grounding picker offers rails objects from the belt's live
      projects, pickable into an ask AND a Phase-87 steer through the
      one shared hydration; over-cap and unknown refs refuse by name
      (HS-88-02).
- [ ] Control vs treatment on a real model: the same question answered
      without and with a grounded open story; the answer demonstrably
      uses the rail content (the Phase-53 proof pattern) (HS-88-02).
- [ ] The ambient observer, running on a local RuntimeProfile, turns a
      real rail-event stream (a story flip, a gate refusal) into a
      journal primitive — read-only, off by default, openable and
      groundable; anything it proposes rides the actuator flow
      (HS-88-03).
- [ ] The walk: a rail object grounded into a live run and used; the
      observer journaling a real flip; the suite + guards green; docs
      shipped (HS-88-05).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-88-01 | Rails objects as grounding kinds — the hub hydration seam | done | [story-01-rails-grounding-hub](./story-01-rails-grounding-hub.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-88-02 | The grounding picker learns the rails | backlog | [story-02-rails-picker](./story-02-rails-picker.md) | - |
| HS-88-03 | The ambient dw observer — the local rail journal | backlog | [story-03-ambient-observer](./story-03-ambient-observer.md) | - |
| HS-88-04 | Reach: rail events from another machine (scoped) | backlog | [story-04-cross-machine-reach](./story-04-cross-machine-reach.md) | - |
| HS-88-05 | The walk, the docs, the close | backlog | [story-05-walk-docs](./story-05-walk-docs.md) | - |

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
words). Next: HS-88-02, the picker.

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

## Decisions deferred

- Whether the journal is a new primitive kind or a specialized note —
  trigger: the picker/lineage needs a distinct glyph — default: reuse
  the note primitive with a `rails-journal` tag until it earns a kind.
- Real-time cross-machine rail relay beyond the reach story — trigger:
  the owner runs two live rails machines — default: local `dw` only,
  the reach story proves the wire on one remote.
- Grounding a CLOSED phase's whole roadmap (vs a single story) —
  trigger: a run that needs the portfolio — default: per-object refs;
  a roadmap ref hydrates the README, not every phase.
