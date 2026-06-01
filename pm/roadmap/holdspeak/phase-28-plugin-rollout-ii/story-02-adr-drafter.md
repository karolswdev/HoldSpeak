# HS-28-02 — `adr_drafter` real run (ADRs)

- **Project:** holdspeak
- **Phase:** 28
- **Status:** backlog
- **Depends on:** HS-28-01 (registry)
- **Unblocks:** HS-28-05
- **Owner:** unassigned

## Problem

`adr_drafter` is registered (`kind="artifact_generator"`, `artifact_type="adr"`)
but is still a `DeterministicPlugin` stub. ADRs (Architecture Decision Records)
are the natural companion to `mermaid_architecture` on architecture meetings — the
RFC's recommended first slice paired them. When a team settles an architectural
question ("Postgres over Dynamo because…"), the durable output is an ADR: context,
the decision, status, and consequences.

## Scope

### In

- Real `AdrDrafterPlugin` (deferred, `required_capabilities=["llm"]`), registered
  in `_REAL_PLUGINS` in place of the stub. Mirror
  `holdspeak/plugins/builtin/requirements_extractor.py`.
- Output: `{"summary", "confidence_hint", "active_intents", "adrs": [{"title",
  "status": "proposed"|"accepted"|"rejected"|"superseded"|"deprecated",
  "context", "decision", "consequences"}]}`. Validate; `status` enum coerced with
  a safe `proposed` fallback; success when ≥1 well-formed ADR, else clean failure.
- Registry body (HS-28-01) for `adr` + `structured_json["adrs"]`.
- Structured `/history` render: per ADR, a title + status pill + Context / Decision
  / Consequences sections (`adrsFor(artifact)` helper + `x-for`). Rebuild web.
- Unit + synthesis tests (mirror HS-27-04); extend the spoken e2e + screenshot.

### Out

- ADR file export to a repo `docs/adr/` tree (later; this is an artifact, not a
  filesystem writer).
- Status transitions tied to user ownership (RFC open question #2) — v1 reports
  the status as the model inferred it.

## Acceptance criteria

- [ ] Real `run()` returns the validated `adrs` payload; failure + capability-
      blocked paths covered.
- [ ] `register_builtin_plugins` returns the real class for `adr_drafter`; others
      unaffected. (No routing ripple — already on the architect/architecture chains.)
- [ ] `adr` artifacts render structured in `/history` (status pill + sections).
- [ ] Tests green; full sweep green; verified live on `.43` Q6.

## Test plan

- Unit: `tests/unit/test_adr_drafter_plugin.py` (mock intel) — success, multi-ADR,
  bad-status fallback, empty → failure, unparseable → failure, no-transcript,
  provider-raises, registrar, capability-blocked.
- Synthesis: an `adr` body case in `test_artifact_synthesis_diagram.py`.
- Full sweep; live `.43` against an architecture-decision transcript.

## Notes / open questions

- Strict prompt, defensive parser (extract fenced JSON, validate the status enum).
- An ADR is usually one-decision-per-record but a meeting can settle several →
  return a list.
