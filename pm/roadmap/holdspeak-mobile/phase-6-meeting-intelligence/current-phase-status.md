# Phase 6 — Meeting Intelligence

**Status:** in-progress (HSM-6-01 + 6-02 + 6-03 + 6-04 done 2026-06-19; the
intelligence layer + the parity harness are host-proven. 6-05 (Gate-5 verdict)
blocked on the device/dep-gated mobile inference engine — Phase 5; 6-06 Follow-ups
blocked on a cross-runtime contract decision). Track G of the Council
Implementation Charter. The artifact-generation engine: it turns a transcribed
meeting into the structured intelligence HoldSpeak is known for — Action Items,
Decisions, Risks, Requirements, Summaries, plus the charter Vision's ADR
Candidates and Follow-ups — running in the Runtime Core (Layer 2) on top of the
Phase-5 `ILLMProvider`, and held to parity with the desktop quality baseline.

**Last updated:** 2026-06-19 (**HSM-6-04 done — the parity baseline harness** — a
deterministic, phrasing-tolerant substance-coverage scorer (`ParityRubric` /
`ParityScorer` / `ParityReport`) that operationally defines the Track-G parity gate:
per-category `mustCover` facts, fact-weighted coverage vs an owner-agreed threshold
(0.8), pure/stable across reruns, per-type attribution. `swift test` 38/38. The
intelligence layer (6-01/02/03) + the harness are now host-proven. **HSM-6-05
(Gate-5 verdict) is blocked** — running a real mobile-vs-desktop parity comparison
needs an on-device `ILLMProvider` (the device/dep-gated Phase-5 inference engine);
no mobile model exists yet, so the verdict can't run. Next major thrust: the mobile
inference engine (unblocks 6-05) and/or the sync-by-default work. Earlier:
**HSM-6-03 done — ADR Candidates** — an open-blob
`Artifact(.adr)` on the HSM-6-01 seam: a candidate ties to an architectural-weight
decision, carries a `source_timestamp` to the moment + a transcript source, and is
never fabricated (no architectural decision → empty candidates). `swift test`
35/35. **Follow-ups split to HSM-6-06 (blocked)** — `artifact_type` is a closed
cross-runtime enum with no follow-up type, so it needs a contract decision (desktop
+ schema + both runtimes + fixtures); owner call was ship-ADR-now-defer-Follow-ups.
Next: HSM-6-04 (parity baseline harness). Earlier: **HSM-6-02 done** — the five core artifact types are
real on the HSM-6-01 seam: Action Items (`Artifact(.actionItems)` whose
`structured_json` is a schema-valid `[ActionItem]`, lifecycle + `sha256(task:owner)[:12]`
id stamped by the engine), Decisions/Risks/Requirements (open-blob `Artifact`s via
per-type desktop-intent prompts), and Summary → `IntelSnapshot` (no invented
`summary` artifact type — contract-honest). Empty input → empty set, never
hallucinated. Also fixed a Phase-5 `extractJSON` bug (it grabbed the first inner
object of an array). `swift test` 33/33, layer guard green. Next: HSM-6-03 (ADR
Candidates + Follow-ups). Earlier: **HSM-6-01 done** — the artifact-generation engine
seam lands in the Runtime Core: `ArtifactGenerationEngine` takes a Phase-0
`Transcript` + an injected `ILLMProvider`, drives the model, decodes via the
Phase-5 `StructuredOutput` bridge into an `ArtifactDraft`, and binds it into a
schema-valid Phase-0 `Artifact` (engine stamps id/type/provenance; model
contributes only the intelligence). Propose-only (`.draft`), robust to prose
output (recoverable error, per-type batch resilience). `swift test` 28/28, layer
guard green. Added public inits to `Artifact`/`ArtifactSource`/`Transcript`;
`RuntimeCore` now depends on `Providers` for the port protocols (transitive-dep
risk flagged for Phase 3 — see Decisions deferred). Concrete per-type prompts are
HSM-6-02/03. Earlier: scaffolded — stories HSM-6-01..05 stubbed).

## Goal

