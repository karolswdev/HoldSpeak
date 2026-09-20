# HS-201-05 - One engine and one assignment from the face

- **Project:** holdspeak
- **Phase:** 201
- **Status:** done
- **Depends on:** HS-201-02
- **Unblocks:** (optional)
- **Owner:** Astra (lane A; face in B)

## Problem

The path needs exactly one text engine and one EXACT capability assignment for `meeting.deferred_analysis` on the SERVICE principal `meeting-intel-queue` (audits/runtime-astra.md facts 3, 4). The live DB holds only `speech.transcribe`. The Concierge's `Use these` writes GROUP assignments only (`concierge_service.py:1148`), which the SERVICE principal cannot see by law (`inference_service_route_policy.py:93`, Constitution XI.4). The owner's config names cloud `gpt-5-mini` (`config.json:28`); the Concierge proposes a local Qwen for everything including speech (walk defect 10).

## Scope

- **In:** an explicit, disclosed SUMMARY-SELECTION gesture in Models ("Use this for meeting summaries", on `Use these` for the summary group, or on a connected hosted/LAN engine) mints the exact `meeting.deferred_analysis` assignment through `InferenceAssignmentService.set_assignment` with the real profile revision, revision-conflict handling and truthful partial-failure feedback; merely connecting an engine does NOT change assignments (the library preserves them, `model_library_service.py:3`); speech assignments are preserved; the owner's gesture is the approval (XI.4), one visible result, internal receipts kept; the Models face shows, for the summary group, the engine that will run it; speech is never offered a text model.
- **Out:** the model-era collapse; the Models naming collapse; new download flows.

## Acceptance criteria

- [x] **A-proven:** Isolated HOME: the summary-selection HTTP gesture; `inference_assignment_heads` then holds an exact `capability:meeting.deferred_analysis` row for a compatible profile, revision from the real service; connecting an engine without the gesture changes no assignment; the speech row is unchanged.
- [x] **A-proven:** A revision conflict and a partial failure each return a truthful typed result and visible receipt, with no silent success.
- **Transferred to HS-201-06 (see status):** Models renders these results and the assigned engine at both widths.
- [x] **A-proven:** The meeting queue's SERVICE principal freezes a route with that assignment (the binder test).
- [x] **A-proven:** Speech recognition is never assigned a text-only profile (fence).
- [x] **A-proven:** One summary-selection gesture returns one visible receipt.
- **Transferred to HS-201-06 (see status):** The face uses one gesture with no modal; Models shots after accept at both widths.

## Test plan

- **Unit:** the assignment write and the compatibility fence.
- **Integration:** Concierge accept then binder freeze in one e2e.
- **Manual / device:** the Models shot after accept, both widths.

## Notes / open questions

Lane A (Astra to Luna) for the service and the read model; the Models FACE edit is lane B (story 06 owns `web/src/features/concierge/*` on this path) against A's contract. Serves exit criteria 3 and 4. Isolated credential storage for any rig that connects a hosted engine (keychain inside the walk HOME). Which engine the owner picks is his (his config says cloud gpt-5-mini; the expected host is then api.openai.com).

## Lane delivery boundary

A owns the service and read model; B owns the Models gesture and its rendering
in HS-201-06. The real producer → detect → HTTP selection → ready route → binder
path is proved in `evidence-story-05.md`. The checked producer amendment mints
a new manifest declaring existing adapter support; it does not rewrite old
profile revisions or make an assignment when a model is connected.
