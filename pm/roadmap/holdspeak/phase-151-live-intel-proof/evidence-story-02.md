# Evidence - HS-151-02

- **Story:** HS-151-02 - The named-owner intel (the prompt learns people)
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-30T01:29:49Z

- **Command:** `bash -c H=$(mktemp -d); HOME=$H HOLDSPEAK_PEOPLE_KEYSTORE_FILE=$H/pk.json uv run --python 3.13.11 pytest -q tests/unit/test_hs151_honest_dispatch.py::TestNamedOwnerParsing tests/unit/test_hs151_honest_dispatch.py::TestNamedOwnerInterplay tests/unit/test_hs151_honest_dispatch.py::TestNamedOwnerCanary tests/unit/test_intel_coerce.py tests/unit/test_owner_gesture.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d065872b059b65c81c45b616964d2fc4e67b9339

```text
........................................................................ [ 67%]
...................................                                      [100%]
107 passed in 3.59s
```

## Orchestrator triage — 2026-08-30

- The second latent defect dies: the intel prompt now speaks
  named owners (`"owner": "<person's name as spoken>|Me|Remote|
  null"`) with counsel M3 verbatim — Me and Remote are the ONLY
  reserved tokens, every other string a literal person name.
  Prompt and INTEL_SCHEMA updated together (M4); shipped in the
  same lane as story 01 (shared files), flipped separately.
- Verified by my own hand: the named-owner parsing pins
  (multi-word verbatim, casing variants pass through,
  null/empty→None), the interplay pins (an intel-born named owner
  maps through the REAL gesture and gains person_label;
  Me/Remote refuse mapping — the 150 reserved contract holds
  untouched), the canary (a transcript naming "Ewa" and "Jan
  Kowalski" round-trips through the pin server into
  action_items rows, review_state=pending, owners verbatim), plus
  the coercion regression file and the 150 owner-gesture suite.
- Counsel's downstream verification stands: every owner consumer
  treats the string as opaque — no code change was needed
  anywhere but the prompt/schema.
