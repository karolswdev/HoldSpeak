# HS-72-06 — Split the meetings god-module

- **Status:** done
- **Priority:** MED (the named watch item, now 330 lines past its warning)
- **Depends on:** HS-72-03, HS-72-04
- **Evidence:** [evidence-story-06.md](./evidence-story-06.md)

## Goal

`holdspeak/web/routes/meetings.py` is 1,855 lines — flagged as a watch item
at 1,525 by `docs/ARCHITECTURE_BACKEND_RUNTIME.md` and now past every module
budget that doc set after Phase 63. It mixes meeting CRUD, action items,
artifacts, aftercare, and proposals. HS-72-03/04 already removed the desk
relay and the duplicated lifecycle; this story finishes the job with the same
package pattern `dictation/` and `activity/` already use.

## Scope

- **In:** `meetings.py` → a `meetings/` package (`__init__.py` assembling one
  router from submodules: `crud.py`, `action_items.py`, `artifacts.py`,
  `aftercare.py`, `proposals.py`, `exports.py` — exact cut lines to be chosen
  along the existing section seams), each under the ~650-line budget; route
  table byte-identical (proven by the HS-72-02 manifest); patch targets
  traced (tests patching `holdspeak.web.routes.meetings.<name>` updated to
  the defining submodule).
- **Out:** any handler behavior change; renaming any route; touching the
  other watch-list modules (`db/activity.py` at 1,596 is real but not this
  story — noted as a follow-up candidate).

## Tasks

- [ ] Cut along the section seams; one `build_meetings_router(ctx)` façade
      preserved so `web_server.py` does not change.
- [ ] Regenerate the API manifest; diff must be empty.
- [ ] Grep + update every test patch target; run the meeting-route test
      slice, then the full suite.
- [ ] Update `ARCHITECTURE_BACKEND_RUNTIME.md`'s module table + retire the
      watch-item row.

## Proof required

Empty manifest diff; `wc -l` table for the new submodules (all under budget)
in the evidence; full suite green with no test edited except patch-target
paths; docs updated in the same commit.

## Done

Shipped. `meetings.py` (1,855 at phase open; 1,424 after 03/04) is a
package of seven route modules + a 44-line façade, every file ≤650. The
route table is byte-identical — the regenerated manifest diff contains only
`module` fields (all 33 routes, redistributed exactly). The split surfaced
a REAL latent bug: the intel-process aftercare callback (HS-56-04)
referenced `get_database` with no import in scope and NameError'd on every
real invocation — fixed and regression-locked
(`test_intel_process_aftercare_callback.py`); two dead bindings orphaned by
04's rewrite were removed with grep proof. Proofs: split verification 118
passed, post-fix slice 26 passed, full suite 3063 passed / 37 skipped. See
[evidence-story-06.md](./evidence-story-06.md).
