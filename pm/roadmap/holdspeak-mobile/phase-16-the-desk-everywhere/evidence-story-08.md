# Evidence — HSM-16-08 (capability objects: the model manifest)

**Done 2026-07-04. The genuinely-open half was the model manifest; the rest was pre-paid or
superseded — recorded below with the same honesty discipline as 16-09.**

## Survey truth-ups (what was NOT built, and why)

- **Pre-paid:** workflow/model as first-class desk kinds (`PrimitiveKind.workflow`/`.model`,
  cartridge/crystal materials), combine-to-run (drop onto an input → `offerRunTarget` →
  `runTargetOverlay`), and the cross-node run itself (`runOnHub`, proven on real metal in
  HSM-22-04).
- **Superseded:** "dropping a model onto a workflow node sets that node's RUNS-ON" — Phase 24
  runtime profiles + `BPNode.runsOn` (22-01) are the owner-ratified shape for "where
  intelligence runs"; a second gesture for the same decision would be drift.
- **Re-read against canon:** "the run's compute target resolves via the manifest" ships as the
  manifest **informing the user's pick** in the run-target sheet — silent auto-routing to a
  cloud target would violate the one approval+egress contract (Phase 15/21).

## What shipped — the `model` manifest, the wire's eleventh kind

1. **Contract**: `ModelManifest {id ("<node>:<file>"), node, name, capabilities[]}` in
   `apple/Sources/Contracts/Primitives.swift`; `SyncKind.model` + the `models` `ChangeSet`
   bucket (tolerant decode) in `Sync.swift`; `schemas/model-manifest.schema.json`
   (`additionalProperties: false` — the availability invariant); the changeset schema +
   `validate.py` kind map + the golden fixture grew the kind (the 17-01 validator lesson
   applied up front).
2. **Hub**: `model_manifests` table (+ canonical schema snapshot regenerated with the test's
   own regex), `ModelManifestRecord` + `ModelManifestRepository`, `db.model_manifests`;
   `routes/sync.py` serves/merges the `models` bucket (LWW + tombstones via the generic
   merge) and the pull emits the hub's OWN model as a live virtual row (`desktop:intel`,
   from `intel_provider` config, never stored).
3. **iPad**: `DeskSyncDriver.localModels` — installed language GGUFs ride the push as
   manifests; the pull's `meshModels` land in `Outcome` and cache to
   `hs.desk.meshModels`; **the run-target sheet's "On your desktop" row now names the
   model it would run** (was the vague "big model").
4. **Docs**: SERIALIZATION-CONTRACT §11 brought current (eleven kinds; also fixed the
   stale post-rename `agents` naming); THE_PRIMITIVE_FRAMEWORK Model row marked landed
   with the `node` field.

## The no-binary invariant, asserted on every layer

- `validate.py` negative: a manifest smuggling `path` is rejected (ALL CHECKS PASSED).
- Swift wire test: the encoded manifest contains no `path`/`url` key.
- Hub route test: every pulled manifest's value keys ⊆ {id, node, name, capabilities,
  created_at, last_modified, deleted}.

## Proof

- `swift test` **467 / 9 skipped / 0 failures** (fixture decode/round-trip/envelope asserts
  grew into the golden tests).
- Hub: `uv run pytest tests/unit` **2474 passed** (incl. the new
  `test_model_manifest_push_pull_round_trip_and_tombstone` + LWW test, the extended
  kind-drift guards, and the regenerated schema snapshot); doc drift guard 18/18.
- App simulator build green; committed shot
  `screenshots/hsm-16-08-runtarget-named-model.png` — the sheet's hub row reads
  "Qwen3.5-9B-Instruct-Q6_K · 192.168.1.43" with the Cloud · your desktop chip.
- The live cross-device manifest round-trip (cabled iPad ↔ real hub) rides 16-06, per the
  story's own test plan.
