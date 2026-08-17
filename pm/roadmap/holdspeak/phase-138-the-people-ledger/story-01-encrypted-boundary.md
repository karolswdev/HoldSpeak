# HS-138-01 — The encrypted boundary

- **Project:** holdspeak
- **Phase:** 135
- **Status:** in-progress
- **Depends on:** none
- **Unblocks:** 135-02, 135-03, 135-04, 135-05
- **Owner:** delegated Terra worker; primary adjudicates

## Problem

HoldSpeak's normal database, backups, indexes, and logs are plaintext. Third-party
relationship material cannot truthfully use that plane. People needs a small,
auditable encrypted authority before any roster or note can exist.

## Scope

- **In:** AES-256-GCM envelope codec with record-bound AAD; random nonces/keys;
  native Keychain/Secret-Service custody with strict backend allow-list; memory key
  adapter for tests only; private sidecar directory/files; minimal ciphertext record
  repository; fail-closed readiness/policy states; core dependency lock.
- **Out:** recovery/export, backup, automatic rotation, sync, FTS, plaintext/env/file
  key fallback, content logging.

## Acceptance criteria

- [ ] Every sensitive payload is canonical JSON encrypted before SQLite write;
  nonce/key/record/kind substitution fails authentication.
- [ ] Production accepts only native Keychain or Secret Service; unavailable,
  locked, wrong, unsafe-permission, or corrupt states refuse without fallback.
- [ ] Store directory is owner-only; existing main-DB backup helpers never include
  People; no automatic People backup or plaintext temp file exists.
- [ ] Readiness returns stable content-free states and no paths/key material/counts.

## Test plan

- **Unit:** `tests/unit/test_people_crypto.py`, `test_people_key_custody.py`,
  `test_people_policy.py`.
- **Integration:** restart with same/missing/wrong key; permission and corrupt-row
  failure; scan DB/WAL/SHM bytes for sentinels.
- **Manual/device:** real macOS Keychain initialization/unlock in the final walk.
