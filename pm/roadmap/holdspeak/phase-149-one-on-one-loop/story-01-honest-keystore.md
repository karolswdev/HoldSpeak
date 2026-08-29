# HS-149-01 — The honest keystore + sidecar truth (L3+L2)

- **Project:** holdspeak
- **Phase:** 149
- **Status:** ready
- **Depends on:** —
- **Unblocks:** HS-149-02, HS-149-06
- **Owner:** unassigned

## Problem

Phase 138's ledger items, proven on the owner's screen twice this
arc (audit-tuesday-walk.md): L3 — no dev-only keystore seam, so
populated-People state cannot be walked or tested headlessly (macOS
keychains are UID-scoped; keyring #623 ignores custom keychain
targets; the GUI dialog lands on the OWNER); L2 — a broken/locked
sidecar renders as silent emptiness on projections.

## Scope

### In (settled-design D1)

- `HOLDSPEAK_PEOPLE_KEYSTORE_FILE=<path>`: when set, the People
  store keys from that file (create-on-first-use under the walk
  HOME), bypassing the keychain entirely — and (counsel F4) uses an
  ISOLATED sidecar path derived from the env world, refusing to
  open or create the production sidecar at DEFAULT_PEOPLE_DB_PATH;
  doctor warns if both worlds exist. Ignored when unset; the
  production keychain path byte-untouched; `doctor` reports LOUDLY
  when active.
- L2: the Door's People-card projection and any People read
  surface distinguish sidecar locked/absent/broken from empty —
  one quiet named line, never silence (match PeopleCore's existing
  gate vocabulary).
- Tests: the seam proven headless (set env → setup → populate →
  read back, zero keychain calls — assert via a keyring-call spy);
  doctor line; L2 states.

### Out

- Key recovery/rotation (138 deferred list); any change to the
  production keychain path beyond the bypass check.

## Acceptance criteria

1. With the env set, full People setup + CRUD runs headless in an
   isolated HOME with ZERO keyring/keychain calls (spy-asserted) —
   the first ever.
2. Without the env, behavior is byte-identical to today (keychain
   path untouched, proven by the existing People suites).
3. doctor names the dev keystore loudly when active; L2 states
   render named, never empty.

## Test plan

People store/service focused suites + new seam tests under
isolated HOME; a keyring-spy fixture; doctor test.
