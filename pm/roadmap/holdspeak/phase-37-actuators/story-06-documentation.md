# HS-37-06 — Actuator documentation (project docs update)

- **Project:** holdspeak
- **Phase:** 37
- **Status:** done
- **Depends on:** HS-37-01, HS-37-02, HS-37-03, HS-37-04, HS-37-05
- **Unblocks:** HS-37-07
- **Owner:** unassigned

## Problem

Actuators are a new, externally-authorable plugin kind with a deliberate safety contract
(propose → approve → execute, audited, payload-parity, gated). None of that is documented
for plugin authors or users yet — and the existing project docs still describe actuators
as **deferred/blocked**. Until the docs catch up, the feature is effectively internal and
the doc-truth guard is at risk. This story brings **all relevant project documentation**
in line with what Phases 37-01→05 actually shipped.

This is a dedicated documentation story (per direct user ask) so the docs update is a
first-class deliverable, not a footnote in the closeout. It runs after the reference
actuator (HS-37-05) so the authoring guide can show a **real, working example**.

## Scope

- **In:**
  - **`docs/PLUGIN_AUTHORING.md`** — a new **"Actuators"** section: the `ActuatorProposal`
    contract (`target`/`action`/`preview`/`payload`/`reversible`/`required_capabilities`),
    the **propose → approve → execute** lifecycle, the `actuator` capability + the
    `allow_actuators` gate + the per-project allow-list (HS-37-04), the **payload-parity**
    and **audit** guarantees, and a worked example based on the HS-37-05 reference
    actuator. Mirrors the guide's existing structure (protocol → run pattern → gate →
    testing → "shipped" bar).
  - **`README.md`** (public surface) — note actuators in the plugin/feature framing
    (an approval-gated third kind), honestly scoped (one reference actuator; off by
    default).
  - **Doc-truth reconciliation** — update every **live** doc that still says actuators are
    *deferred / blocked / a later phase* to reflect that they're unblocked behind the
    approval gate (e.g. the `plugin_sdk` / pack-authoring references, any HANDOVER/roadmap
    canon lines that pre-date Phase 37). Frozen PMO history is left verbatim.
  - Link the new section from `docs/README.md` if the index needs it.
  - Keep the **doc drift-guard** + the **live-doc link-check** green (update them in
    lockstep if a guarded phrase legitimately changes).
- **Out:**
  - The egress-posture review + `final-summary.md` + README phase-row flip — those are the
    closeout (HS-37-07).
  - New code or behavior change — this is documentation only.

## Acceptance criteria

- [x] `docs/PLUGIN_AUTHORING.md` has an **Actuators** section: the propose → approve →
      execute diagram, the `ActuatorProposal` field table, the lifecycle + the three gates
      (capability / human approval / `MeetingConfig`), the `ActuatorExecutor` (parity +
      audit), and a worked example built on `followup_ticket_actuator` (+ the outbox
      connector + the wiring) with links to the real modules + the e2e test.
- [x] The public `README.md` plugin section gains an actuators paragraph (the third kind,
      approval-gated, off by default, `followup_ticket_actuator` as the worked example,
      linked to the new section).
- [x] No **live** doc still claims actuators are deferred/blocked — the four stale
      `PLUGIN_AUTHORING.md` claims (kind table "_none shipped_", "deferred to a future
      phase", "not a valid kind yet", the Out-of-scope bullet) are reconciled. (The
      `docs/evidence/**` + MIR-01 "disabled by default" lines are left: the former is
      frozen history, the latter remains *true* — the master gate is off by default.)
- [x] Doc drift-guard + live-doc link-check green; full suite green (2080/15).

## Test plan

- `uv run pytest -q --ignore=tests/e2e/test_metal.py` — green (incl.
  `test_doc_drift_guard.py` + the live-doc link-check).
- Manual: read the new authoring section end-to-end against the shipped code; verify the
  worked example's API/field names match `holdspeak/plugins/actuators.py` + the reference
  actuator.

## Notes / open questions

- Grep first for stale claims: `actuator.*defer`, `actuator.*block`, "later phase",
  "Phase 36" (the old deferral target) across `docs/`, `README.md`, `CLAUDE.md`, and the
  source-canon list — fix the **live** ones, leave frozen PMO records.
- Keep the authoring guide consistent with `docs/CONNECTOR_DEVELOPMENT.md`'s shape (the
  two ecosystems read the same).