Build the meeting-intelligence engine in the Runtime Core: consume a finished
transcript and the Phase-5 `ILLMProvider`, and emit the Phase-0 contract shapes
(`Artifact`, `ActionItem`, `Decision`, `Risk`, `Requirement`) plus the Vision's
ADR Candidates and Follow-ups, all as structured JSON, at quality on par with
the shipped desktop product. The model never acts on its own — the Propose →
Review → Approve → Execute lifecycle is preserved end to end.

## Scope

- **In:** the Runtime-Core artifact-generation engine that drives `ILLMProvider`
  and binds output to the Phase-0 contracts as structured JSON (HSM-6-01); the
  five core artifact types — Action Items, Decisions, Risks, Requirements,
  Summaries — each mapped to its contract (HSM-6-02); ADR Candidates and
  Follow-ups, the charter Vision extras (HSM-6-03); a comparison harness that
  judges mobile output against the desktop quality baseline on substance, not
  exact wording (HSM-6-04); the Gate-5 closeout that measures and records parity
  with the desktop baseline (HSM-6-05).
- **Out:** the `ILLMProvider` implementation and local-inference engine itself
  (Phase 5). MIR profiles and profile-driven extraction differences (Phase 7).
  Any UI for reviewing or approving artifacts (Phases 8–9). Execution of accepted
  actions / connectors — the engine only emits proposals; the Approve → Execute
  half stays the host's job. The desktop product's own intelligence code (this
  phase reads it as the baseline; it does not change it).

## Exit criteria (evidence required)

- [ ] The Runtime-Core artifact-generation engine produces, from a transcript +
      `ILLMProvider`, valid structured JSON that conforms to the Phase-0
      `Artifact`/`ActionItem`/`Decision`/`Risk`/`Requirement` schemas with zero
      schema errors on a real meeting (HSM-6-01).
- [ ] Each of the five core artifact types is generated and round-trips against
      its Phase-0 contract; the engine emits nothing the contract can't hold
      (HSM-6-02).
- [ ] ADR Candidates and Follow-ups are generated as their own artifact shapes
      and validate against the Phase-0 `Artifact` contract (HSM-6-03).
- [ ] A parity harness exists that compares mobile output to a captured desktop
      baseline on substance (artifact presence, type, coverage of the
      decisions/actions actually in the transcript), not on exact strings, and
      runs repeatably despite non-deterministic generation (HSM-6-04).
- [ ] **Track G gate — parity with desktop quality baseline:** the harness
      reports mobile artifact quality at parity with the desktop baseline on the
      agreed baseline meetings, with the measured result recorded; Gate 5 passes
      (HSM-6-05).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HSM-6-01 | The artifact-generation engine | done | [story-01](./story-01-artifact-generation-engine.md) | [evidence-01](./evidence-story-01.md) |
| HSM-6-02 | The five core artifact types | done | [story-02](./story-02-core-artifact-types.md) | [evidence-02](./evidence-story-02.md) |
| HSM-6-03 | ADR Candidates (Follow-ups split to 6-06) | done | [story-03](./story-03-adr-candidates-followups.md) | [evidence-03](./evidence-story-03.md) |
| HSM-6-04 | The parity baseline harness | done | [story-04](./story-04-parity-baseline-harness.md) | [evidence-04](./evidence-story-04.md) |
| HSM-6-05 | Gate-5 parity closeout | blocked | [story-05](./story-05-parity-closeout.md) | — |
| HSM-6-06 | Follow-ups | blocked | [story-06](./story-06-followups.md) | — |

## Where we are

