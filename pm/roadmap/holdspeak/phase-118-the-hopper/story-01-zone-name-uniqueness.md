# HS-118-01 — Zone name uniqueness

- **Project:** holdspeak
- **Phase:** 118
- **Status:** done
- **Depends on:** --
- **Unblocks:** HS-118-04, HS-118-05
- **Owner:** unassigned

## The thesis (the bar)

Today multiple zones can share a name. `POST /api/directories` and
`PUT /api/directories/{id}` perform no uniqueness check — the name
field is just a string. This phase introduces voice-to-drawer
resolution: the user says "research notes" and the system must
resolve exactly one zone. Ambiguity is a system error, not a user
choice.

When this ships, zone names are globally unique addresses.
Uniqueness is enforced by a database index on the normalized name —
not by application-level lookup. Create and rename both fail
atomically on collision. Existing duplicates are disambiguated by a
deterministic, idempotent migration. The web surface shows inline
validation on rename so the user sees the constraint before the
server rejects it.

**Articles served:** II (everything is a DeskPrimitive — names are
addresses in the primitive namespace), VI (honest by construction —
ambiguous resolution is dishonest; DB-enforced, not hoped-for).

## The normalization algorithm

Zone names are normalized before uniqueness comparison:

1. Strip leading and trailing whitespace.
2. Collapse interior whitespace to single spaces.
3. Apply Unicode NFC normalization.
4. Case-fold (Python `str.casefold()`).

**Python is the single authority.** The normalized form is computed
in `DirectoryRepository` and stored in a new `name_normalized`
column. The unique index is on this column. SQL never recomputes
normalization — it compares stored values only (`WHERE
name_normalized = ?`). The TypeScript resolver (HS-118-04) matches
against the stored `name_normalized` value fetched from the API, not
against a JS-side recomputation. This avoids Python/SQL/JS Unicode
divergence. The original `name` column retains the user's casing and
spacing for display.

## Deliverables

1. **Schema change.** Add `name_normalized TEXT NOT NULL` to the
   `directories` table. Add a unique index:
   `CREATE UNIQUE INDEX idx_directory_name_norm
   ON directories(name_normalized) WHERE deleted = 0`.
   (Soft-deleted zones do not occupy the namespace.)

2. **Normalization in the repository.** `DirectoryRepository.upsert`
   computes `name_normalized` from the name before insert/update.
   The DB enforces uniqueness — the application catches the
   `IntegrityError` and translates it to HTTP 409 with body
   `{"error": "zone_name_taken", "existing_name": "..."}`.

3. **Rename self-exclusion.** Renaming zone A to its own current
   name (e.g. changing case: "notes" → "Notes") must succeed. The
   unique index handles this naturally — the normalized value hasn't
   changed, so no collision occurs. Test this explicitly.

4. **Migration for existing duplicates.** A startup migration:
   - Query groups sharing the same `casefold(name)`.
   - Within each group, sort by `created_at ASC`, then `id ASC`
     (deterministic).
   - First zone keeps its name. Others get ` (2)`, ` (3)`, etc.
   - Before appending a suffix, check that the suffixed name doesn't
     collide with an existing zone. If it does, increment the
     counter until a free slot is found.
   - The migration is idempotent: rerunning it on an already-clean
     database is a no-op.
   - Log each rename to stdout: `"Zone renamed: 'Notes' (dir_xxx)
     → 'Notes (2)'"`.

5. **Character constraints.** Zone names must be 1–64 characters
   after normalization. The backend validates and returns 422 on
   violation. The frontend trims before submitting.

6. **Frontend inline validation.** In the zone rename flow
   (EditInPlace on ZoneWindow title): on 409 response, show an
   inline error below the field: `"A zone named [name] already
   exists"` in `--danger-signal` color. The field retains focus.
   No toast — keep the error co-located.

7. **New repository method.** `find_by_normalized_name(name: str)
   -> Optional[DirectoryRecord]` for lookup by name (used by the
   @-reference tokenizer and voice resolver in later stories).

8. **Expose `name_normalized` on the API.** The `GET /api/directories`
   response includes `name_normalized` for each zone. The TypeScript
   `Directory` interface gains `nameNormalized: string`. The
   client-side resolver matches against this field — never
   recomputing normalization in JavaScript.

9. **Migration ordering.** The migration is a single transaction:
   (a) add `name_normalized` column with a default, (b) backfill
   from existing names using Python normalization, (c) disambiguate
   duplicates, (d) create the unique index. If the index creation
   fails (unexpected duplicate), the transaction rolls back.

10. **Suffix overflow.** If appending ` (N)` would exceed the
    64-character limit, truncate the base name to make room. The
    truncation preserves a word boundary where possible. Test:
    a 64-character zone name that needs disambiguation → truncated
    base + suffix ≤ 64 characters.

11. **Logging policy.** Migration renames are logged at `INFO` level
    using the project's structured logger, not `print()`. Log the
    zone ID and the old/new normalized names, not the display names
    (which may contain user content).

## What NOT to do

- Do NOT use application-level check-then-insert. The DB index is
  the single source of truth. The application catches the
  constraint violation.
- Do NOT namespace zone names per parent directory. Names are flat
  and globally unique. Simplicity over hierarchy.
- Do NOT add fuzzy matching or "did you mean?" suggestions.

## Test plan

- `uv run pytest -q tests/ -k directory` — existing tests pass.
- New tests:
  - Create "Research", create "research" → 409 (case-insensitive).
  - Create "Research", rename zone B to "Research" → 409.
  - Rename "research" to "Research" (same zone, case change) →
    succeeds.
  - Create "  Research  " → stored as "Research", normalized as
    "research".
  - Seed three zones named "Notes" → after migration, names are
    "Notes", "Notes (2)", "Notes (3)".
  - Seed zones "Notes", "Notes (2)" → migration of a third "Notes"
    produces "Notes (3)", not a collision with "Notes (2)".
  - Rerun migration on clean DB → no changes (idempotent).
  - Concurrent creates (two threads, same name) → exactly one
    succeeds, one gets 409.
  - Name > 64 chars → 422.
  - Empty name → 422.
  - Suffix overflow: 64-char zone needing disambiguation →
    truncated base + suffix ≤ 64 chars.
  - Migration ordering: column add → backfill → dedup → index,
    all in one transaction.
- Visual at 1440: rename a zone to a taken name → inline error
  below the field, field retains focus.
