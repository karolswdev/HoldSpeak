# Evidence — HSM-21-02 — The Swift banned-copy + reassurance-prose guard

**Status:** done (2026-07-03), on `holdspeak-mobile/hsm-21-02-swift-guard`.

## 1. The sites fixed (the guard then found a 7th)

Every "on-device · nothing leaves" label adopts the badge grammar ("on device" / the
`EgressScope` constants):

- `LocalHarnessApp.swift`, `SpeakHarnessApp.swift` (Text labels),
  `InferenceHarnessApp.swift` (the egress descriptor's `.local` arm).
- `RuntimeCore`: `MeetingCapture.egressLabel` + `ReviewModel.egressLabel` (and their two
  test assertions updated with them).
- `DeskHome.swift` model-card snippet: the ", nothing leaves." tail died (labels, not
  manuals).
- **The 7th, caught by the new guard itself on its first run** (the survey had missed it):
  `MeetingCaptureApp.swift:693` — the classic home header's
  `"ON-DEVICE · NOTHING LEAVES"` capsule, now rendered from `EgressScope.local`
  (label + symbol).

Screenshot: [`hsm-21-02-header-on-device.png`](./screenshots/hsm-21-02-header-on-device.png)
— the home header wearing **ON DEVICE**.

## 2. The guard (`tests/unit/test_doc_drift_guard.py`)

- `_swift_user_facing()` sweeps `apple/App/**` + `apple/Sources/**` (never the staged
  `build/`); `_SWIFT_STRING` scans **string literals only**, so code comments and doc
  comments stay legal — and the Qlippy DOC test that REQUIRES the verbatim phrase in a
  doc is untouched (docs rule vs UI rule, kept apart deliberately).
- `test_no_swift_copy_uses_banned_feature_names` — the `_BANNED_NAMES` synonyms cannot
  reappear in iPad copy.
- `test_no_swift_copy_narrates_privacy_reassurance` — `nothing leaves` / `never leaves` /
  `stays on this|your` in a Swift string is a failure with the fix named (render the
  `EgressScope` badge).
- `test_swift_guard_scans_the_app_sources` — the red-proof: >50 files reached (incl.
  `CompanionShellApp` / `DeskDioramaStage` / `EgressScope`), a seeded violation literal
  flags, the same words in a comment do not, a seeded banned-name literal flags.

## Honest boundaries

- Multi-line `"""` literals are outside the per-line literal scan (UI label copy in this
  codebase is single-line) — noted in the guard's own comment.
- `apple/scripts/diorama/Diorama.swift` (a throwaway render harness, not App/Sources)
  keeps one demo sentence; out of the product-copy scope on purpose.

## Suites

`uv run pytest -q tests/unit/test_doc_drift_guard.py` **18 passed** (was 15; +3 Swift
tests, first run caught the 7th site) · `swift test` **428/8-skip/0-fail** (the two
updated egressLabel assertions green) · sim builds: meeting-capture, companion-shell,
Harness, SpeakHarness + LocalHarness (via `patch-llm-macro.sh` +
`-disableAutomaticPackageResolution`, the standing toolchain workaround) — all
**BUILD SUCCEEDED**.