**HSM-6-01 is done.** The artifact-generation engine seam lives in the Runtime
Core (`ArtifactGenerationEngine`): it takes a Phase-0 `Transcript` + an injected
`ILLMProvider`, builds a per-type prompt (a generic schema-hinted default;
HSM-6-02/03 inject the concrete ones), drives the model through the Phase-5
`StructuredOutput` bridge to decode an `ArtifactDraft`, and binds that into a
schema-valid Phase-0 `Artifact` — the engine owns the discriminator/identity/
provenance, the model owns only the intelligence. Propose-only (`.draft`); prose
output surfaces as a recoverable error and one bad type doesn't sink a batch.
`swift test` 33/33, layer guard green. **HSM-6-02 is also done** — the five core
types are real on the seam (Action Items typed to `[ActionItem]`; Decisions / Risks
/ Requirements as open-blob `Artifact`s; Summary as `IntelSnapshot`), contract-honest
(no invented `summary` type), empty-input-safe. The remaining stories: the Vision
extras: **HSM-6-03 (ADR Candidates) is done** on the seam; **Follow-ups split to
HSM-6-06 (blocked** on a `follow_up` artifact-type contract decision — see Decisions
deferred). **HSM-6-04 is done** — the parity harness operationally defines the gate
(substance coverage, per-type, threshold 0.8, deterministic). What remains in
Phase 6 is **HSM-6-05 (the Gate-5 verdict)**, which is **blocked**: a real
mobile-vs-desktop parity comparison needs an on-device `ILLMProvider` to generate
mobile artifacts — that is the device/dep-gated Phase-5 inference engine, and no
mobile model exists yet. So Phase 6's intelligence + harness are host-proven, but
the verdict awaits the on-device engine. **Next** is therefore either the **mobile
inference engine** (unblocks 6-05) or the owner's **sync-by-default** thrust
(see the program README / Phase 10); HSM-6-06 (Follow-ups) stays blocked on the
cross-runtime `follow_up` type.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Intel is non-deterministic — the same transcript yields different wording every run, so any exact-string assertion is flaky | high | Judge substance, never exact strings — assert artifact presence, type, and coverage of what's actually in the transcript; tolerate phrasing variance | A test asserts an exact artifact string and goes red on a rerun — rewrite it as a substance check, don't pin the model |
| "Parity with desktop" has no number — parity is undefined until it's measured | high | HSM-6-04 defines parity operationally (a fixed baseline-meeting set + a substance rubric) before HSM-6-05 judges against it | The closeout can't say whether parity was met because no rubric exists — stop, define the rubric in HSM-6-04 first |
| A 4B/8B mobile model underperforms the desktop baseline on artifact quality | medium | Measure the gap with the harness; if real, surface it to the owner as a Gate-5 finding (model tier, prompt, or gate-bar decision) rather than hiding it | Parity is repeatedly missed on the same artifact type across baseline meetings — escalate; it's a model/prompt decision, not a test bug |
| The engine emits a shape the Phase-0 contract can't hold | medium | Bind output to the contracts in HSM-6-01 and validate every artifact; treat a mismatch as a contract question, not a local hack | An artifact needs a field the contract lacks — escalate to the Phase-0 contract, don't fork the shape |
| The Propose→Review→Approve→Execute boundary erodes — the engine starts implying action | low | The engine emits proposals only; no execution path lives in this phase (charter non-goal: no agentic automation) | Any code in this phase calls an executor or connector — remove it; that's Phase 8–9/host territory |

## Decisions made (this phase)

- 2026-06-18 — Parity is judged on substance, never on exact strings: intel is
  non-deterministic, so the acceptance bar is artifact presence/type/coverage
  against the transcript, not phrasing — charter Track G ("parity with desktop
  quality baseline") + repo convention (intel tests judge substance).

## Decisions deferred

- The operational parity rubric (which baseline meetings, what counts as
  "covered", the pass threshold) — trigger: HSM-6-04 — default: a small fixed set
  of captured desktop meetings + a per-artifact-type coverage rubric, agreed with
  the owner before HSM-6-05 runs.
- What happens if a mobile model can't reach parity at the chosen tier (raise the
  tier, tune the prompt, or move the gate bar) — trigger: HSM-6-05 measures a real
  gap — default: surface the measured gap to the owner as a Gate-5 finding; do not
  silently relax the gate.
- Whether ADR Candidates and Follow-ups are full `Artifact` subtypes or a
  distinct shape — trigger: HSM-6-03 — default: model them as `Artifact` types per
  the Phase-0 contract until the contract says otherwise.
- **How to keep the heavy adapter deps out of the domain.** HSM-6-01 made
  `RuntimeCore` depend on `Providers` (the port protocols live there). Trigger:
  **HSM-3-01** adds the WhisperKit SPM dependency to the `Providers` target —
  which would then transitively link a transcription engine into `RuntimeCore`
  and its tests. Default: at Phase 3, split a dependency-free `ProviderInterfaces`
  target (the `I*` protocols) that both `RuntimeCore` and the concrete `Providers`
  adapters depend on, so the domain never links WhisperKit/llama.cpp. Cheap to do
  now, cheaper than after more RuntimeCore code piles on the current edge.
