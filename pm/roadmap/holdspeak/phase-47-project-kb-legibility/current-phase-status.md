# Phase 47 — Project Knowledge: Legible & Inviting

**Status:** IN PROGRESS (2/6). Opened 2026-06-07 on user direction — while reviewing
the Phase-46 docs, the user said: *"I struggle to understand the 'project KB' …
and I feel like many users will also struggle. It's not only about documentation,
but also the UI/UX, and the way to present it."* Confirmed by the doc-fix attempt
itself getting the concept **wrong** (see the thesis).

**Last updated:** 2026-06-07 (HS-47-02 shipped. Both surfaces now teach: a
what/why/worked-example **explainer** on each (Facts shows a `{project.kb.stack}`
substitution; Context shows a rewrite being shaped), plus an inviting **empty
state** with a one-click starter (Facts → "Use starter facts"; Context → "Start
with an example", which loads an unsaved example to review and save). Static
markup toggled by JS to dodge the scoped-CSS trap; screenshot-verified;
focus-safe (0 `.focus()` in the bundle). Full suite 2367/17. Next: HS-47-03
(guided setup, which carries the copiable "draft my `.hs/` with your coding
agent" prompt) + HS-47-04 (discovery nudge).)

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
| HS-47-01 | Concept & naming reconciliation (the model) | done | [story-01-concept-and-naming.md](./story-01-concept-and-naming.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-47-02 | In-app explainer + inviting empty states | done | [story-02-explainer-empty-states.md](./story-02-explainer-empty-states.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-47-03 | Guided setup flow (fresh repo → working) | backlog | [story-03-guided-setup-flow.md](./story-03-guided-setup-flow.md) | — |
| HS-47-04 | Discovery nudge (find it where it helps) | backlog | [story-04-discovery-nudge.md](./story-04-discovery-nudge.md) | — |
| HS-47-05 | Docs alignment (both mechanisms, correctly) | backlog | [story-05-docs-alignment.md](./story-05-docs-alignment.md) | — |
| HS-47-06 | Closeout — before/after + dogfood + PR | backlog | [story-06-closeout.md](./story-06-closeout.md) | — |

## Where we are

**HS-47-01 is done.** The model is settled and recorded in
[`decision-concept-and-naming.md`](./decision-concept-and-naming.md): project
knowledge = **Facts** (the `project.yaml` `kb:` map, stamped into templates
verbatim by `kb-enricher`, no LLM) + **Context** (the `.hs/` files, read by the
optional `project-rewriter` stage). The `/dictation` "Project KB" tab is now
"Project Facts"; both tab ledes, the readiness card, and the `DOCS_STYLE.md`
glossary all name the umbrella and state the relationship. On-disk names and
pipeline behavior are unchanged; full suite 2365/17, 0 tracked `_built/`.

**HS-47-02 is done.** Both surfaces present the HS-47-01 model: a
what/why/worked-example explainer (`.kn-explainer`) and a teaching empty state
(`#kb-empty` / `#hs-empty`) with a one-click starter. The empty states are static
markup toggled by JS (not `innerHTML`) so their scoped CSS applies, and they are
screenshot-verified. The Context starter loads an unsaved example for the user to
review and save, keeping the never-write-without-approval rule.

Next is **HS-47-03** (guided setup, fresh repo → working), which carries the added
user direction: a **copiable "draft my `.hs/` with your coding agent" prompt** so
users who do not know what good context looks like can have Claude or Codex author
a tailored starter set (generation stays on their machine; writes stay
approval-gated). **HS-47-04** (discovery nudge) can run alongside. Sequence:
01 ✅ → 02 ✅ → (03, 04) → 05 → 06. **Read
[`AGENT-BRIEF.md`](./AGENT-BRIEF.md)** for the mapped code seams and rules of the
road. Phase 46 is CLOSED + merged (PR #25); the docs humanize pass merged too
(PR #26).

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
- **The names (HS-47-01).** Umbrella **"Project knowledge"** with two parts,
  **Facts** (the KB) and **Context** (the `.hs/` files). Rename only the jargon
  half: "Project KB" tab → "Project Facts"; "Project Context" kept. Keep all
  on-disk names + config keys + `{project.kb.*}` placeholders. Rationale +
  alternatives in [`decision-concept-and-naming.md`](./decision-concept-and-naming.md).
- **"Draft with your coding agent" prompt (from user, 2026-06-07).** The setup
  flow should offer a copiable, repo-aware prompt that has the user's own agent
  (Claude/Codex) generate good starter `.hs/` files, with a worked example so the
  output is usable. Folded into HS-47-03 (scope + an acceptance criterion);
  generation stays local, writes stay approval-gated.

## Decisions deferred

- ~~**Rename vs. keep "Project KB" / "Project Context".**~~ Decided in HS-47-01:
  unified under the "Project knowledge" umbrella; "Project KB" → "Project Facts",
  "Project Context" kept.
- ~~**On-disk renames.**~~ Decided in HS-47-01: keep `.holdspeak/project.yaml` +
  `.hs/` + config keys as-is; presentation change only.
