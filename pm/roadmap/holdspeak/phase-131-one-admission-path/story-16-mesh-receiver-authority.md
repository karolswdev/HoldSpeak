# HS-131-16 — The mesh receiver proves authority locally

- **Project:** holdspeak
- **Phase:** 131
- **Status:** done
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
- Implement inside the hunk-level boundary in
  [ACCEPTANCE-MAP-HS-131-16](./ACCEPTANCE-MAP-HS-131-16.md): only protocol CORE,
  focused PROOF, and a before/after-demonstrated REGRESSION ride in this story.
  Any path expansion is classified there before it is edited.

### Out

- General-purpose federation, account identity, or cloud control plane.
- Trusting LAN reachability, source IP, or a nonempty signature field.
- Reusing a hub-issued in-memory claim witness across processes.
- An allowlist exception for `commands/mesh_serve.py`.
- Product-wide profile/Models UI CAS, Setup/Doctor/readiness unification, browser
  audio/floor generations, meeting planning, observer projections, generic
  database retirement/finalization, documentation, or final-walk work.
- Scheduler-hostile process probes without an ordinary shipped mesh trigger;
  record them as adversarial notes rather than widening the release bar.

## Acceptance criteria

- [x] A Sol-ruled design names the cross-node trust root and exact local
  admission/claim/receipt protocol before implementation.
- [x] Forged, missing, expired, replayed, wrong-node, wrong-destination,
  wrong-revision, wrong-operation, or revoked envelopes refuse by name before
  engine construction or model dispatch.
- [x] Every worker physical model attempt is causally linked to the offered hub
  operation, names its exact local principal and frozen revision, and ends in
  one immutable terminal receipt.
- [x] Hub result acceptance independently revalidates the returned operation,
  worker, revision, authority binding, and terminal outcome.
- [x] Cancellation and replay races cannot produce accepted late output or
  mutate either node's terminal receipt.
- [x] The one-path census removes `mesh-receiver` with zero command-scope
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

On 2026-08-14 the first isolated implementation was frozen and rejected as a
ship candidate at 151 changed paths. It remains a forensic reference only. The
story reset to the clean `e4193f12` base under the binding acceptance map above;
no partial review verdict, test claim, or hunk from that candidate transfers by
implication.

The first reduced candidate froze at 31 paths / 268,140 bytes. Hostile Sol review
returned FAIL and Terra's execution was blocked by worktree isolation while its
static review also found blockers. Their sustained ordinary-use findings are
consolidated once in
[REPAIR-HS-131-16-R1](./REPAIR-HS-131-16-R1.md); no partial finding is patched
outside that brief. R1 then froze at 33 paths / 380,139 bytes and passed the
attached 30-file gate (574 passed, one environmental skip), but the second
hostile review still returned FAIL. Its ordinary-use findings and two narrow
wire/HTTP clarifications are consolidated in
[REPAIR-HS-131-16-R2](./REPAIR-HS-131-16-R2.md). R2 implemented at 36 paths and
its attached union exposed one concrete stale test double: the fake mesh node was
never paired after name-only liveness was correctly deleted. The owner then
closed the academic review loop. No R3 hostile brief was opened.

The final 40-path candidate fixes that functional red through the real pairing
seam and freezes at manifest
`24e25287380abcbad6527d5037f051afccbf155620059b38f11069f8085b1413` / complete
diff `17cb83aaf53082bfccf1e963b942c7304e43fad8f76aca2038fea4e018b14450`.
The final 46-file functional matrix passes 864 tests, including the real
separate-process loopback and zero-finding census. The full unit candidate lane
passes 4,643 tests; the only omitted guard files reproduce three pre-existing
failures whose inspected inputs are byte-identical to `e4193f12`. Web tokens,
architecture, typecheck, and build pass; 785 tests outside two unchanged stale
Speak mock files pass. The orchestrator classifies those inherited reds as
adjacent baseline, not HS-131-16 regressions, and rules **SHIP** at the owner's
ordinary-product bar.

The recommended default for the design beat is node-side admission because it
keeps the worker's physical act locally receipted. Cryptographic envelope
verification remains acceptable only if it still yields a locally authenticated
claim and immutable terminal receipt rather than importing ambient authority.
