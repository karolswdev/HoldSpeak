# Phase 88 — The Rails-Aware Desk — Final Summary

- **Phase opened:** 2026-07-08 (scaffolded from backlog candidate V /
  the owner's rails-aware direction, immediately after Phase 87 closed)
- **Phase closed:** 2026-07-08, the same day
- **Stories shipped:** 5/5

## Goal — was it met?

> The rails become desk-native material. An open phase, a roadmap, a
> story, an evidence file are pickable in the grounding picker exactly
> like a meeting — hydrated with provenance into ANY agent run — and a
> local model keeps a running journal of what the rails do, read-only
> and off by default. Owner: *"the ability to natively offer parts of
> open phases, open roadmaps, open stories, to use as context for any
> of the agent definitions… and agent chains so the local model keeps
> a note of everything happening with dw in the background."*

**Yes.** A rail object grounds into an ask and a steer as a receipt;
an ambient local model journals real rail motion; the reach merges a
remote node's events; the journal grounds in turn — all proven in a
single seven-beat walk against the real `dw`, the real `.43` model,
and a real tmux pane.

## Exit criteria — final state

- [x] An open story / phase / evidence hydrates into a run as a
      receipt, CLI-mediated (HS-88-01) — `test_grounding_rails`, live
      `dw context`.
- [x] The picker offers rails objects, pickable into ask AND steer
      through one shared hydration; over-cap/unknown refuse (HS-88-02).
- [x] Control vs treatment on a real model: the grounded open story
      changes the answer (HS-88-02, HS-88-05) — the bare model can't
      name a repo-specific fact; the grounded run does.
- [x] The ambient observer journals a real rail-event stream on a
      local RuntimeProfile — read-only, off by default, openable and
      groundable (HS-88-03) — proven live on `.43`.
- [x] The walk: a rail object grounded into a live run and used; the
      observer journaling real motion; suite + guards green; docs
      shipped (HS-88-05).

## What shipped

- **`holdspeak/grounding_rails.py`** — resolves a `{repo, project,
  kind, id}` ref through `dw context` (the CLI names the trace path),
  reads the contained file, returns the SAME `GroundingBlock` the
  meeting/artifact path returns. A no-scrape census forbids parsing
  rail state from markdown.
- **`RailsPicker.tsx` + `grounding.ts`** — the belt's live projects
  as pickable rail objects; `buildGrounding` merges desk objects +
  rails into one wire, so ask and steer ground rails identically;
  `POST /api/missioncontrol/rails/size` gives the gauge honest sizes.
- **`holdspeak/rails_observer.py` + `_rails_observer_loop`** — the
  ambient observer: event diffing, a local-model batch summary, a
  `rails-journal` note; off by default; read-only (a census pins it);
  degrades honestly when the model is absent. `GET .../rails/journal`.
- **The reach** — `POST .../rails/remote-events` accepts a far node's
  `{node, ts, events}` envelope (events only, origin-stamped, honest
  liveness); the observer merges it.
- **Docs** — USER_GUIDE "Ground a run on the rails" + "The rails
  journal", the SECURITY.md rails-as-material trust boundary, the
  ARCHITECTURE.md rails-as-material paragraph.

## What the trenches taught

- **`dw context` gives a receipt for free.** Every rail object already
  has a named trace path; grounding never had to parse a slug or a
  status — it reads the file the CLI points at.
- **The mesh relay queue is the wrong shape for events.** It is
  prompt/result-shaped; rail events ride their own thin push wire
  instead, scoped to the receiving half with the pushing worker
  deferred until a second machine is real.
- **Liveness reports, drain prunes.** A stale remote node reads
  `False` from `remote_node_liveness` and is removed on the next
  `drain` — the walk's beat-6 assertion had to match that two-step,
  a small honest correction.

## The handoff

- **The remote-events worker daemon** (a `holdspeak mesh serve`-style
  loop that tails a far node's `dw events` and POSTs the envelope on a
  cadence) is the one deferred rider — the receiving wire is shipped
  and proven; the pusher lands when a second rails machine is real.
- **B3 (the factory)** and **B4 (the DeskOS belt)** inherit rails-as-
  material: a new project's belt is groundable from birth, and the
  journal is a synced primitive the iPad renders like any note.

## Not done here (by design)

- No new egress: the rails read is your own `dw`; the journal is local.
- The observer never acts: it reads and journals; anything it would do
  is the existing proposal, human-approved, the gate keeping say.
- Grounding a closed phase's whole roadmap (vs a single object), and a
  distinct journal primitive kind, are deferred triggers.
