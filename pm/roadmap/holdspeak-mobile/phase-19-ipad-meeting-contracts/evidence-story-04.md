# Evidence — HSM-19-04 — Artifact provenance: the confidence ring + sources

**Status:** done (2026-07-03), on `holdspeak-mobile/hsm-19-open`. The build itself merged
before the phase formally opened (client: PR #151/`3544fc1`; UI: PR #159 `1b34b14`; the
EQ-W6 metal-readiness fix: `050d176`/`4865a8f`). This file is the story's evidence trail,
verified against the shipped code today.

## 1. The client reads the hub's persisted artifacts

`HTTPDesktopClient+Artifacts.swift:26` — `meetingArtifacts(meetingId:)` GET
`/api/meetings/{id}/artifacts` (hub route `holdspeak/web/routes/meetings/insights.py:117`),
decoding `MeetingArtifact` with the two fields the audit found dropped: `confidence` and
`sources`. This answers the phase doc's "deeper question": the iPad reads the hub's source
of truth, not only the changeset sync.

## 2. The render: the ring + the trail

`CompanionShellApp.swift`:

- `ConfidenceRing` (line 46) — the synthesis confidence as a banded arc (≥0.75 green /
  ≥0.5 amber / low red), the number in the center; a `nil` confidence renders the ring
  dimmed at 0 — never invented.
- `artifactsCard(_:)` (line 327) — ring + title + status pill (accepted / needs review /
  rejected) + the type + "Synthesized from transcript · decision" source trail.
- Wired: tapping a desktop meeting row loads artifacts + aftercare together
  (`loadArtifacts`, line 175; the tap at line 466).

Screenshot: [`confidence-ring-ipad.png`](./screenshots/confidence-ring-ipad.png)
(`HS_SHELL_DEMO=artifacts` — three confidences banding green/amber/red).

## 3. The metal-readiness catch (EQ-W6, locked by test)

`ArtifactsClientTests.swift` decodes the route's REAL wire shape — including
`created_at: "2026-06-27T10:00:00.123456"` (naive/local, microseconds, no `Z`). The
contract originally decoded these as `Date` via `.iso8601`, which throws on a zone-less
string and would have failed the whole artifact decode on real metal; timestamps are now
raw `String?`. The load-bearing assertions: `confidence == 0.82` and both `sources`
entries decode.

## Honest boundaries

- The desk app's local `ReviewUI` artifacts carry **no ring** by design: handwritten notes
  are confidence-1.0 by construction; hub-provenance rendering is the Companion shell's job.
- `/api/all-action-items` remains unread from Swift — named, deliberately out.
- Real-metal verification (a live hub's real synthesized artifacts on the cabled iPad)
  rides the 19-07 walk (check W4).

## Suites

`swift test` **425 passed / 8 skipped / 0 failures** (incl. `ArtifactsClientTests`) ·
companion-shell simulator build (`gen-companion-shell.rb` → xcodebuild, iPad Air 13-inch
M4) **BUILD SUCCEEDED** — both run today.
