# Accuracy check — Luna

Source reviewed: `675401a857b85336d4acaa8c65383dfc9636e4c8`.
Scope: source truth for the new architecture/security/storage/meeting/runtime/
destination documents and Philo registries. No product edits, live hub, owner
database, provider, network, full test suite, stage, commit, or story flip was
performed.

VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:

1. **The Gate source has an unsafe preview, and the remaining evidence wording must stay honest.** The current correction at `docs/GATE.md:74-79` and `docs/SECURITY_MODEL.md:175-182` now accurately warns that the 120-character preview is truncation, not secret redaction. `holdspeak/coder_gate.py:136-144` still canonicalizes the complete input and returns `canonical[:120]`; a short key in that prefix reaches `args_head` and the proposal row. The residual mismatch is `docs/GATE.md:83-89`, which says `tests/unit/test_coder_gate.py` checks “redaction,” while `tests/unit/test_coder_gate.py:199-204` checks only hash/canonical ordering and length; `tests/unit/test_gate_chokepoint.py:78-91` and `tests/integration/test_gate_threat_model.py:298-303` check that full `tool_input` is absent, not that a short secret is absent from the head. Keep the new executable unsafe-preview claim and rename the test evidence to truncation/bounded-head evidence, or add a real secret-redaction assertion. This fails Tenets 1 and 3 if the evidence continues to imply protection that the code does not provide. **High.**

2. **Kernel content claims are broader than the source contract.** `docs/KERNEL.md:60-64,216-219`, `docs/SECURITY_MODEL.md:95-97,127-132`, and `docs/STORAGE_AND_MIGRATIONS.md:102-105` describe the kernel as unable to retain prompt/transcript/completion content and as storing only references and hashes. `holdspeak/kernel/model.py:9-13,65-73` rejects only the named audio/PCM/token keys. `holdspeak/kernel/parent_run.py:32-35,105-106` accepts a general mapping snapshot and persists it in `kernel_parent_runs.input_json`; `holdspeak/services/agent_turn_service.py:148-158` places cleaned messages there, and `holdspeak/services/sequence_workflow_service.py:322-328` stores the request body. The generic journal may remain content-restricted, but the blanket kernel/metadata wording is false and the receipt-only limitation does not cover parent snapshots. This fails Tenet 7 (the senior architect needs a truthful authority/data boundary). **High.**

3. **The documented startup recovery order is wrong for the actual runtime entry point.** `docs/KERNEL.md:223-227`, `docs/SECURITY_MODEL.md:148-152`, and `docs/STORAGE_AND_MIGRATIONS.md:130-137` say liveness reaping occurs before route recovery and projection recovery. `holdspeak/kernel/runtime.py:173-175` calls `reconcile_abandoned()`, then `recover_route_executions()`, then `projection_stager.recover()`. The stager's own `holdspeak/kernel/projection_stager.py:343-346` calls `reap_expired()`, while the separately named helper in `holdspeak/kernel/broker.py:275-284` has the safe parent → reap → projection sequence. The docs conflate those paths and cite the broad runtime range as proof. This fails Tenet 7 and risks a false recovery guarantee. **High.**

4. **Record-only meetings are promised a final transcription that the source drops.** The lifecycle graph and prose at `docs/MEETING_ARCHITECTURE.md:13-31` route record-only capture through “final transcribe remaining audio.” In `holdspeak/meeting_session/transcribe_loop.py:61-66`, a missing transcriber logs a named refusal and returns `None`; `session.py:603-610` starts the transcription thread only when a transcriber exists. The final stop path can call the seam, but it cannot transcribe a record-only session. Qualify the graph and stop behavior as “final transcription when a transcriber was admitted; otherwise preserve record-only capture.” This fails Tenet 3 because the owner would expect text after a record-only meeting. **High.**

5. **The SRS overstates provider-key exclusion from Web state and storage.** `docs/internal/philo/SRS.md:151-155` says provider keys never enter Web state or storage. `web/src/pages/cores/ModelLibraryCore.tsx:219-239,252-273,383-397` reads the key from a password DOM input and sends it in the connect request; `holdspeak/profile_key_store.py:30,46-52` persists the key in local custody. The narrower true statement is that the key is excluded from the persisted Web app projection/local browser storage and from public profile/receipt DTOs; the temporary form/request and backend custody are real boundaries. This fails Tenet 7 and can mislead the owner about the actual secret path. **Medium.**

6. **Aftercare documentation collapses two provenance guards with different behavior.** `docs/MEETING_AFTERCARE.md:33-35` says an out-of-range timestamp is rejected by decision capture and that aftercare therefore reports a bounded source reference. `holdspeak/plugins/builtin/decision_capture.py:239-259` does reject it and records `provenance_drops`, but the aftercare resolver independently clamps a malformed/out-of-range value; the inspected test named at `docs/MEETING_AFTERCARE.md:43` covers that behavior. State that normal plugin output drops the field, while aftercare's defensive resolver clamps malformed persisted artifacts. This is a lower-cost Tenet 7 accuracy condition.

CONDITIONS:

1. Keep the Gate docs explicit that the preview is sensitive truncation, and change the “redaction” test wording to bounded truncation unless code is changed to actually redact. Keep the focused short-secret executable claim in the metadata.
2. Narrow kernel/security/storage wording to the generic journal/operation fields, or explicitly document and classify parent input snapshots as content-bearing domain/service storage. Add a source-backed claim/test for the distinction.
3. Describe the real `runtime.py` startup path separately from `Broker.reap_and_recover_projections`, and do not claim a global liveness-before-route ordering until the source does that.
4. Qualify record-only final transcription and distinguish decision-plugin rejection from aftercare defensive clamping.
5. Correct the SRS provider-key sentence to identify persistent Web-state exclusion, temporary browser/request handling, and backend custody.
6. Re-run the bounded architecture validator and doc-claim coverage check after these edits. Keep all named test evidence labelled `not_run`; no owner or live integration result follows from source inspection.

