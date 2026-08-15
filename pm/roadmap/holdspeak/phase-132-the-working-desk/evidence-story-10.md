# Evidence - HS-132-10

- **Story:** HS-132-10 - One meetings placement dial
- **Status:** done
- **Date:** 2026-08-15

## Proof

### Captured run — 2026-08-15T22:55:07Z

- **Command:** `env HOME=/tmp/hs132-10-home uv run pytest -q tests/unit/test_meeting_placement_policy.py tests/unit/test_receipt_model_honesty.py tests/integration/test_settings_placement_provenance.py tests/integration/test_settings_version_guard.py tests/unit/test_one_dial.py --tb=short`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 8cc3130e1c9e925b7591642c2043b7c0dbecd08c

```text
.............................................................            [100%]
61 passed in 12.23s
```

## Orchestrator notes

- Web proof (not in the captured run): settingsModels 14 vitest green
  (8 new: one per placement state, the rule line, the exactly-one-decider
  assertion, the provider write path); tsc clean under the orchestrator.
- Design shipped: the Meetings destination pointer (Models > Runs on) is
  the dial; the Provider cycle left Prefs and sits beneath it as a
  subordinate fallback; exactly one row reads DECIDES PLACEMENT and it is
  the one the hub obeys; PROVIDER SELECTION IGNORED lamp names the
  adopted destination; the rule renders in one line. Provenance rides
  /api/settings as _placement.meeting and is stripped before persist so
  an echoing client can never write the describer.
- Round trip proven: after the PUT, resolve_meeting_placement resolves to
  the pointed destination's base_url; clearing the pointer hands the
  decision back to the provider.
- Ledger (recorded, unfixed): the backend constant
  PLACEMENT_PROVIDER_OVERRIDDEN actually means the DESTINATION pointer
  was dropped and the provider decided — the name reads backwards; UI
  maps to semantics; rename candidate for a later slice.
