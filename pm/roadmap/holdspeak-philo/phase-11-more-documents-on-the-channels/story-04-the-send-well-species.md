# PHILO-11-04 - The SEND well as one library species

- **Project:** holdspeak-philo
- **Phase:** 11
- **Status:** backlog
- **Depends on:** PHILO-11-03 ratified (canvas E); PHILO-11-01 merged
- **Unblocks:** PHILO-11-05
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Astra checks
- **Closure finding:** `docs/internal/philo/phase-11/grounding/faces.md` §2 (B1–B8), F3, F4
- **Design:** `design/document-sources.md` section 4 (the wire)
- **Canvas:** E (the shared well), ratified in story 03

## Problem

`web/src/features/channels/SendWell.tsx` is a feature module bound to the update at eight points (faces.md B1–B8): the `update` prop, the `update_id` wire, the `project_update:` filter, the press-store key name, `REV ${update.draftRevision}`, `DeliveryHistory` on the update controller, `ListChips` on `update.deliveries`, and the reload. On four or more faces it is a recurring element; UX-CANON §B says it goes into the library first.

## Scope

- **In:** the well takes a document reference (`{ref, title, label}`) in place of the update; B1–B8 replaced; `PreviewWell`, `ProofCell` and `useDestinations` exported or moved (faces.md §2); the history for a new kind from `channel.sends` by `document_ref` (the ended sends; F4); the update keeps its manual row and Mark delivered as a slot only it fills (R8); the Slack case in `ProofCell` (POSTED, no link); the species in the library and documented in `web/src/desk/surface/contract.md`; the update face recomposed on it with no visible change.
- **Out:** the well on the new faces (05).

## Acceptance criteria

- [ ] One well component in the library, documented in `contract.md`; no face hand-rolls its rows.
- [ ] The update's Phase 10 glass fences and atlas cases pass unchanged at both widths (no visible change).
- [ ] A web-unit case per state for a non-update document: no destination, picked, SENT, POSTED (no link), REFUSED, FAILED, UNKNOWN, PREPARED; no manual row on a non-update.
- [ ] The web baseline has zero branch-new failures.

## Effort (not a promise)

PROVISIONAL: about 1 engineering day.

## Test plan

- **Web unit:** the species' states for the update and one new kind.
- **Glass:** the Phase 10 update fences at 1440 and 393.

## Notes

- 2026-09-29 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
