# Evidence - HSM-27-02

- **Story:** HSM-27-02 - The terminal surface on the diorama
- **Status:** done
- **Date:** 2026-07-08

## Proof

### Captured run — 2026-07-09T01:18:07Z

- **Command:** `bash -c cd apple && swift test 2>&1 | grep -E 'Executed.*failures' | tail -1 && echo '--- sim build ---' && xcodebuild -project build/HoldSpeakMeetingCapture.xcodeproj -scheme HoldSpeakMobile -destination 'generic/platform=iOS Simulator' -derivedDataPath build/mc-sim -skipMacroValidation CODE_SIGNING_ALLOWED=NO build 2>&1 | grep -E 'BUILD SUCCEEDED|BUILD FAILED'`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3331dc2b286a9f6c1e63ec3cfbb95da3f7dbd5e8

```text
	 Executed 519 tests, with 9 tests skipped and 0 failures (0 unexpected) in 1.834 (1.871) seconds
--- sim build ---
** BUILD SUCCEEDED **
```
