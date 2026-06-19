# HSM-1-03 — CI pipeline (iPhone + iPad sim)

- **Project:** holdspeak-mobile
- **Phase:** 1
- **Status:** backlog
- **Depends on:** HSM-1-01
- **Unblocks:** HSM-1-04
- **Owner:** unassigned

## Problem

Without CI, the four-layer rule and the contract round-trip are only as good as
whoever ran them last on their laptop. The charter's Gate 1 covers iPhone *and*
iPad, so a single-destination green build is a false signal. We need a pipeline
that builds the package and runs the tests against both an iPhone and an iPad
simulator destination, failing loudly if either is missing.

## Scope

- **In:** a CI workflow (e.g. `.github/workflows/` for the mobile package) that,
  on push/PR touching the mobile source, runs `swift build` and `swift test` (or
  `xcodebuild test`) against an explicitly-pinned iPhone simulator destination AND
  an iPad simulator destination. The job fails if either destination is
  unavailable on the runner. The CI host decision (deferred on the phase status
  doc) recorded here.
- **Out:** the test *content* (HSM-1-02 round-trip, HSM-1-04 harness/launch) —
  this story wires the runner, the other stories supply what it runs. Device
  (non-simulator) runs, code signing, TestFlight. Release packaging.

## Acceptance criteria

- [ ] A CI workflow file exists and triggers on changes to the mobile package.
- [ ] The workflow builds the package and runs the tests against an iPhone
      simulator destination — green on a real run (link the run in evidence).
- [ ] The workflow builds and runs against an iPad simulator destination — green
      on the same real run.
- [ ] Both destinations are pinned explicitly (device name + OS), and the job
      fails (does not silently skip) if a destination is missing from the runner
      image.
- [ ] The chosen CI host (GitHub-hosted macOS runner vs. self-hosted) is recorded
      in the workflow or the package README.

## Test plan

- Unit: the CI run itself is the test — a green run over both destinations, linked
  in evidence (the actual run, not a local re-creation).
- Integration: a deliberately broken commit (e.g. a failing test) produces a red
  CI run — proves the gate actually gates. Capture once in evidence.
- Manual / device: confirm the runner image lists the pinned iPhone and iPad
  simulators before relying on them.

## Notes / open questions

- CI host is a deferred decision (phase status doc); default is a GitHub-hosted
  macOS runner. If signing or real-device runs are ever needed, revisit then — not
  in this story.
- Pin simulator destinations to versions the runner image actually ships;
  unpinned "latest" destinations are the classic source of a green-then-red CI.
- Reuse the desktop repo's CI conventions where they fit, but the mobile package
  builds with the Apple toolchain, not `uv`/`pytest` — keep the workflows separate.
