# HS-91-07 — The Meetings archive in React

- **Project:** holdspeak
- **Phase:** 91
- **Status:** done
- **Depends on:** HS-91-01, HS-91-02
- **Unblocks:** HS-91-09
- **Owner:** unassigned

## Problem

`history.astro` is 3,389 lines plus a 1,777-line controller and carries search,
facets, import, meeting detail, artifacts, aftercare, actions, speakers,
projects, intel, proposals and exports. It is the highest behavioral-risk route
in the migration and needs a dedicated story and proof ledger.

## Scope

- In: React `/history` and `/meetings`; every archive tab, search/facets,
  import, detail/transcript, artifact/proposal review, aftercare, action items,
  speakers, projects, intel/plugin queues, local exports and approved egress
  affordances; decomposed feature components and typed hooks.
- Out: archive schema/API redesign; new artifact kinds; changing actuator
  governance.

## Acceptance criteria

- [x] Every History ledger row passes, with explicit tests for destructive,
      egressing, approval-gated, empty, partial and failed-import paths.
- [x] No monolithic replacement component: tabs/features have bounded modules,
      typed data adapters and focused tests.
- [x] Search/facet state is navigable and recoverable; dialogs trap/restore
      focus; long transcripts/artifact lists remain responsive.
- [x] Egress copy remains explicit and approved; no action sends merely because
      it was rendered or selected.
- [x] Existing archive/import/aftercare/proposal/export integration suites pass;
      old History Astro/controller code is removed.

## Test plan

- Unit: per-feature hooks/reducers and wire adapters.
- Integration: existing History pytest plus browser walks for import, facets,
  meeting detail, proposal review and export.
- Manual / device: owner archive workflow on real data, including one failed
  import recovery and one approval-gated proposal preview.

## Notes / open questions

This story may use several internal commits, but it is one PMO story/PR because
the archive cannot safely expose two competing state owners.
