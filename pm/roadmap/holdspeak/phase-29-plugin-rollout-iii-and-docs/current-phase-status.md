# Phase 29 — Complete the plugin rollout + public docs

**Last updated:** 2026-06-01 (HS-29-01 shipped — three delivery/product stubs flipped to real: `dependency_mapper` (`dependency_map`), `scope_guard` (`scope_review`), `customer_signal_extractor` (`customer_signals`), each with a structured `/history` render. **Ten real plugins now, four stubs.** No routing ripple. Verified live on `.43` Q6; the spoken e2e exercises ten plugins. Phase **in-progress, 1/5**).

> Lineage note: Phases 16 → 27 → 28 proved, generalized, and scaled the
> LLM-backed plugin pattern (transcript → LLM → parse/validate → structured output
> → registry body → structured web render), reaching **seven real plugins**. This
> phase finishes the job: it flips the **last seven** `DeterministicPlugin` stubs
> to real (so **zero stubs** remain) and — finally — documents the plugin system
> on the public `README.md`. Read Phase 28's `final-summary.md` §Handoff first.

## Goal

Flip the remaining seven stubs to real, grouped by meeting theme, and document the
whole plugin surface publicly. After this phase: **fourteen real plugins, zero
stubs** — every registered MIR plugin has a real `run()`, a structured artifact,
and a `/history` render. The public `README.md` gains a "Meeting intelligence
plugins" section so users know what the product actually produces.

## Scope

### In

- Real `run()` for the last seven stubs, re-using the proven pattern + the
  HS-28-01 renderer registry, grouped by theme:
  - **Delivery & product:** `dependency_mapper` (`dependency_map`), `scope_guard`
    (`scope_review`), `customer_signal_extractor` (`customer_signals`).
  - **Incident:** `incident_timeline` (`incident_timeline`), `runbook_delta`
    (`runbook_delta`).
  - **Comms:** `stakeholder_update_drafter` (`stakeholder_update`),
    `decision_announcement_drafter` (`decision_announcement`).
- A structured `/history` render for each new artifact shape (never raw
  `body_markdown`).
- Unit + synthesis tests (success / failure / capability-blocked) per plugin; a
  per-plugin **live `.43` Q6 direct check** with a theme-appropriate transcript.
- **Public docs:** a "Meeting intelligence plugins" section in `README.md` listing
  the fourteen plugins, their artifact types, and how the chain runs on saved
  meetings; a pointer to the plugin RFC.
- Phase exit: RFC reality-status table → **all fourteen ✅, zero ⚠️**;
  `final-summary.md`.

### Out

- New plugin IDs beyond the registered fourteen (`actuators`, niche packs) — future.
- External side effects (Jira/Slack/GitHub) — RFC-disabled.
- Forcing the incident/comms plugins into the shared spoken-e2e conversation (it's
  a customer-feedback kickoff — no incident, no formal comms). Those are verified
  by direct live checks + unit tests; the e2e adds only the plugins that naturally
  fire on its conversation (delivery/product).
- Hardware tracks (Phases 15 / 24 / 25).

## Exit criteria (evidence required)

- [ ] All seven remaining stubs ship a real, non-stub `run()` meeting the four
      Appendix-A bars (real LLM, structured payload, synthesis-rendered, tests for
      success/failure/blocked). `_REAL_PLUGINS` covers all fourteen IDs; **no
      `DeterministicPlugin` left** in the registrar's output.
- [ ] Each new artifact type renders structured in `/history` (not raw markdown).
- [ ] Each new plugin verified live on `.43` Q6 (direct check recorded in evidence).
- [ ] `README.md` documents the plugin system (the fourteen plugins + artifacts).
- [ ] RFC reality-status table shows fourteen ✅, zero ⚠️.
- [ ] No regressions: full sweep `uv run pytest -q --ignore=tests/e2e/test_metal.py`
      green; the spoken e2e stays opt-in/excluded.
- [ ] `final-summary.md` records the completion + the next-frontier handoff.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-29-01 | Delivery & product plugins (dependency_mapper, scope_guard, customer_signal_extractor) | done | [story-01-delivery-product-plugins.md](./story-01-delivery-product-plugins.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-29-02 | Incident plugins (incident_timeline, runbook_delta) | backlog | [story-02-incident-plugins.md](./story-02-incident-plugins.md) | — |
| HS-29-03 | Comms plugins (stakeholder_update_drafter, decision_announcement_drafter) | backlog | [story-03-comms-plugins.md](./story-03-comms-plugins.md) | — |
| HS-29-04 | Public README + plugin docs | backlog | [story-04-public-docs.md](./story-04-public-docs.md) | — |
| HS-29-05 | RFC reality-check refresh + phase exit | backlog | [story-05-phase-exit.md](./story-05-phase-exit.md) | — |

## Where we are

**Planning, 0/5.** Scaffolded 2026-06-01 after Phase 28 closed. Each story is an
**atomic chunk** (a themed group of plugins) per the PMO contract's documented-
bundling allowance — grouping by meeting profile beats seven near-identical
commits. The pattern is fully mechanized (Phase 28 `final-summary.md`): real plugin
→ `_REAL_PLUGINS` → `_ARTIFACT_TYPE_BY_PLUGIN` (all already mapped) → a renderer in
`synthesis._ARTIFACT_RENDERERS` → structured web render → unit + synthesis tests →
direct live check. **Routing note:** all seven are already in their profile/intent
chains (`dependency_mapper`/`scope_guard`/`customer_signal_extractor` on delivery/
product, `incident_timeline`/`runbook_delta` on incident, the two drafters on
comms), so flipping stub→real ripples no dispatch test.

**HS-29-01 shipped** — `dependency_mapper`, `scope_guard`,
`customer_signal_extractor` are real (ten real plugins now, four stubs); the
spoken e2e exercises ten plugins.

Pickup: **HS-29-02** (incident), then 03 (comms), 04 (docs), 05 (close).

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Grouped commits are large diffs | medium | Independent files per plugin; evidence file documents each plugin's live check. | A group's diff becomes unreviewable → split the story. |
| Niche plugins (incident/comms) parse worse on Q6 | medium | Strict prompt + defensive parser + enum coercion per plugin; per-plugin tailored live check. | Parse-failure > 40% on a plugin → demote to draft-only + document. |
| Seven new artifact shapes bloat the web detail view | low | One compact structured render per shape; the registry keeps synthesis tidy. | Render unreadable → collapse behind a per-type summary line. |

## Decisions made (this phase)

- 2026-06-01 — **Finish the rollout (zero stubs)** rather than stop at the
  high-value seven — a clean, documentable end-state for the public README. — author: Karol + agent.
- 2026-06-01 — **Group the last seven by meeting theme** (delivery/product,
  incident, comms) as atomic chunks, not one commit per plugin. — author: Karol + agent.
- 2026-06-01 — **Public README must document the plugin system** before pushing. — author: Karol.

## Decisions deferred

- (none open.)
