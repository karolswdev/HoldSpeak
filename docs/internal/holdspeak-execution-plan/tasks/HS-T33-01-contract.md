# HS-T33-01 · Set the People Add recovery contract

**Conditional characterization task; implementation not assigned.** Parent: [HS-S33](../stories/HS-S33-people-add-recovery.md), [HS-E30](../epics/HS-E30-recovery-outcomes.md). Requires assigned [HS-T00](HS-T00-baseline.md). Source pin `80b641fa41c7352280cfa52e933acf6dbe8d3857`.

## Mandatory context

[Agent safety](../AGENT_START.md#authority-and-checkout-safety); story [choices](../stories/HS-S33-people-add-recovery.md#g33-choices-and-limits), [design](../stories/HS-S33-people-add-recovery.md#narrow-implementation-design) and [matrix](../stories/HS-S33-people-add-recovery.md#acceptance-matrix); [V33](../VALIDATION.md#v33-people-add-recovery-verification); [I04/I16/I17/I18/I21/I23/I25](../INVARIANTS.md). Do not require the whole research library.

## Work

1. Recheck the exact V33 source and caller map. Trace create persistence/readback, atomic same-ID acceptance, public projection, owner route gate, current unkeyed person hosts, draft storage and malformed-success parsing. Record source facts separately from actual baseline results.
2. Resolve G33-A versus B, same-mount limits, explicit Check/Accept/new-promise controls, private in-memory receipt custody, conservative draft clearing, bounded host reset and uncertain-readiness protective fallback. Generic 503 cannot distinguish key loss from outage without the existing readiness read. A request for durable/crash/cross-window exactly-once behavior invalidates A; revise the contract instead of adding localStorage.
3. Enumerate precise known pre-write refusals and unknown outcomes. A later accept refusal never erases an acknowledged request. Missing/partial relationship read cannot prove no effect; public accepted linkage comes from exact commitment request_id, not an internal field or matching words.
4. Confirm one production owner and V33 test/capture budget. Independently inspect temporary encrypted store setup, fake key custody, authenticated full edge and browser interception. Both TestClient auth headers must be removed for unauthorized cases. No owner HOME/Keychain/provider work is permitted by a test name.
5. Under execution assignment only, collect and establish the named focused baseline. Plan the expected-red composed cases: actual changing create IDs, accepted-but-response-lost, older host read, same-text edit roundtrip, protected failure and malformed success. Existing generic draft tests and stable fake create response are preservation evidence, not the missing recovery proof.

## Exit and stops

Return accepted/pending G33 details, current path/identity/error contract, exact baseline or explicit unrun status, permitted fixtures and edit ownership. Do not begin implementation merely because the plan is detailed. Stop for a different target guarantee, unsafe keys/background work, ambiguous protected-data behavior or necessary scope expansion. No data rollback or deletion is part of characterization.
