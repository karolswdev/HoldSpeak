# Phase 28 — Plugin rollout II: round out the core meeting types

**Last updated:** 2026-06-01 (HS-28-01 shipped — synthesis per-type **renderer registry** replaces the hand-branched body chain, behavior-preserving: the byte-for-byte synthesis tests pass unchanged. Adding a new artifact body is now register-a-renderer. Phase **in-progress, 1/5**).

> Lineage note: Phases 16 + 27 proved and generalized the LLM-backed plugin
> pattern (transcript → LLM → parse/validate → structured output → synthesis body
> → structured web render), shipping four real plugins (`mermaid_architecture`,
> `action_owner_enforcer`, `decision_capture`, `requirements_extractor`) and a
> real spoken-meeting e2e. This phase is their direct continuation: it flips the
> next three highest-value stubs and pays down the synthesis body-branch debt the
> Phase-27 `final-summary.md` flagged ("extract a per-type renderer registry once
> the fifth custom body lands"). Read Phase 27's `final-summary.md` first.

## Goal

Flip the next batch of `DeterministicPlugin` stubs to real LLM-backed plugins,
completing the **architecture / delivery / risk** meeting types that the four
shipped plugins don't yet cover: ADRs, milestone plans, and risk registers. Lead
with a behavior-preserving synthesis refactor so adding three new artifact bodies
doesn't grow an unmaintainable if/elif chain. Each new plugin ships a structured
`/history` render and is demonstrated in the existing spoken-meeting e2e.

After this phase: **seven real plugins, seven stubs.**

## Scope

### In

- A per-artifact-type **renderer registry** in `synthesis.py` replacing the
  hand-branched body chain (`diagram` / `action_items` / `decisions` /
  `requirements`), behavior-preserving — every existing body stays byte-for-byte.
- Real `run()` for three stubs, each re-using the proven pattern (strict prompt →
  fenced JSON → parse/validate → structured output → registry body → structured
  web render):
  - `adr_drafter` → `adr` artifact (architecture decision records).
  - `milestone_planner` → `milestone_plan` artifact (delivery).
  - `risk_heatmap` → `risk_register` artifact (cross-cutting risk).
- Structured web render for each new artifact shape (never the raw `body_markdown`
  path — the Phase-27 rule).
- Each plugin: unit + synthesis tests (success / failure / capability-blocked) and
  an extension of the opt-in spoken-meeting e2e + refreshed screenshot.
- Phase exit: RFC reality-status table refreshed (three more ✅), `final-summary.md`.

### Out

- The remaining seven stubs (`dependency_mapper`, `scope_guard`,
  `customer_signal_extractor`, `incident_timeline`, `runbook_delta`,
  `stakeholder_update_drafter`, `decision_announcement_drafter`) — a later phase.
- `actuators` / external side effects (Jira/Slack/GitHub) — RFC-disabled, out.
- Live-meeting plugin hooks; editing artifacts in the web UI (read-only render).
- Cross-network / hardware work (Phases 15 / 24 / 25).

## Exit criteria (evidence required)

- [x] Synthesis renderer registry lands behavior-preserving: every pre-existing
      artifact body is byte-for-byte unchanged (regression-locked tests green).
      (HS-28-01 — `evidence-story-01.md`.)
- [ ] `adr_drafter`, `milestone_planner`, `risk_heatmap` each ship a real,
      non-stub `run()` meeting all four Appendix-A bars (real LLM, structured
      payload, synthesis-rendered, tests for success/failure/blocked).
- [ ] Each new artifact type renders structured in `/history` (not raw markdown).
- [ ] The three flipped plugins are ✅ in the RFC reality-status table; the rest ⚠️.
- [ ] No regressions: full sweep `uv run pytest -q --ignore=tests/e2e/test_metal.py`
      green; the spoken e2e stays opt-in/excluded and is extended to exercise the
      new plugins.
- [ ] `final-summary.md` records which plugins shipped, per-plugin `.43` Q6
      parse-quality, and the handoff for the next plugin-rollout phase.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-28-01 | Synthesis per-type renderer registry (behavior-preserving) | done | [story-01-renderer-registry.md](./story-01-renderer-registry.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-28-02 | `adr_drafter` — real run (ADRs) | backlog | [story-02-adr-drafter.md](./story-02-adr-drafter.md) | — |
| HS-28-03 | `milestone_planner` — real run (delivery) | backlog | [story-03-milestone-planner.md](./story-03-milestone-planner.md) | — |
| HS-28-04 | `risk_heatmap` — real run (risk register) | backlog | [story-04-risk-heatmap.md](./story-04-risk-heatmap.md) | — |
| HS-28-05 | RFC reality-check refresh + phase exit | backlog | [story-05-phase-exit.md](./story-05-phase-exit.md) | — |

## Where we are

**In-progress, 1/5.** Scaffolded 2026-06-01 directly after Phase 27 closed.
**HS-28-01 shipped same day** — the synthesis renderer registry replaced the
hand-branched body chain (behavior-preserving; byte-for-byte tests unchanged), so
the three new bodies now plug in as renderers. The pattern is fully trodden (see
Phase 27's `final-summary.md` §Handoff): real plugin → `_REAL_PLUGINS` →
`_ARTIFACT_TYPE_BY_PLUGIN` (the three IDs already map to `adr` / `milestone_plan`
/ `risk_register`) → register a renderer + `structured_json` → structured web
render → unit + synthesis tests → extend the spoken e2e. **Routing note:**
`milestone_planner` rides the `delivery` chains, `adr_drafter` the
`architect`/`architecture` chains, and `risk_heatmap` the `incident` chain, but
none are in the `balanced` base chain — so flipping them to real is no routing
ripple (already routed); only a *net-new* ID added to a base chain ripples the
dispatch tests.

Pickup: **HS-28-02** (`adr_drafter`), then HS-28-03/04 (milestone/risk), then
HS-28-05 (close).

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| The registry refactor silently changes a body | medium | Behavior-preserving by construction; the byte-for-byte synthesis tests are the guard — they must pass unchanged. | Any existing synthesis test needs editing to pass → the refactor changed behavior; revert + redo. |
| ADR / milestone / risk JSON is more structured than action-items, so parse-failure rate is higher on Q6 | medium | Strict prompt + defensive parser per plugin (reuse the fenced-JSON shape); validate enums (status / impact / likelihood) with safe fallbacks. | Parse-failure > 40% on `.43` Q6 for a plugin → demote to draft-only + document. |
| Three new artifact shapes bloat the web detail view | low | One structured render per shape, mirroring decisions/requirements; the registry keeps synthesis tidy. | Render becomes unreadable → collapse behind a per-type summary line. |

## Decisions made (this phase)

- 2026-06-01 — **Lead with the renderer-registry refactor**, before adding three
  more artifact bodies, to clear the Phase-27-flagged synthesis debt. — author: Karol + agent.
- 2026-06-01 — **Round out architecture/delivery/risk** (`adr_drafter`,
  `milestone_planner`, `risk_heatmap`) over the niche long tail
  (incident/runbook/stakeholder/customer-signal). — author: Karol + agent.

## Decisions deferred

- Whether `risk_heatmap`'s artifact should also drive a literal heatmap visual
  (vs a structured table) — default to a table for v1; revisit if asked.
