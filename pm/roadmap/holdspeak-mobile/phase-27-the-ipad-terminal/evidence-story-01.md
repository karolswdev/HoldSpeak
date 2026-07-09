# Evidence - HSM-27-01

- **Story:** HSM-27-01 - The steering client parity
- **Status:** done
- **Date:** 2026-07-08

## Proof

### Captured run — 2026-07-09T00:47:21Z

- **Command:** `bash -c cd apple && swift test --filter SteeringClientTests 2>&1 | tail -6`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a384aa4f2b2e92a0efcd3a2671db37279b82c4da

```text
Test Suite 'Selected tests' passed at 2026-07-08 18:47:22.112.
	 Executed 16 tests, with 0 failures (0 unexpected) in 0.015 (0.017) seconds
◇ Test run started.
↳ Testing Library Version: 1743
↳ Target Platform: arm64e-apple-macos14.0
✔ Test run with 0 tests in 0 suites passed after 0.001 seconds.
```
