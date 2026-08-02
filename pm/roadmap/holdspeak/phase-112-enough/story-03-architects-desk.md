# HS-112-03 - The architect's desk

- **Project:** holdspeak
- **Phase:** 112
- **Status:** backlog
- **Depends on:** —
- **Unblocks:** HS-112-04, HS-112-05
- **Owner:** unassigned

## The thesis (the bar)

The owner: "I want an environment seed that starts fresh and
beautiful — a desk with drawers like ADRs, Meetings, Rules... what a
Senior Software Architect would want on his desktop. What you have
today is an artifact of end-to-end testing and it makes me really,
really confused." The bar: **a fresh HOME boots into a curated
architect's desk — named drawers, one honest starter object each,
nothing else — and any cluttered desk can RESET to that seed with
one confirmed, undoable-by-honesty verb.**

The seed roster (owner's examples plus the architect's staples;
final names judged on the real desk):

- **ADRs** — with one starter note: an ADR template.
- **Meetings** — where the tape catalog files its records.
- **Rules** — with one starter note: the desk's own working rules.
- **Decisions** — the Phase-109 decision records' drawer.
- **Reference** — KBs and reading.
- **Inbox** — the unfiled landing zone, so the floor stays clean.

## Ground (from the pre-charter survey)

- There is no product-side seed: a fresh install renders `EmptyDesk`
  (`web/src/desk/DeskApp.tsx:46-54`); no migration inserts any desk
  primitive (`holdspeak/db/core.py`).
- The desk UI has **no delete verb at all** — the only desk-store
  DELETE is an unfile (`web/src/desk/store.ts:735`). A desk is
  append-only from the UI; the owner's clutter is accumulated dev
  residue in `~/.local/share/holdspeak/holdspeak.db`.
- The seed format and idempotent applier exist, quarantined in the
  UAT rig (`uat/conductor/induction/seeds.py:125`, manifests in
  `uat/seeds/`; deterministic ids are the idempotency contract,
  `seeds.py:131`).
- A drawer is a `Directory` (`holdspeak/db/primitives.py:841`;
  sprite rule `web/src/desk/sprites.ts:39`); filing via
  `PUT /api/directories/{dir}/members/{id}`
  (`holdspeak/web/routes/primitives/directories.py:118`).
- Reset must TOMBSTONE, not purge: sync ships
  `include_deleted=True` for last-write-wins
  (`holdspeak/web/routes/sync.py:526`) — a hard purge would be
  resurrected by a paired device.
- Layout lives in localStorage keys (`hs.diorama.pos`,
  `hs.desk.panels`, `hs.desk.zonew`, `hs.desk.zone-views`,
  `hs.desk.zone-windows`, `hs.desk.open-windows`) —
  `resetLayout()` (`web/src/desk/store.ts:1033`) covers only part.

## Method

1. **The manifest ships in the product.** A packaged
   `fresh-desk` seed in the existing YAML schema, deterministic
   `hs-desk-*` ids, drawers in dependency order, starter notes with
   real authored content (the ADR template and the Rules note are
   written, not lorem).
2. **A repo-level seeder.** `holdspeak/db/seed.py` applying through
   the repositories (the routes are thin wrappers over the same
   calls); idempotent by id. A CLI verb (`holdspeak seed`, beside
   `doctor`/`backup`) and a route so the desk can reach it. No
   auto-seed on boot — the UAT `fresh-desk.yaml` recipe's
   empty-desk assertions stay true.
3. **Reset-to-seed.** Tombstone sweep across desk primitives →
   re-apply the seed → sweep the layout keys. The verb lands in the
   registry (beside `desk.reset-layout`) and in Prefs; it is the
   desk's first destructive act, so it confirms in-world (no modal)
   and states exactly what it keeps: meetings archive, journal, and
   settings survive; desk objects reset.
4. **Beautiful means judged.** The seeded desk is composed on the
   real floor — drawer order, default positions, the first-boot
   impression — per the high-UI-standards rule, both viewports.

## Test plan

- Apply twice → identical desk (no duplicates; id contract pinned).
- Fresh isolated HOME boots into the architect's desk: six drawers,
  starter objects openable, floor otherwise clean.
- Reset from a dense desk (the `dense-desk` UAT seed as the
  before-state): clutter tombstoned, seed present, ghost layout gone.
- Tombstone semantics: after reset, a sync pull reports the removed
  primitives as deleted, never resurrects them (pinned by test).
- UAT `fresh-desk` recipe still passes untouched.
- Screenshot walk at 1440+393: first boot, a drawer opened, the ADR
  template read, the reset confirm and after-state.
