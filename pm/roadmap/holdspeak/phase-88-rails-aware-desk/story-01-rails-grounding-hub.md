# HS-88-01 — Rails objects as grounding kinds: the hub hydration seam

- **Project:** holdspeak
- **Phase:** 88
- **Status:** done
- **Depends on:** none (consumes Phase-87 `hydrate_refs`)
- **Unblocks:** HS-88-02
- **Owner:** unassigned

## Problem

The desk can ground a meeting or an artifact into a run; it cannot
ground the rails. An open story, its phase, its evidence, the roadmap
README — these are the material the owner actually reasons over, and
they should hydrate into a run exactly like a meeting does: labeled,
capped, and as a RECEIPT (the CLI names the path), never a markdown
scrape.

## Scope

- In: extend `holdspeak/grounding.py` — a `hydrate_rails_refs(refs,
  *, runner)` that resolves each `{repo, project, kind, id}`
  (`kind ∈ {phase, story, evidence, roadmap}`) to a file path via
  `missioncontrol_bridge` + `dw context`, reads the contained file,
  and returns the SAME `GroundingBlock` type the meeting/artifact path
  returns (`kind="rails:<kind>"`, a provenance subtitle naming the
  repo/project, the file's text, capped + cut-marked); unknown or
  unreachable refs come back named. `compose_steer` and the ask
  envelope consume these blocks unchanged.
- Out: the picker UI (02); the observer (03); grounding a whole
  roadmap's every phase (a roadmap ref hydrates the README only —
  the deferred decision); re-deriving any rail STATE from markdown.

## Acceptance criteria

- [ ] A story ref hydrates to a `GroundingBlock` whose text is the
      story file's contents and whose subtitle names `repo/project` —
      byte-identical in shape to a meeting block (a parity test pins
      it against `hydrate_refs`).
- [ ] Phase (`current-phase-status.md`), evidence
      (`evidence-story-NN.md`), and roadmap (`README.md`) refs each
      resolve through the SAME `dw context` path lookup; the path is
      NAMED by the CLI, never guessed from a slug.
- [ ] An unknown ref (bad id, repo not in the map, `dw` unavailable)
      refuses by name — a typed `unknown`/`unavailable`, never a
      partial best-effort block.
- [ ] Over-cap rail content is cut and MARKED (the meeting-transcript
      cut posture), never silently truncated.
- [ ] No rail STATE is parsed from the markdown body — the resolver
      reads the file as opaque text; a grep test forbids `Status:`/
      status-regex parsing in the rails hydration path.
- [ ] Full suite green (read from the file); the ask/steer suites
      that exercise hydration pass unmodified.

## Test plan

- Unit: `tests/unit/test_grounding_rails.py` — fake runner returning a
  `dw context` document + a temp repo tree; resolution for each kind,
  unknown/unavailable refusals, the cap+cut, the parity-with-meeting
  shape.
- Integration: a live `dw context` against THIS repo, grounding a real
  open story file (captured).
- Manual / device: ground HS-88-01 itself into an ask on the desk.

## Implementation direction

- **The receipt lookup:** reuse `missioncontrol_bridge.dw_argv_base`
  and the injectable runner; `dw context <project>` (JSON) names each
  story's `trace` (`story`, `evidence`, `phase_status`, `readme`) and
  each phase's `status_file`/`path`. Resolve `{kind, id}` → the trace
  path, read the file bytes, decode `errors="replace"`.
- **One block type:** return `GroundingBlock` (the Phase-87 dataclass)
  so `compose_steer` and the ask envelope need zero changes; the
  provenance header the steer already prints
  (`--- from rails:story: "HS-88-01" (holdspeak) ---`) falls out for
  free.
- **Caps:** reuse `GROUNDING_TRANSCRIPT_CAP` for the per-object cut;
  the roadmap README is the largest — cut + mark like a transcript.
- **The wire:** the ask/steer grounding object grows a `rails: [refs]`
  key beside `meeting_ids`/`artifact_ids`; hydration folds rails
  blocks in after the meeting/artifact blocks, one ordered list.
