# HS-170-02 - The species sweep (library-level fixes that lift every face at once; the canon guards made mechanical)

- **Project:** holdspeak
- **Phase:** 170
- **Status:** in-progress
- **Depends on:** HS-170-01
- **Unblocks:** HS-170-03, HS-170-04
- **Owner:** unassigned

## Problem

Most violations are species, not faces: raw buttons, stretched tokens, prose helpers, zero counters, portaled footers, type-step collapse.

## Scope

- **In:** for each violation class in the census, the fix at the library or the shared CSS (never per face): Button everywhere a `<button>` was; token species; the footer's empty-slot law; the type steps; empty states as one line; counters of zero removed; egress chips where fetches happen; the guards added to tests/unit (raw button, zero counter, sentence, accent rail, single-step face) so the canon cannot regress; re-shoot the census after the sweep.
- **Out:** redesigning a face's composition (03+).

## Acceptance criteria

- [ ] The violation count per class before/after in the evidence; the guards green on the swept tree.
- [ ] The census re-shot; the orchestrator read every PNG.
- [ ] Web baseline zero branch-new.

## Test plan

The new guards; `scripts/check_web_baseline.py --run`; the census rig alone.

## Delivered

_(pending)_
