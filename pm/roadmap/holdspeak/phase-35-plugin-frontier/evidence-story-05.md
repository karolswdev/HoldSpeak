# Evidence — HS-35-05 (Phase closeout + final-summary)

**Shipped:** 2026-06-04. Phase 35 verified end-to-end and closed; `final-summary.md`
written, project README phase row flipped to `done`, HANDOVER pickup pointer refreshed
to tee up Phase 36 — Actuators.

## Routing invariants re-verified (the 14 built-ins unchanged)

```
$ uv run pytest -q tests/unit/test_intent_dispatch.py tests/unit/test_intent_router.py \
    tests/unit/test_plugin_disable.py tests/unit/test_plugin_sdk.py \
    tests/unit/test_plugin_pack_loader.py
54 passed in 0.11s
```

`test_intent_dispatch.py` / `test_intent_router.py` are **unchanged and green** — the
built `RouteDecision.plugin_chain` for the 14 built-ins is byte-identical. The plugin
packs (`plugin_sdk` / `plugin_pack_loader`) and the per-project disable gate (`skipped`
status) layer *around* the built chain, not into it.

## Doc truth

```
$ uv run pytest -q -k "doc_drift or dangling_relative_link"
3 passed, 1 skipped, 2034 deselected
```

Drift-guard + the live-doc relative-link check green after the roadmap/HANDOVER edits.
The 1 skip is the opt-in spoken-e2e module (no `HOLDSPEAK_SPOKEN_E2E=1`).
`docs/PLUGIN_AUTHORING.md` matches the shipped pack/enable surface and is linked from
`docs/README.md` + the root README plugin section.

## Ruff + full suite

```
$ uv run ruff check holdspeak/plugin_sdk.py holdspeak/plugin_pack_loader.py \
    holdspeak/plugin_packs/ tests/e2e/test_spoken_meeting_e2e.py
All checks passed!

$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2007 passed, 15 skipped in 58.38s
```

## Carried follow-up (NOT fixed here — foundation-hardening)

Surfaced while verifying HS-35-04: `Config.load()` parses each sub-config as
`MeetingConfig(**data)` inside a broad `except Exception: return cls()`. A single
unknown/legacy key (found live: the HS-32-06-retired `meeting.web_enabled`) makes the
**entire** config silently fall back to defaults — a configured `intel_cloud_base_url`
(`.43`) is ignored on every load with no error. Recorded in `final-summary.md` +
`HANDOVER.md` for the user to schedule; out of the plugin-frontier scope.

## Phase state at close

- 5/5 stories `done`; `final-summary.md` written.
- Suite green 2007/15; plugin-frontier modules ruff/F821 clean; built-in routing
  unchanged.
- Branch `phase-35/hs-35-01-plugin-authoring-guide` (phase open + 5 story commits) —
  ready to open a PR to `main`.
- Next: Phase 36 — Actuators (not yet scaffolded).
