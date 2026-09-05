# HS-174-03 — Scoped remote identity

- **Project:** holdspeak
- **Phase:** 174
- **Status:** in-progress
- **Depends on:** HS-174-01, HS-174-02
- **Unblocks:** HS-174-04, HS-174-08
- **Owner:** unassigned

## Problem

Today AgentCredentialStore (principals.py:89-172) mints AGENT-kind
principals with TTL and revocation, but every credential has full
access to the tool surface — there is no palette restriction and no way
for the owner to issue a credential scoped to a subset of tools. A
remote machine running overnight must not hold OWNER authority (Article
XI:4: "Only the owner approves, rejects, or delegates") and must be
restricted to the bounded delegation the owner configured.

## Scope

- In:
  - Extend AgentCredentialStore to accept a palette restriction at
    issue time (PROJECT_PALETTE or a configured subset of tool
    families); the credential carries its allowed palette.
  - The kernel derives authority from the credential (Article XI:3) and
    refuses tools outside the palette with a typed capability error
    (MCP-005).
  - OWNER is never a remote principal: the remote transport always
    derives a scoped AGENT principal from the credential, never the
    owner's web token.
  - The owner mints and revokes remote credentials from the desk
    (Settings face from story 01).
  - The credential row shows: identity label, allowed palette, TTL,
    last-used, expiry, revoke verb.
- Out:
  - Per-tool granularity below the family level (palette families are
    the floor; finer scopes deferred).
  - Credential rotation automation (manual mint + revoke is the V0).
  - OAuth or token capture for connectors (gh and acli hold those;
    Article III).

## Acceptance criteria

- [ ] A credential minted with a palette restriction limits the remote
      client to that palette; tools outside it return a typed
      capability error (MCP-005; Article XI:3).
- [ ] OWNER is never derivable from a remote credential: the remote
      transport path always uses AgentCredentialStore, never the
      owner's web token (Article XI:4).
- [ ] The owner can mint and revoke credentials from the desk; the
      credential row shows identity, palette, TTL, last-used, expiry,
      and revoke.
- [ ] A revoked credential is immediately rejected; an expired
      credential is rejected on the next derive call.

## Test plan

- Unit: mint a credential with palette `["project", "desk"]`; call a
  tool outside the palette; assert a typed capability error.
- Unit: attempt to derive OWNER from a remote credential; assert
  refusal.
- Integration: a remote HTTP call with a scoped credential reaches
  the allowed tools and is refused on the others.
- Manual: mint a credential from the desk UI; verify the row; revoke
  it; verify the remote call is refused.

## Notes / open questions

- The palette mechanism (PROJECT_PALETTE, 45 tools, MCP-007) already
  exists. The question is whether the credential carries the palette
  by name (e.g. "project") or by explicit family list. Propose by
  name (the existing mechanism); the owner can override at mint time.
