# Phase 27 — Ubiquitous plugins + spoken-meeting e2e

**Last updated:** 2026-06-01 (scaffolded). Status: **not-started** (all stories backlog).

> Lineage note: Phase 16 (`first-real-plugin`) proved the LLM-backed plugin
> pattern end-to-end with `mermaid_architecture`. Its docs refer to "phase 17" as
> the follow-on that flips the remaining stubs — but phase 17 was already taken
> (`device-initiative`), so this follow-on is **Phase 27**. Read Phase 16's
> `final-summary.md` first; this phase is its direct continuation.

## Goal

Flip the highest-value `DeterministicPlugin` stubs to **real** LLM-backed plugins
— starting with the ones useful on *almost every* meeting, not niche ones — and
prove the whole stack with a **real spoken-meeting end-to-end harness**: a mock
meeting is synthesized with `say`, transcribed by Whisper, routed through MIR,
processed by the real plugins against the live `.43` LLM, persisted, and rendered
in the web UI — captured as screenshots.

The substrate is already proven (Phase 16); this phase is about **breadth**
(more real plugins) + **confidence** (a true e2e you can watch and screenshot).

## Scope

### In

- Real `run()` for ubiquitous stub plugins, re-using the Phase-16 pattern
  (LLM call via `resolve_intel_provider` → parse/validate → structured output →
  synthesis body → web render). Lead with the ones that fire on almost every
  meeting.
- A spoken-meeting e2e harness: `say` → wav → `Transcriber` → MIR → `PluginHost`
  → `synthesize_and_persist` → web → Puppeteer screenshots. Real endpoints
  (local Whisper + `.43` Q6 LLM), opt-in (slow), structural assertions.
- Web rendering for any new artifact *shapes* the new plugins introduce (text /
  checklist bodies render via the existing markdown path; only diagrams need the
  mermaid SVG path from HS-16-04).
- Phase exit: RFC reality-status table updated (flip the plugins shipped here),
  `final-summary.md`.

### Out

- Flipping **all** twelve remaining stubs in one phase — pick the ubiquitous
  few; the long tail (incident/runbook/stakeholder/customer-signal) is a later
  phase.
- `actuators` / external side effects (Jira/Slack/GitHub). Disabled by default
  per the RFC; out of scope.
- Live-meeting plugin hooks (running plugins during an active meeting). Saved /
  recorded meetings only, per Phase 16's carried-forward decision.
- Editing artifacts in the web UI. Read-only render.
- Cross-network / hardware work (Phase 15 / Phase 24).

## Exit criteria (evidence required)

- [ ] At least the ubiquity champion (`action_owner_enforcer`) ships a real,
      non-stub `run()` meeting all four Appendix-A bars (real downstream,
      structured payload, synthesis-rendered, tests for success/failure/blocked).
- [ ] A spoken-meeting e2e harness exists and runs against real endpoints: it
      synthesizes audio with `say`, transcribes it, runs the real plugin chain,
      persists artifacts, and captures at least one web screenshot showing a
      rendered artifact. Opt-in (skips cleanly when `say` / `.43` / Chrome
      absent).
- [ ] Every plugin flipped to real this phase is annotated ✅ in the RFC
      reality-status table; the rest stay ⚠️.
- [ ] No regressions: full sweep `uv run pytest -q --ignore=tests/e2e/test_metal.py`
      green; the new e2e is excluded from the default sweep (own marker).
- [ ] `final-summary.md` records which plugins shipped, the e2e posture, and the
      handoff for the next plugin-rollout phase.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-27-01 | `action_owner_enforcer` — real run (ubiquity champion) | backlog | [story-01-action-owner-enforcer.md](./story-01-action-owner-enforcer.md) | — |
| HS-27-02 | Spoken-meeting e2e harness (`say` → pipeline → screenshots) | backlog | [story-02-spoken-meeting-e2e.md](./story-02-spoken-meeting-e2e.md) | — |
| HS-27-03 | `decision_capture` — decisions + open questions (net-new, ubiquitous) | backlog | [story-03-decision-capture.md](./story-03-decision-capture.md) | — |
| HS-27-04 | `requirements_extractor` — real run | backlog | [story-04-requirements-extractor.md](./story-04-requirements-extractor.md) | — |
| HS-27-05 | RFC reality-check refresh + phase exit | backlog | [story-05-phase-exit.md](./story-05-phase-exit.md) | — |

## Where we are

**Scaffolded 2026-06-01**, not started. Phase 16 just closed: the
transcript→LLM→artifact→rendered-SVG path is live for one real plugin
(`mermaid_architecture`) against the `.43` Q6 endpoint. This phase broadens to the
*ubiquitous* plugins and adds the spoken e2e that demonstrates the whole stack.

Pickup order: **HS-27-01** (action_owner_enforcer — proves the pattern
generalizes to a text/checklist artifact, on the most universal meeting output),
then **HS-27-02** (the e2e harness, which then demonstrates mermaid + action
items together), then **HS-27-03 / HS-27-04** (more ubiquitous plugins), then
**HS-27-05** (close).

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| LLM output quality varies per plugin (structured JSON vs free text) | medium | Strict prompt + post-hoc validation per plugin (reject malformed); reuse mermaid's parse-then-fallback shape. | Parse-failure > 40% on `.43` Q6 for a given plugin → demote to draft-only + document. |
| `say` TTS audio transcribes poorly / unrealistically | low | TTS is clean audio; Whisper handles it well. Use multiple `say` voices for multi-speaker realism. | If Whisper WER on `say` audio is too high to route intents, hand-author the transcript and feed it directly (skip TTS) for the assertion path; keep TTS for the demo screenshot. |
| The e2e is slow + non-deterministic → flaky in CI | high | Opt-in marker (excluded from default sweep, like `test_metal.py`); assert *structure* (artifact exists, valid block) not exact text; gate on endpoint/tool availability. | If it can't be made reliable even structurally, keep it as a `make demo` script rather than a pytest test. |
| Action-item plugin overlaps the existing action-item system | medium | Scope `action_owner_enforcer` as an *artifact* (ownership-gap report) over transcript content, not a mutation of the existing action-item review tables. | If it duplicates the existing extractor, pivot to enriching existing action items instead — separate decision. |

## Decisions made (this phase)

- 2026-06-01 — **Lead with ubiquity, not visual flash.** `action_owner_enforcer`
  (every meeting has action items) over `customer_signal_extractor` (niche). The
  visual demo is still carried by `mermaid_architecture` via the e2e. — author: Karol + agent.
- 2026-06-01 — **Real spoken e2e on real endpoints**, opt-in + structural
  assertions, doubling as a living demo (screenshots). — author: Karol + agent.

## Decisions deferred

- **HS-27-03 vs HS-27-04 ordering, and whether both ship this phase.**
  `decision_capture` (decisions + open questions) is the most ubiquitous *net-new*
  plugin (needs a new `_BUILTIN_PLUGIN_DEFS` entry + artifact type);
  `requirements_extractor` is a lower-risk existing stub. Default: do
  `decision_capture` first (higher ubiquity), `requirements_extractor` if budget
  remains. Trigger to revisit: after HS-27-01/02 land and we see real per-plugin
  parse quality on `.43`.
- **Whether the e2e becomes a pytest test or a standalone demo script.** Default:
  pytest with an opt-in marker; fall back to a script if it can't be made
  structurally reliable.
