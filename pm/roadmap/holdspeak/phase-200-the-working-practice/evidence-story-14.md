# Evidence - HS-200-14

- **Story:** HS-200-14 - Make permitted People preparation useful
- **Status:** done
- **Date:** 2026-09-17

## Proof

### Captured run — 2026-09-18T04:47:24Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.INypKw9Zzy uv run pytest -q -p no:cacheprovider tests/unit/test_phase200_people_preparation.py tests/unit/test_hs172_room_people.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** da102cd00ce723d62a45152348665af9ddebd57b

```text
.............................                                            [100%]
29 passed in 4.96s
```

### Captured run — 2026-09-18T04:47:30Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.sUwesxLyc1 PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q -p no:cacheprovider tests/e2e/test_hs200_people_preparation_glass.py tests/e2e/test_hs172_room_people_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** da102cd00ce723d62a45152348665af9ddebd57b

```text
......                                                                   [100%]
6 passed in 31.84s
```

## What was built

A `PEOPLE` posture in the Project Room: per person on the Project (record owners from HS-200-12's commitments, Watch identities, Project links), their open commitments with the transcript span and `Open source`, and observable work facts per linked source with its label; nothing inferred (no score, rank, sentiment, authority — a fence walks every key). An owner string that matches two People reads `OWNER · AMBIGUOUS · 2 MATCHES` with `Resolve` unfolding the candidates in place; a single near match is offered, never applied; a shared display name in the Watch resolver now returns ambiguous instead of the first store-order match (a pre-existing attribution defect). `People` on the section head opens PeopleCore scoped to the Project (`N ON THIS PROJECT · N MORE · Everyone`) and focus returns to the verb. Missing or locked context is a typed partial: `PEOPLE 0 OF 2 · LOCKED · Unlock`, `NOT SET UP · Set up People`, `UNAVAILABLE`, `NOT LINKED · Link`; a paused or retired Watch contributes no count and reads `PAUSED · OMITTED`. Reserved owner strings (`me`, `you`, `remote`) never make a row.

## The boundary, adversarially (counsel)

Every door held: an AGENT credential gets 403 on the people route, the alias route and the room; MCP `project.get_room` carries no people, unresolved or candidate keys; the scoped roster is a client-side filter over the owner-gated list; alias links go through Phase 138's route with its refusals intact; raw owner strings never ride a `/ws` frame; a corrupted key store reads `UNAVAILABLE` and is never wiped. The protected-field fence asserts six sentinels and a key allow-list across the projection, the route, `room()`, the meeting export and the raw database bytes.

## Counsel-on-built: RATIFY-WITH-CONDITIONS, all paid

P0: `_read_room_commitments` filtered `status != 'completed'` while the completion verb writes `closed`, so a commitment marked Done stayed an open commitment in PEOPLE forever (`after Done: people rows -> [('Priya Sharma', ['Confirm the freeze window'])]`); the filter is `status = 'open'` now and a fence completes through the real verb and reopens. P2 paid: reserved `me` drawn as a person; `OWNER · LOCKED` under a `NOT SET UP` head (the row now carries the ledger's own state); the guide's `Link` sentence and the `UNAVAILABLE` state; the phase-172 glass rig wrote tracked shots on every run (gated; the three PNGs restored byte-identical); the charter's "revoked source" and "derived summary" cases fenced. Reported to BACKLOG: diacritics in owner matching (`Príya`); an alias equal to another person's display name wins outright.
