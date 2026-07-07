# HS-85-02 — The mesh profile kind + the relay provider

- **Project:** holdspeak
- **Phase:** 85
- **Status:** done
- **Depends on:** HS-85-01
- **Unblocks:** HS-85-04, HS-85-05
- **Owner:** unassigned

## Problem

A node's provider becomes pickable the same way everything became pickable
in Phase 84: as a profile. The shape needs one new kind (`meshNode`) and one
new field (`node`), mirrored three ways; and the resolver needs the branch
that turns that profile into a provider which enqueues on the HS-85-01
queue, waits bounded, and returns the node's answer — or refuses by name.

## Scope

- In: the contract change, moved together and pinned: `node: string` on
  `profile.schema.json` (+ kind enum grows `meshNode`), `ProfileRecord` /
  repository / the sync field set (`web/routes/sync.py` profiles row), and
  the Swift `Contracts` mirror — the primitive-contract test updated in the
  same commit. (The ONLY Swift file this phase touches.)
- In: `MeshRelayIntel` in `holdspeak/intel/`: implements
  `run_prompt(system_prompt=, user_prompt=, temperature=, max_tokens=) ->
  str`; refuses IMMEDIATELY (`MeetingIntelError` naming the node and its
  last-seen age) when the node is not live; otherwise enqueues with the
  pinned deadline (120s) and polls coarsely (0.5s) to completion; a failed
  or expired job surfaces the job's named error.
- In: `_apply_runtime_profile` adoption branch — a `meshNode` profile with
  a live-checkable node resolves to the relay shape; every existing
  fallback behavior (dangling, unknown kind) is untouched, byte-identically.
- In: egress — `endpoint_egress` grows the mesh case
  (`{scope: "mesh", host: <node>}`); `_run_egress` reports it for relayed
  runs; the web badge renderer(s) learn the scope ("Mesh · <node>").
- Out: the worker (HS-85-03), pickers/doctor visibility (HS-85-04), Apple
  provider modes, streaming, `analyze()` relay (only `run_prompt` rides).

## Acceptance criteria

- [ ] Contract mirrored three ways; the primitive-contract test pins the
  new field/kind across schema, Python, and Swift.
- [ ] `MeshRelayIntel.run_prompt` round-trips against a stubbed queue: the
  job payload carries the prompts verbatim; the completed result returns
  verbatim (tests, no real node).
- [ ] Non-live node ⇒ immediate `MeetingIntelError` naming node +
  last-seen; expired job ⇒ error naming the deadline (tests, injected
  clock).
- [ ] `_apply_runtime_profile` matrix grows the meshNode rows; every
  existing resolution case passes unmodified.
- [ ] `endpoint_egress(mesh)` shape test-pinned; existing badge consumers'
  wire shapes unchanged (route tests pass verbatim).

## Test plan

- Unit: extend `test_intel_profile_resolution.py` (matrix) + a new
  `test_mesh_relay_provider.py`; `uv run pytest -q tests/unit -k
  "relay or profile_resolution"`.
- Integration: `uv run pytest -q --ignore=tests/e2e/test_metal.py`;
  `tests/unit/test_primitive_contract.py` explicitly.
- Manual / device: n/a — HS-85-05.

## Notes / open questions

- The bounded wait runs where the engine already runs (the routes call
  providers off the event loop through the existing seam); confirm no
  non-mesh route latency regression (a risk-table stop signal).
- meeting intel / dictation assignment to a meshNode profile works through
  the Phase-84 knobs for free once this branch exists — worth one matrix
  row each, not new plumbing.
- **Scope decision (recorded, then REVERSED by the owner in-story):** the
  first cut had dictation refuse meshNode ("the DIR runtime speaks
  grammar-constrained calls"). The owner overruled — *"DIR could also be
  routed"* — and the code agrees: DIR's `openai_compatible` leg is ALREADY
  advisory-constrained (ask for JSON, parse, validate, retry), so the relay
  rides the identical posture. Shipped: `MeshRelayRuntime`
  (`runtime_mesh_relay.py`) REUSES the endpoint backend's message/validation
  helpers with the transport swapped to the relay queue; assembly builds it
  (wrapped in the same counting/cold-start delegate) on adoption; the setup
  probe reports node liveness; doctor names the node. Latency is governed by
  the pipeline's existing honesty (the per-utterance budget + the DIR-R-003
  cold-start cap) — a far edge degrades exactly like a slow endpoint.
- **Schema note:** `profiles.node` needed a column, so the phase carries
  TWO bumps (v10 queue, v11 profiles.node), each with its DDL.
- **Swift decode was load-bearing:** the `Kind` enum decode throws on
  unknown cases — without `case meshNode`, a synced meshNode profile would
  have broken iPad sync. Caught in the pre-edit read, mirrored in the same
  commit.
- Three pre-existing test stubs of `build_meeting_intel_for_profile` grew
  the `node=""` kwarg (signature growth, not behavior change).
