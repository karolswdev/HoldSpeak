# Evidence — HSM-18-07 — The Desk-Era rider

**Status:** done (2026-07-03). Two commits on `holdspeak-mobile/hsm-18-07-desk-era-rider`:
the contract half (`origin` on the wire), then the desk half (identity + the beat).

## 1. `origin` joins the artifact contract

- **Hub:** `ArtifactSummary.origin` (`holdspeak/db/models.py`, default `"meeting"`), populated
  from the row at all three mapper sites (`holdspeak/db/plugins.py`); emitted by
  `_artifact_value` (sync pull, `holdspeak/web/routes/sync.py`) and the meeting-artifacts
  route (`holdspeak/web/routes/meetings/insights.py`).
- **Schema:** `contracts/schemas/artifact.schema.json` gains `origin` as an **optional**
  enum (`meeting` | `run`) — optional because a client push may omit it (the hub derives it
  from `meeting_id` on merge, `plugins.py:691`); hub emissions always carry it. Fixture
  updated (kept canonical — the validator's round-trip rule requires exact
  `json.dumps(indent=2)` form).
- **Swift:** `Artifact.origin: String?` + `Artifact.isRunBorn` (the hub's own derivation as
  fallback when the wire omits the field); `MeetingArtifact.origin: String?`. iPad SQLite
  stores artifacts as JSON blobs, so `origin` persists with zero storage changes.
- **Proven:** `uv run pytest -q tests/unit` **2397 passed** (incl. the new
  `test_origin_explicit_on_every_serialized_surface` — both surfaces, schema-validated,
  origin-less back-compat); `swift test` **416 passed** (incl.
  `testArtifactOriginDecodesAndDerivesRunBorn` — present / absent / unknown);
  `contracts/validate.py` ALL CHECKS PASSED.

## 2. The route-surface lock — already shipped, recorded not duplicated

Design item 3 was verified to already exist as **HS-72-02**:
`scripts/gen_api_surface.py` sweeps `apple/**/*.swift` for `api/…` path literals and
`tests/unit/test_api_surface.py` fails CI unless every extracted iOS call matches a served
route (`unmatched_calls` must be empty; `/api/coders/dismiss` shows `"ios"` as a consumer in
the committed `docs/api-surface.json`). Zero stale `api/companion` literals remain in Swift.
Building a second guard would have been duplication; the story records the finding instead.

## 3. Run-born artifacts land on the iPad desk

Grounded in a full map of the desk's artifact path (the sync bridge upserts hub artifacts
into `outputs`; `derivativesOf` groups meeting-anchored ones into the drawer; a run-born
card falls through and sits loose — correct). The three real gaps, fixed:

- **The hub's `artifact_id` was silently dropped.** `HubRunResult` never decoded it, so
  `runOnHub` minted a throwaway UUID and a kept card would **duplicate** against the hub's
  own artifact on the next sync. Now: `HubRunResult.artifactId` decodes (tolerant — an older
  hub omits it) and the printed card reuses the hub's id, so Keep reconciles instead of
  duplicating. Proven: `testRunAgentDecodesArtifactId` /
  `testRunChainWithoutArtifactIdStillDecodes` (stubbed transport).
- **No arrival beat on a kept run result.** `keepPrinted()` now fires the exact beat woven
  deliverables and synced peers get (`arrivedIds` halo + NEW badge + flash, 6s clear).
- **Desk-minted cards now say `origin: "run"`** on their embedded contract
  (`DeskRecords.swift` desk-authored init) instead of leaving the wire to infer it.
  Proven: `testOutputRecordRoundTrip` asserts `origin == "run"` and `isRunBorn`.

**Simulator proof:** full `xcodebuild` (iphonesimulator, iPad Air 13-inch (M4)) green; the
`HS_DESK_ARRIVE=1` seed extended with a genuine run-born card (agent lens, non-meeting
source). Screenshot: [`screenshots/hsm-18-07-run-born-arrival.png`](./screenshots/hsm-18-07-run-born-arrival.png)
— the run-born card **loose on the desk** (not in a meeting drawer) with the arrival halo +
NEW badge, beside the meeting cassette with the same beat.

## Honest boundaries

- The beat on a real hub run (tap Run on a paired desk → Keep) is Simulator-verified logic
  reusing a proven mechanism; the on-device walk is the phase gate (HSM-18-06) plus the
  owner's standing device pass — not claimed here.
- The web agent editor still doesn't surface `manual_context` (a Desk-Era handover note,
  hub-side; out of this story's scope).
