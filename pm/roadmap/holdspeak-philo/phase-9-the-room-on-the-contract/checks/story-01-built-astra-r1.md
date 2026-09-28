VERDICT: DO-NOT-RATIFY

FINDINGS:

1. **P1 — Resource requests can change the wrong Room.** PUT and DELETE merge the body after the URL identifiers. A request to project A with `project_id=B` and another `resource_ref` changes B, returning 200. Both preservation tests pass on `ffbeb04b` and fail here. **Tenets 3/7.** Evidence: `holdspeak/web/routes/projects.py:326`, also line 352.

2. **P2 — A1’s replay promise is incompletely implemented and tested.** Repeating a resource PUT with the same command key returns only the stored command envelope; the original resource’s `id`, `resource_ref`, relationship and timestamps disappear. The fence compares only `project_revision`, hiding this mismatch. The underlying ledger limitation is inherited, but this newly exposed replay contract remains unpaid. **Tenets 3/7.** Evidence: `tests/unit/test_philo9_room_contract.py:97`, `holdspeak/services/project_service.py:4644`.

3. **P2 — Discovery teaches the same wrong review field that story 02 must repair.** The catalogue directs callers to `open_review.id`; both real producers return top-level `review_id`. The discovery fence checks that a named tool exists, without resolving the advertised response path. **Tenets 3/4.** Evidence: `holdspeak/operations.py:1607`, `holdspeak/services/project_delta_service.py:1901`, `tests/unit/test_philo9_discovery.py:124`.

4. **P2 — New drafts hide an existing published update.** After publishing once and creating eleven newer drafts, the Room reports `counts.published=1` but `latest_published=null`. The lookup searches only the ten recent rows. This also hides that update’s deliveries from this projection. **Tenets 3/7; Article VI.** Evidence: `holdspeak/services/project_service.py:672`.

5. **P2 — The compatibility claim overlooks a previously supported field.** HTTP item creation accepted and stored `source_observation_id` on the base. The new closed descriptor rejects it with 400. It is a consumed field, not an ignored unknown field. The preservation test covers only `provenance_kind`. **Tenets 3/7.** Evidence: `holdspeak/operations.py:1864`, `holdspeak/services/project_service.py:3897`, `tests/unit/test_philo9_contract.py:231`.

All five findings have executable reproductions: **six failing checks** in [review tests](/tmp/astra-pr680.dIiaOA/test_pr680_review.py), with [results](/tmp/astra-pr680.dIiaOA/review-red.log).

The supplied proof is otherwise substantial: I independently reproduced **114 passed, 1 expected failure**, plus **419 existing tests passed**; all eight behavioral reds and F14’s `ModuleNotFoundError` reproduce on the base. The census reports **263 residual identities and 236 tools**. Own/foreign receipt authorization and the delivery mutation fence pass.

CONDITIONS:

- Fix findings 1–5 and strengthen their fences: URL target ownership, complete replay responses, real response-path discovery, published-update lookup beyond the recent window, and preservation of consumed HTTP fields.
- Change the discovery words and their fence together.
- Supply the required verification evidence before merge; the current record does not establish every claimed acceptance criterion.

MISSED:

Ranked by owner cost: wrong-Room mutation; incomplete retry responses; misleading review discovery; disappearing published-update projection; rejected provenance input.

`enforced=False` follows the charter’s explicit story-01/story-02 sequencing and is openly exported and fenced. It is declared migration debt, with Article XI enforcement still owed by story 02. The delivery transaction seam fits the steward beat. Story 02 must also replace the early validation/refusal paths as its B2 contract requires.

I found no lying field in the rewritten needs-you double. It inherits the real aggregation method; the separate F13 fence uses real stored proposals and mute settings. The receipt-palette rewrite retains own/foreign authorization coverage.

The `web/src` search found no active caller relying on the newly rejected fields: Door creation sends `outcome/sources`, filing sends `relationship`, and project rename uses PATCH. Current-face compatibility looks sound by inspection; finding 5 still breaks the broader HTTP compatibility claim.

TUESDAY: The normal Room path improves, but wrong-target writes and misleading discovery prevent a reliable Tuesday verdict.

UNKNOWN:

No 1440/393 shots, actual atlas-run observations, or full-suite result were present in the supplied evidence. The rig test exercises request helpers for two operations; the restart test rebuilds the app inside one process. Neither proves the corresponding live walk. I reviewed the ratified steward beat from `main`, since it is absent at this PR head.

Reviewed `74a9bdd5` in a fresh worktree. The tracked tree is unchanged.