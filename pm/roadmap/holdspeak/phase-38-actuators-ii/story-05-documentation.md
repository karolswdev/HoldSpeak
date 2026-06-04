# HS-38-05 — Actuators II documentation

- **Project:** holdspeak
- **Phase:** 38
- **Status:** not-started
- **Depends on:** HS-38-01, HS-38-02, HS-38-03, HS-38-04
- **Unblocks:** HS-38-06
- **Owner:** unassigned

## Problem

Phase 38 adds real external reach — write connectors (GitHub, webhook) behind a permission
manifest, and live in-meeting approval. The authoring docs still describe actuators as
local-only (the Phase-37 outbox reference) and post-meeting-only. This story brings the
docs in line so an author can write a *write* connector safely, and a user understands the
live-approval surface. (Dedicated docs story — the standing per-phase practice.)

## Scope

- **In:**
  - **`docs/PLUGIN_AUTHORING.md`** — extend the **Actuators** section with **write
    connectors**: the per-connector **permission manifest**, the `PermissionGate` mapping
    (`shell:exec` / `network:outbound`), `build_gated_connector`, and the two reference
    connectors (`gh issue create`, the webhook POST) as worked examples; and a note on
    **live proposals** (the broadcast + the live approval panel). Keep it consistent with
    `docs/CONNECTOR_DEVELOPMENT.md`.
  - **Doc-truth reconciliation** — update any live doc/section that implies actuators only
    write locally or only approve post-meeting (e.g. the Phase-37 outbox framing as "the
    only side effect"); the reference set is now outbox + GitHub + webhook.
  - Surface the new config (the webhook host allow-list) in the relevant config doc if one
    exists.
  - Keep the **doc drift-guard** + **live-doc link-check** green.
- **Out:**
  - New behavior — documentation only.

## Acceptance criteria

- [ ] `docs/PLUGIN_AUTHORING.md` documents write connectors (permission manifest + the gate
      mapping + both reference connectors as worked examples) and live proposals; matches
      the shipped surface (HS-38-01→04).
- [ ] No live doc implies actuators are local-only / post-meeting-only; the config
      additions (webhook allow-list) are documented.
- [ ] Doc drift-guard + live-doc link-check green; all new relative links resolve.
- [ ] Suite green (incl. the doc-guard tests).

## Test plan

- `uv run pytest -q --ignore=tests/e2e/test_metal.py` — green (incl.
  `test_doc_drift_guard.py`).
- Manual: read the write-connector section against the shipped connectors; verify the
  worked examples' API/field names match the code.

## Notes / open questions

- Grep first for stale "outbox" / "local file" / "saved meeting" framing that now reads as
  the *only* option; fix the live ones, leave frozen PMO/evidence history.
- Mirror Phase-37 HS-37-06's shape (contract → gates → worked example → testing).
