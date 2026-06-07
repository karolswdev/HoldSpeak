# Phase 47 — Project Knowledge: Legible & Inviting

**Status:** PLANNING (0/6). Opened 2026-06-07 on user direction — while reviewing
the Phase-46 docs, the user said: *"I struggle to understand the 'project KB' …
and I feel like many users will also struggle. It's not only about documentation,
but also the UI/UX, and the way to present it."* Confirmed by the doc-fix attempt
itself getting the concept **wrong** (see the thesis).

**Last updated:** 2026-06-07 (phase scaffolded off the Phase-46 finding. HS-47-01 —
the concept & naming reconciliation — is the entry point; everything else builds on
the model it settles.)

## The thesis — why this phase

**HoldSpeak has a genuinely powerful "teach the copilot about this project"
capability — and it's hidden behind jargon and a confusing split.** Grounded in
the live tree (not vibes):

- **The term "project KB" is overloaded, and the two things it could mean are
  *different mechanisms*.** `/dictation` shows **two adjacent tabs**:
  - **"Project KB"** (`section-kb`) edits a `kb:` key-value map in
    `<repo>/.holdspeak/project.yaml`; its keys become `{project.kb.<key>}`
    placeholders that the **default `kb-enricher`** stage substitutes into a block
    template — **deterministic, no LLM** (`holdspeak/plugins/dictation/builtin/
    kb_enricher.py`, `project_kb.py`).
  - **"Project Context"** (`section-hs`) edits the **`.hs/` Markdown folder**
    (`instructions`/`context`/`workflows`/`targets`/`ignore`), read by the
    **optional `project-rewriter`** (LLM) stage.
  Two names a syllable apart, two file homes, two pipeline stages, two enablement
  defaults — and **no in-app explanation** of what either is, why you'd use one,
  or how they relate.
- **The confusion is provable.** The Phase-46 docs pass — by an attentive agent —
  *defined "project KB" as the `.hs/` files*, which is wrong. The Intelligent
  Typing guide documented `.hs/` at length but **never documented the real
  (project.yaml) KB at all**. If the docs author conflates them, a user has no
  chance.
- **The surfaces are bare.** The tabs are editors (a key/value grid; a Markdown
  textarea) with a terse `<p>` lede and a "Use starter" button — no plain "what is
  this / why / show me an example," no inviting empty state, no guided path from a
  fresh repo to working project-aware dictation. The feature is for people who
  *already know it exists and what it does*.
- **It's undiscoverable.** Nothing nudges a user dictating into a detected project
  toward setting up project knowledge; you find it only by clicking an opaque tab.

This phase makes project knowledge **legible** (a user understands what it is in
seconds) and **inviting** (a user can set one up from the UI without reading a
guide or hand-editing files) — naming, framing, explainers, empty states, a guided
flow, and discovery.

## Goal

Turn "project KB / project context" from an expert-only, easily-confused pair of
editors into a **legible, inviting, discoverable** capability: clear names, a
plain-language model of the two parts and how they help, real teaching empty
states, a guided setup flow (fresh repo → working project-aware dictation, no file
editing), and an honest nudge that helps users find it — held to the Phase-43+ UX
bar.

## Scope

- **In:** a **concept & naming reconciliation** (settle the canonical model + names
  for the project.yaml KB vs the `.hs/` context, and apply the label changes); an
  **in-app explainer + inviting empty states** on both surfaces (what / why / an
  example; a teaching empty state, not a blank grid); a **guided setup flow**
  (create the `.hs/` defaults + a `project.yaml` KB starter from the UI, with a
  detected project root); a **discovery nudge** (ambient, dismissible, never naggy
  — surface project knowledge where a user would benefit); a **docs alignment** pass
  (document *both* mechanisms correctly, matching the new framing — the real KB is
  currently undocumented in the guide); a **closeout** (before/after, dogfood,
  `final-summary.md`, PR).
- **Out:** changing the *pipeline behavior* (the stages, substitution, and rewrite
  semantics stay — this is legibility/UX over the existing mechanisms, not a
  re-architecture); new pixellab art; renaming the underlying files/config keys on
  disk unless HS-47-01 explicitly decides it's worth the churn (default: keep
  `.holdspeak/project.yaml` + `.hs/` on disk, change only the *presentation*);
  meeting-side intel.

## Exit criteria (evidence required)

- A concept/naming decision is recorded and applied: the UI no longer presents two
  bare, easily-confused tabs without a stated relationship; the names + framing are
  settled and consistent across UI + docs. (HS-47-01)
