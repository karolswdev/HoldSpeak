# HS-109-01 - The decision record — first-class, with lifecycle

- **Project:** holdspeak
- **Phase:** 109
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-109-02, HS-109-03, HS-109-04, HS-109-05
- **Owner:** unassigned

## The thesis (the bar)

Today a decision is an anonymous item inside
`artifacts.structured_json["decisions"]` — the aftercare reader
(`holdspeak/meeting_aftercare.py:79-95`) proves it by parsing that
blob and deduplicating by normalized text, because there is nothing
else to key on. No stable ID, no date of its own, no lifecycle, no
supersession, no project key, no direct query.

The bar: **a decision becomes a durable record with identity — and
the existing pipeline does not learn a single new trick.** Records
are DERIVED from the `decisions` artifacts the plugins already
produce, backfilled idempotently over the real archive, and
reconciled on every future synthesis. The plugin chain, the
synthesis mappings, and aftercare's reader keep working byte-for-byte
unchanged. A rival store the plugins must feed is the failure mode.

## Problem

"What did we decide about X, and does it still stand?" is
unanswerable by the system. The blob has no identity to attach an
answer to: an ADR cannot cite the decision it formalized, a later
decision cannot supersede an earlier one, a project cannot list its
decisions, and search cannot return one.

## Recipe

1. **The record.** A `decisions` table (additive migration in
   `db/core.py`): stable ID derived from meeting + artifact + payload
   hash (the same discipline as `synthesis.py:600-681`'s stable
   artifact IDs), decision text, rationale, decided_at (the meeting's
   date until 02 lands the transcript moment), source artifact and
   meeting keys, optional project key, lifecycle
   (`recorded | accepted | superseded | rejected`), and
   `superseded_by` (nullable self-reference). Tombstones + sync clock
   per house schema rules.
2. **The projection.** A one-way deriver: given a persisted
   `decisions` artifact, upsert decision records. Idempotent on the
   derived ID — re-running a meeting's plugins updates in place,
   never duplicates (mirror the Phase-80 idempotency seam).
3. **The backfill.** One pass over every existing `decisions`
   artifact in the archive at migration time; rerunnable; proven on
   the real database, counts printed.
4. **The reconciliation hook.** The artifact persistence seam
   (`synthesis.py:700-748`) triggers the projection after it writes —
   one call site, no plugin edits.
5. **Deletion semantics, settled in writing.** Meetings hard-delete
   and meeting-born artifacts CASCADE (`db/core.py:416-423`). Decide
   and pin: decision records from a deleted meeting keep the record
   with a severed-source marker (memory survives; provenance says
   "source deleted"), never a silent cascade of the memory itself.
6. **The read surface.** Repository + routes: list by project, by
   meeting, by lifecycle; get one with its lineage. Reads owe
   principal + read authority (Article XI clause 5), never admission.
7. **Lifecycle writes are the owner's gesture.** Accept / reject /
   supersede are direct-gesture writes with receipts through the
   existing route discipline — no new consent surface, no modal.

## Out of scope

- Transcript-moment provenance (HS-109-02).
- Promotion to ADR/artifacts (HS-109-03).
- Any FTS/index work (HS-109-04).
- Any web UI (HS-109-05 renders these records).
- Plugin or synthesis behavior changes of any kind.

## Acceptance

- A decision from a real archived meeting has a stable ID, lifecycle,
  and source links; re-running that meeting's plugin chain changes
  nothing (idempotency proven on the real archive, before/after
  counts printed).
- The backfill is rerunnable: second run is a no-op, proven.
- Superseding links both ways: old record carries `superseded_by`,
  and the supersession is queryable from either end.
- Deleting a meeting leaves its decision records with a named
  severed-source state — proven, not asserted.
- Lifecycle writes refuse an unauthenticated principal by name;
  reads require read authority.
- Schema migration is additive only; the schema snapshot regenerates
  clean.
- Full suite green (`uv run pytest -q --ignore=tests/e2e/test_metal.py`);
  kernel spine byte-unchanged.

## Test plan

- **Unit:** ID derivation stability; projection idempotency;
  lifecycle transitions incl. illegal ones refused by name;
  severed-source on cascade.
- **Integration:** backfill over a seeded multi-meeting archive;
  reconciliation fires on artifact persistence; routes with
  principal enforcement.
- **Live (evidence):** backfill against the real archive with counts;
  a real re-synthesis proving no duplicates.

## Chef's notes

- The dedup-by-normalized-text heuristic in aftercare is the enemy of
  identity — do NOT import it. Identity comes from the artifact's
  stable derivation, and two meetings deciding the same words are two
  records (supersession is how they relate, not dedup).
- `decided_at` honesty: until 02, it is the meeting's date and must
  be labeled as such in the record (a `date_basis` field beats a lie).
- Watch the sync wire: additive schema only; this record syncs like
  any primitive or explicitly does not sync yet — decide in writing,
  don't leave it ambiguous.
