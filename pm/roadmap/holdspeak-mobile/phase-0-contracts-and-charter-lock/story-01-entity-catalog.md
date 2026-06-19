# HSM-0-01 — The entity catalog

- **Project:** holdspeak-mobile
- **Phase:** 0
- **Status:** done
- **Depends on:** none
- **Unblocks:** HSM-0-02
- **Owner:** unassigned

## Problem

The mobile runtime must interoperate with the desktop product, but the domain
model lives implicitly in Python code and route payloads — there is no single
catalogue of "every entity HoldSpeak emits and what fields it has." Without it,
the JSON Schemas (HSM-0-02) would be guesses.

## Scope

- **In:** `holdspeak-mobile/contracts/ENTITY-CATALOG.md` (or equivalent in the
  package home decided in HSM-0-03) listing every domain entity the desktop
  emits — at minimum the charter's ten (`Meeting`, `Transcript`, `Speaker`,
  `Segment`, `ActionItem`, `Decision`, `Risk`, `Requirement`, `Artifact`,
  `IntelJob`) plus any sibling the extraction surfaces (e.g. aftercare digest,
  actuator proposal/decision, dictation journal entry). Each entity: its fields,
  types, optionality, enum vocab, relationships, and a desktop source trace
  (file:line or a captured payload).
- **Out:** the schema files themselves (HSM-0-02). Any new field not already
  emitted by desktop (record as a proposed addition, do not bake in).

## Acceptance criteria

- [ ] Every charter Layer-1 entity appears with a complete field list.
- [ ] Every field cites a desktop source (a `holdspeak/...` path + symbol, or a
      captured JSON payload from a route/CLI).
- [ ] Enum-valued fields (statuses, MIR profile, egress scope, artifact type)
      list their full vocabulary as the desktop actually uses it.
- [ ] Entity relationships (Meeting → Segments → Speakers; Artifact → IntelJob;
      ActionItem → Decision provenance) are drawn.
- [ ] Entities found beyond the charter's ten are listed under "Beyond the
      charter" with a keep/park recommendation.

## Test plan

- Manual: cross-check the catalog against a real desktop meeting payload (export
  one meeting via the desktop API/CLI; confirm every field in the payload has a
  catalog entry and vice-versa).
- Unit: n/a (documentation deliverable; validated by HSM-0-02's schema run).

## Notes / open questions

- The charter lists ten entities as the contract surface; the desktop almost
  certainly emits more (aftercare, actuator records). Treat ten as the floor.
- Resolve naming/casing impedance in HSM-0-03, not here — here, record the
  desktop's actual field names verbatim.