- Both surfaces carry an in-app explainer (what / why / example) and an inviting,
  teaching **empty state** with a one-click starter. (HS-47-02)
- A guided setup flow takes a detected project from nothing → working project-aware
  dictation **without hand-editing files**; proven by a dogfood. (HS-47-03)
- An honest, dismissible discovery nudge surfaces project knowledge where it helps,
  off by default / never naggy, focus-safe. (HS-47-04)
- The docs document **both** mechanisms correctly (KB = `project.yaml`; context =
  `.hs/`), matching the new framing; doc-drift + link guards green. (HS-47-05)
- Before/after captured; dogfood green; `final-summary.md`; phase CLOSED; PR to
  `main`. (HS-47-06)

## Invariants

- **Behavior-preserving for the pipeline.** The `kb-enricher` substitution and the
  `project-rewriter` rewrite are unchanged; this phase changes *presentation,
  framing, and onboarding*, not what the stages do. Pipeline tests stay green.
- **Honest.** The two mechanisms are described accurately (the Phase-46 lesson);
  no surface implies the KB does what context does or vice-versa; "no LLM" /
  "optional LLM stage" stated where true.
- **Local-first & focus-safe.** Everything stays local; any nudge is dismissible,
  never steals keyboard focus, and respects the off-by-default posture.
- **UX bar.** Apply the Phase-43/44 "Signal" premium language via the
  `ui-ux-pro-max` skill; no bare grids or flat empty states (the standing
  high-UI-standards rule).
- **No file churn by default.** Keep `.holdspeak/project.yaml` + `.hs/` on disk as-is
  unless HS-47-01 explicitly justifies a rename + migration.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-47-01 | Concept & naming reconciliation (the model) | backlog | [story-01-concept-and-naming.md](./story-01-concept-and-naming.md) | — |
| HS-47-02 | In-app explainer + inviting empty states | backlog | [story-02-explainer-empty-states.md](./story-02-explainer-empty-states.md) | — |
| HS-47-03 | Guided setup flow (fresh repo → working) | backlog | [story-03-guided-setup-flow.md](./story-03-guided-setup-flow.md) | — |
| HS-47-04 | Discovery nudge (find it where it helps) | backlog | [story-04-discovery-nudge.md](./story-04-discovery-nudge.md) | — |
| HS-47-05 | Docs alignment (both mechanisms, correctly) | backlog | [story-05-docs-alignment.md](./story-05-docs-alignment.md) | — |
| HS-47-06 | Closeout — before/after + dogfood + PR | backlog | [story-06-closeout.md](./story-06-closeout.md) | — |

## Where we are

Scaffolded off the Phase-46 documentation lift, which surfaced (and stumbled on)
the project-KB overload. Nothing built yet. **Read
[`AGENT-BRIEF.md`](./AGENT-BRIEF.md) first** — it has the mission, the mapped code
seams, the rules of the road, and per-story success criteria. **HS-47-01** (settle
the concept + names) is the foundation — every other surface presents the model it
decides. Sequence: 01 → 02 → (03, 04) → 05 → 06. Phase 46 is CLOSED + merged
(PR #25); the docs humanize pass merged too (PR #26).

## Active risks

- **Bikeshedding the names.** Mitigation: HS-47-01 makes one decision, records the
  rationale, and moves on; the default is to keep on-disk names and fix only
  presentation.
- **Scope creep into a pipeline redesign.** Mitigation: the behavior-preserving
  invariant; this is legibility/onboarding over the existing mechanisms.
- **A naggy nudge.** Mitigation: dismissible + off-by-default + focus-safe, designed
  in (HS-47-04), mirroring the presence/onboarding posture.
- **Re-confusing the docs.** Mitigation: HS-47-05 + the Phase-46 doc guards +
  `DOCS_STYLE.md` glossary entry (already corrected) as the source of truth.

## Decisions made (this phase, from user)

- **Split from Phase 46.** The docs-side clarity fix landed in Phase 46 (HS-46-05);
  the product/UX legibility is this dedicated phase (user chose "new phase + docs
  fix now").

## Decisions deferred

- **Rename vs. keep "Project KB" / "Project Context".** Whether to rename the tabs
  (and/or unify them under one umbrella with two clearly-labelled parts) or keep
  the names with strong framing — settle in HS-47-01.
- **On-disk renames.** Whether to touch `.holdspeak/project.yaml` / `.hs/` on disk
  at all (default: no) — settle in HS-47-01.
