# Evidence - HS-149-01

- **Story:** HS-149-01 - The honest keystore + sidecar truth (L3+L2)
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-29T18:25:23Z

- **Command:** `bash -c HOME_REAL=$HOME; HOME=$(mktemp -d) uv run --python 3.13.11 pytest -q tests/unit/test_honest_keystore.py tests/unit/test_door_read_model.py tests/unit/test_people_crypto.py tests/unit/test_people_key_custody.py tests/unit/test_people_mcp.py tests/unit/test_people_no_leaks.py tests/unit/test_people_policy.py && (cd web && npx vitest run src/desk/chair/lanes/DoorBoardLane.test.tsx)`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 051343e29e96675ef2946ab0bfc967b5056c398e

```text
........................................................................ [ 87%]
..........                                                               [100%]
82 passed in 4.03s

 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web


 Test Files  1 passed (1)
      Tests  34 passed (34)
   Start at  12:25:29
   Duration  1.63s (transform 307ms, setup 72ms, import 537ms, tests 612ms, environment 323ms)
```

## Orchestrator triage note (2026-08-29)

Custody code read line-by-line by the orchestrator (the phase's
sensitivity demands it): FileKeyStore honors the KeyStore Protocol
with the house refusal vocabulary, strict base64 + KEY_BYTES
validation, 0600 create, locking on writes; the F4 isolation is
exactly the amended spec (`<stem>.sidecar.sqlite3` beside the
keyfile — the dev world structurally cannot touch
DEFAULT_PEOPLE_DB_PATH); the composition point is env-gated with
unset = byte-identical Native path. The keyring-SPY proof is the
phase's founding artifact: a FULL People lifecycle, headless, with
zero keyring/Security calls asserted — the keychain dialog is now
structurally impossible for walks. 152 focused (106+46) + 34 web
re-run and read by the orchestrator.

**Test-update ruling:** the builder's change to
test_door_read_model's no-leak pin is an honest (a)-class update —
the old whole-JSON word check ("people" absent anywhere) was
blunter than its invariant; the new pin asserts the TRUE law (no
People CARDS in the board + the state fact correctly present).
Classified, not papered.

Also rides this commit: the owner's headless-Linux custody ledger
note (the Protocol already whitelists Secret Service; a
production-sanctioned headless keystore is a one-class future
story).
