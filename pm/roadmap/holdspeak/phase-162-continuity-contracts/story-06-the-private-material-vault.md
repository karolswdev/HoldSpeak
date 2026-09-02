# HS-162-06 — The private-material vault: custody and key saga

- **Project:** holdspeak
- **Phase:** 160
- **Status:** backlog
- **Depends on:** HS-162-01, HS-162-02, HS-162-03
- **Unblocks:** HS-162-05, HS-162-07, HS-162-08, HS-162-09
- **Owner:** unassigned

## Problem

Continuity needs source content to derive memory, yet duplicating private prose,
queries, prompts, or vectors into public SQLite rows, logs, receipts, and
backups would violate HoldSpeak's local/private contract. CF-0 needs a small,
crash-safe vault primitive before migration, planning, or deletion can rely on
encrypted private material.

## Scope

- **In:** native-key-backed envelope encryption; key-intent saga; key and
  ciphertext lineage; authenticated metadata; encrypted payload primitives;
  typed store/resolve/destroy interfaces; redaction/telemetry boundary;
  derivative-purger registration protocol; backup/key-loss law and fault probes.
- **Out:** inventing cryptography, plaintext fallback, cloud key escrow,
  legacy inference-table cutover (HS-162-07), Remove/Forget orchestration
  (HS-162-08), arbitrary filesystem secure-erasure claims, and derivation.

## Acceptance criteria

- [ ] Private source/value/query/prompt/vector material is encrypted with an
  approved library, unique nonces, authenticated metadata, versioned cipher
  suite, and native key references; secrets never enter public manifests.
- [ ] Locked, missing, deleted, or mismatched keys produce typed unavailable or
  removed outcomes; no path falls back to plaintext.
- [ ] Key intent and envelope admission recover deterministically across
  `reserved`, native `key_created`, envelope commit, `active`, `destroying`,
  native delete, and `destroyed`; recovery never exposes a usable orphan key or
  an envelope whose key lineage was not committed.
- [ ] Store/resolve/destroy is idempotent, binds authenticated owner/operation/
  material metadata, and returns private bytes only to an admitted in-process
  consumer; public manifests expose identifier, state, and digest only.
- [ ] A closed derivative-purger registry defines resumable, idempotent lineage
  purge progress without claiming that any derivative schema exists yet.
- [ ] Canary scans cover the vault DB/WAL/temp boundary, library errors, receipts,
  logs, crash reports, and backup manifests; backup without its native key is
  unusable and disclosed, never silently decrypted or rewritten plaintext.

## Test plan

- **Crypto:** known-answer/library interop, AAD tamper, nonce uniqueness,
  locked/missing/deleted key, corrupt envelope, backup without native key.
- **Saga:** crash/recovery before and after reserved, key creation, envelope
  commit, activation, destroying, native deletion, and destroyed; duplicate
  create/destroy and an unavailable native key store.
- **Interfaces:** authorization/AAD mismatch, purger registration/refusal, typed
  resolution outcomes, concurrent store/destroy.
- **Leakage:** unique sentinel values scanned across every vault artifact class.

## Notes / open questions

- CF-0 INV-008/009 and §§12/15 are normative; HS-162-07/08 complete this
  work package as separately mergeable, disabled-by-default PRs.
- This story may define key-provider interfaces for platforms not yet shipped;
  a fake provider cannot satisfy native key-store release proof.
