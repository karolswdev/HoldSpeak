# HS-131-16 — The mesh receiver proves authority locally

- **Project:** holdspeak
- **Phase:** 131
- **Status:** backlog
- **Depends on:** HS-131-01, HS-131-02, HS-131-07
- **Unblocks:** HS-131-10
- **Owner:** unassigned

## Problem

`mesh_serve` receives a hand-built job envelope, constructs an engine, and runs a
prompt. Nonempty warrant-shaped fields prove neither sender authenticity nor a
locally admitted child. The hub-side envelope checks from HS-131-07 protect
result acceptance, but they do not satisfy Constitution Article XI.2 for the
worker's physical model act or XI.3's kernel-derived principal and authority.

## Scope

### In

- Begin with a Sol-ruled design beat comparing two acceptable shapes:
  cryptographic verification of an admitted cross-node envelope before local
  claim, or a node-side `InferenceRunner` that admits and receipts the physical
  work locally under an authenticated node/service principal.
- Specify the trust root, replay protection, destination binding, immutable
  deployment revision, parent/causal linkage, expiry/revocation, attempt
  ordinal, cancellation, and terminal-receipt ownership. Nonempty strings,
  caller-built `DispatchContext`, and process topology are not authority.
- Ensure the worker constructs an engine only after local verification/admission
  and an exact claim witness. The physical enqueue and worker model attempt must
  each retain their correct, separately typed receipt semantics.
- Preserve the hub's independent validation of operation target, envelope
  revision, warrant binding, worker identity, and returned result. Worker
  success cannot force hub acceptance.
- Make retries and compatibility follow-ups separately admitted physical
  attempts with distinct immutable receipts; prevent replayed or cancelled jobs
  from publishing late results.
- Remove the two `mesh-receiver` finding sites only when the census can trace
  construction and `run_prompt` through the chosen authenticated local spine.

### Out

- General-purpose federation, account identity, or cloud control plane.
- Trusting LAN reachability, source IP, or a nonempty signature field.
- Reusing a hub-issued in-memory claim witness across processes.
- An allowlist exception for `commands/mesh_serve.py`.

## Acceptance criteria

- [ ] A Sol-ruled design names the cross-node trust root and exact local
  admission/claim/receipt protocol before implementation.
- [ ] Forged, missing, expired, replayed, wrong-node, wrong-destination,
  wrong-revision, wrong-operation, or revoked envelopes refuse by name before
  engine construction or model dispatch.
- [ ] Every worker physical model attempt is causally linked to the offered hub
  operation, names its exact local principal and frozen revision, and ends in
  one immutable terminal receipt.
- [ ] Hub result acceptance independently revalidates the returned operation,
  worker, revision, authority binding, and terminal outcome.
- [ ] Cancellation and replay races cannot produce accepted late output or
  mutate either node's terminal receipt.
- [ ] The one-path census removes `mesh-receiver` with zero command-scope
  allowlist entries and zero unregistered execution.

## Test plan

- Design: adversarial protocol review over trust bootstrap, replay, clock skew,
  restart, cancellation, compromise boundary, and receipt ownership.
- Unit: deterministic forged/tampered/replayed/swapped/expired envelope matrix;
  exact context binding; child/receipt/physical cardinality; late result fence;
  one-path census.
- Integration: real hub and worker processes on loopback, then LAN where
  available, proving both local terminal receipt and independent hub acceptance
  or refusal.
- Mutation: bypass verification with a direct `run_prompt` callable and prove
  the exact named census failure before restoring green.
- Manual / device: HS-131-12 repeats the chosen protocol against the real mesh
  node and model.

## Notes / open questions

The recommended default for the design beat is node-side admission because it
keeps the worker's physical act locally receipted. Cryptographic envelope
verification remains acceptable only if it still yields a locally authenticated
claim and immutable terminal receipt rather than importing ambient authority.
