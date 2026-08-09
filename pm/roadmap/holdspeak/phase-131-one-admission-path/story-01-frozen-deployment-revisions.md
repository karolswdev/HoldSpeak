# HS-131-01 — Frozen deployment revisions and one sync registry

- **Project:** holdspeak
- **Phase:** 131
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-131-02, HS-131-03, HS-131-04
- **Owner:** unassigned

## Problem

Phase 130 made readiness, execution, and receipt projection describe one
`DeploymentIdentity`, but execution admission still names mutable target state.
A profile can change after admission, and four hand-maintained sync authorities
currently disagree about kinds, buckets, serializers, and mergers. A revision
that cannot survive sync would be another receipt that tells only half the
truth.

## Scope

### In

- Capture an immutable, content-addressed deployment revision from the resolved
  Phase-130 identity before dispatch. The revision includes the destination,
  engine/model spec, endpoint or node identity, egress boundary, and derived
  secret-slot identifier, but never secret material.
- Make engine construction consume that captured revision without fetching the
  mutable profile row again.
- Introduce one Python sync registry that derives `SYNC_KINDS`, bucket-to-kind
  mapping, merge availability, pull serialization, schema/envelope coverage,
  and qualified-kind validation. Replace the parallel authorities in
  `holdspeak/services/sync_service.py:15-81,552-688`.
- Give deployment revisions a sync-visible, resolvable representation through
  that registry. Preserve historical meaning after the editable target moves.
- Repair the six registry/contract failures assigned by HS-130-10. The seventh,
  the synced Workflow execution proof, closes in HS-131-04 after Workflow joins
  admission.
- Replace the Python test that reads a Swift enum with an assertion against the
  authoritative Python/web sync contract. Do not edit Swift source.

### Out

- Moving a product model caller onto kernel admission. HS-131-02 onward owns
  that work.
- Sync protocol redesign, vector clocks, or broad conflict-resolution changes.
- Credential replication. Secret values remain device-local.
- Any Swift implementation or compatibility-driven weakening of the new
  Python/web contract.

## Acceptance criteria

- [ ] Admission can name a stable deployment revision ID and later resolve the
  exact immutable spec from that ID.
- [ ] Changing or deleting the mutable target after capture cannot change the
  endpoint, model, node, egress boundary, or secret slot used by the captured
  revision.
- [ ] Engine construction has no mutable profile re-read after revision capture.
- [ ] One registry derives sync kinds, accepted buckets, serializers, merger
  availability, schema/envelope coverage, and qualified-kind validation.
- [ ] Workbench and DecisionRecord kinds are total across the registry; an absent
  bucket does not require unrelated repositories or serializers.
- [ ] Deployment revision references survive push/pull and remain resolvable on
  the receiving database without syncing a credential.
- [ ] The five `test_primitive_contract` / `test_web_routes_sync` failures and
  the companion qualified-kind failure from HS-130-10 pass or are replaced by
  a stricter canonical-contract assertion with the old test's retirement
  recorded.
- [ ] No Swift source file changes.

## Test plan

- Unit: `uv run pytest -q tests/unit/test_primitive_contract.py tests/unit/test_web_routes_sync.py tests/unit/test_inference_kernel.py`.
- Integration: `uv run pytest -q tests/integration/test_web_companion_slack.py -k source_identity` plus deployment-revision sync round-trip and post-capture mutation tests added by this story.
- Manual / device: use an isolated database; capture a LAN deployment revision,
  edit the target, execute from the revision, and inspect the unchanged identity.

## Notes / open questions

The legacy test named `test_swift_sync_kind_matches_hub` encodes the wrong
authority direction for this program. Its behavior must become Python-contract
exactness without touching Swift. Removing the assertion without a stricter
replacement is not acceptable.
