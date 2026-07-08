# Evidence - HSM-26-02

- **Story:** HSM-26-02 - The belt on the diorama
- **Status:** done
- **Date:** 2026-07-08

## Proof

### Captured run — 2026-07-08T13:51:35Z

- **Command:** `bash -c cd apple && swift test --filter MissionControlTests`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7f35e327415730454253f8b74ce1cc981e855ee

```text
[0/1] Planning build
Building for debugging...
[0/2] Write swift-version-39B54973F684ADAB.txt
Build complete! (1.68s)
Test Suite 'Selected tests' started at 2026-07-08 07:51:38.281.
Test Suite 'HoldSpeakMobilePackageTests.xctest' started at 2026-07-08 07:51:38.282.
Test Suite 'MissionControlTests' started at 2026-07-08 07:51:38.282.
Test Case '-[ContractsTests.MissionControlTests testARailsRefRoundTripsToTheWire]' started.
Test Case '-[ContractsTests.MissionControlTests testARailsRefRoundTripsToTheWire]' passed (0.002 seconds).
Test Case '-[ContractsTests.MissionControlTests testBeltStateDecodesFromTheStateFeedShape]' started.
Test Case '-[ContractsTests.MissionControlTests testBeltStateDecodesFromTheStateFeedShape]' passed (0.001 seconds).
Test Case '-[ContractsTests.MissionControlTests testTheSteeringAndRailsFixtureDecodes]' started.
Test Case '-[ContractsTests.MissionControlTests testTheSteeringAndRailsFixtureDecodes]' passed (0.002 seconds).
Test Suite 'MissionControlTests' passed at 2026-07-08 07:51:38.288.
	 Executed 3 tests, with 0 failures (0 unexpected) in 0.005 (0.006) seconds
Test Suite 'HoldSpeakMobilePackageTests.xctest' passed at 2026-07-08 07:51:38.288.
	 Executed 3 tests, with 0 failures (0 unexpected) in 0.005 (0.006) seconds
Test Suite 'Selected tests' passed at 2026-07-08 07:51:38.288.
	 Executed 3 tests, with 0 failures (0 unexpected) in 0.005 (0.007) seconds
◇ Test run started.
↳ Testing Library Version: 1743
↳ Target Platform: arm64e-apple-macos14.0
✔ Test run with 0 tests in 0 suites passed after 0.001 seconds.
```

### Captured run — 2026-07-08T13:51:38Z

- **Command:** `bash -c cd apple && xcodebuild -project build/HoldSpeakMeetingCapture.xcodeproj -scheme HoldSpeakMobile -destination 'generic/platform=iOS Simulator' -derivedDataPath build/mc-sim -skipMacroValidation CODE_SIGNING_ALLOWED=NO build 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7f35e327415730454253f8b74ce1cc981e855ee

```text

** BUILD SUCCEEDED **
```