MISSED:

1. Gate secret leakage is the highest owner cost because it defeats the stated held-tool privacy boundary.
2. The parent snapshot path is easy for future service authors to extend with transcript/prompt content while believing the kernel is content-free.
3. Recovery-order prose can cause an operator to trust a projection state before the route-recovery path has been understood.
4. Record-only users can lose the expectation that stop creates text; this is a Tuesday-facing contract mismatch.
5. Integration inventory review found no additional high-risk authority mismatch in the seven new integration records, but it did not execute provider, companion, actuator, or owner paths.

TUESDAY: Not yet for the affected contracts: the owner can read the guides, but the Gate privacy promise, startup ordering, and record-only meeting outcome are currently unsafe to use as operating instructions.

UNKNOWN:

- I did not run the full unit/integration/browser suites, a live hub, an owner database, a model/provider, or a network/companion path.
- I did not classify missing integration/visual artifacts as defects; those lanes were still being authored per the brief.
- I inspected source and named assertions at the pinned snapshot. The current working tree is dirty and the Gate/security warning correction landed during this review; the remaining condition is the test-evidence wording and the source-level unsafe preview behavior.

## Final recheck disposition — 2026-09-19

The author applied the six requested documentation/metadata corrections. I
re-read each affected assertion and ran the bounded validators after the edits.
This section supersedes the initial conditional disposition above.

VERDICT: RATIFY

FINDINGS:

1. **Resolved.** `docs/GATE.md:74-79` and `docs/SECURITY_MODEL.md:175-182`
   now state the actual Gate behavior: the preview is a 120-character
   truncation and can retain a short credential. The new registered executable
   claim at `tests/unit/doc_claims/registry.py:363-370` observes that synthetic
   prefix, and `doc_claims.py --measure` reports it `HOLDS`. The product
   redaction improvement remains an engineering proposal; this accuracy check
   does not require it. The word “redaction” in the existing test name/evidence
   is read in the bounded-preview sense and is qualified by the surrounding
   warning.
2. **Resolved.** `docs/KERNEL.md:60-67,217-223`,
   `docs/SECURITY_MODEL.md:95-97,127-133`, `docs/STORAGE_AND_MIGRATIONS.md:102-106`,
   and `runtime.json` now distinguish content-restricted journal/receipt paths
   from content-bearing parent snapshots. The executable claim at
   `tests/unit/doc_claims/registry.py:372-404` admits a real disposable
   Sequence parent and reads back the synthetic prompt from `input_json`;
   `doc_claims.py --measure` reports it `HOLDS`.
3. **Resolved.** `docs/KERNEL.md:227-233`,
   `docs/SECURITY_MODEL.md:149-155`, and `docs/STORAGE_AND_MIGRATIONS.md:133-141`
   describe the actual runtime entry path and separately identify the helper
   that reaps before projection recovery. They no longer claim global
   liveness-before-route ordering.
4. **Resolved.** `docs/MEETING_ARCHITECTURE.md:8-34,106-108` and
   `voice.json` qualify final transcription on an admitted transcriber and say
   record-only stop preserves capture without creating transcript text.
5. **Resolved.** `docs/internal/philo/SRS.md:151-158` identifies temporary
   password-input/request handling, exclusion from persisted Web projections
   and public DTOs, and separate backend custody.
6. **Resolved.** `docs/MEETING_AFTERCARE.md:33-35` now distinguishes plugin
   rejection from aftercare resolution: out-of-range numeric values can clamp
   to the selected segment, while missing/non-numeric values and empty segment
   lists return no reference. This matches
   `holdspeak/meeting_aftercare.py:38-76` and the decision plugin at
   `holdspeak/plugins/builtin/decision_capture.py:239-259`.

CONDITIONS: None for documentation/source accuracy. The Gate's unsafe
truncation remains a documented product limitation and a separate engineering
proposal; no runtime redesign is required to ratify the current truthful docs.

MISSED: No new documentation/source defect was found in these six rechecks.
The highest owner cost remains the known Gate prefix leakage, which is now
explicitly disclosed rather than misrepresented as secret redaction.

TUESDAY: Yes for the reviewed documentation contracts: the owner can now see
which paths retain content, which recovery order actually runs, when a meeting
has no transcript, how aftercare resolves timestamps, and where provider/Gate
secrets can exist.

UNKNOWN: Full suites, live hub/database/provider/network behavior, owner use,
integration execution, and visuals remain unverified as stated above. The
bounded checks passed: `validate_architecture.py --allow-missing-shards`
reported 4 shards/147 records, `check_doc_coverage.py --check
--allow-missing-shards` completed, and `doc_claims.py --measure` reported zero
drift (19 claims, four pre-existing known-false ratchet rows).

## Astra final disposition

The Luna verdict applies to its six inspected corrections. Subsequent root
validation also corrected the four existing descriptive known-false records;
19 executable document claims now report zero drift and zero known-false rows.
The full suite and baseline investigation are recorded separately in the final
audit. This update does not expand Luna's verdict into hardware, owner-use,
release, accessibility or whole-product certification.
