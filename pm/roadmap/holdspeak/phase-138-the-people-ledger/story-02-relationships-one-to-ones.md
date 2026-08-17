# HS-138-02 — Relationships and one-to-ones

- **Project:** holdspeak
- **Phase:** 138
- **Status:** ready
- **Depends on:** 138-01
- **Unblocks:** 138-03, 138-04
- **Owner:** delegated Terra worker; primary adjudicates

## Problem

Technical leaders need durable 1:1 continuity, but a free-text note is not a request
or promise and ordinary meeting capture lacks the consent/privacy contract. The first
domain slice must be manual, explicit, and entirely inside the encrypted authority.

## Scope

- **In:** relationships; notes-only 1:1 sessions; shared-intent agenda and
  leader-private prep; requests; lifecycle and supersession invariants; authenticated
  loopback service/routes; redacted errors; archive (not destructive delete).
- **Out:** recording/transcripts, meeting/speaker/calendar linkage, inference,
  participant access, search indexing, sync/export/connectors.

## Acceptance criteria

- [ ] CRUD/list/restart works through PeopleService only; no raw store route.
- [ ] `shared_intent` and `leader_private` govern local policy and never claim remote
  access; all nonlocal/capture/inference/sync/export operations named-refuse.
- [ ] Rolled agenda creates a successor link; accepted text is superseded, never
  silently overwritten; archived relationships disappear from active roster.
- [ ] Unauthorized/guessed IDs and locked store yield content-free errors.

## Test plan

- **Unit:** domain state machine, policy matrix, DTO validation, supersession.
- **Integration:** authenticated People routes with temporary encrypted store;
  restart persistence and locked/corrupt behavior.
- **Manual/device:** create relationship, 1:1, shared agenda/private prep and reopen.
