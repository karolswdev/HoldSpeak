# Phase 108 - The Locked Room

**Status:** CLOSED (7/7). Activated and built 2026-07-29 by owner
direction; closed 2026-07-30 after the corrected 8/8 machine sitting and
the owner's verdict: "'s all's good, moyt."

**Last updated:** 2026-07-30 (the debt register is empty; raw desktop
typing crosses a warrant-validating spawned process; terminal text and
keys are universally `process.input@1`; CLI reads require authenticated
principals; generic liveness and the mandatory live-bus CI gate are in
place).

## Why this phase exists

Phase 107 moved the constitutional effect debt from 38 sites to 15 and
left every remainder with a machine-asserted closing condition. Five
were audited side doors in otherwise migrated families:

- T01/T02: the web steering text and keys routes could still reach the
  tmux transport without `process.input@1`.
- C02/C03/C05: GitHub, Jira, and Delivery Workbench reads still had
  ambient `LOCAL_OWNER` defaults.

The other ten, A01-A10, were the raw desktop primitives themselves:
clipboard replacement, synthetic key press/release/type, and a dormant
AppleScript helper. Routing their caller through `desktop.type_text@1`
did not confine those primitives. They still lived in the ordinary
runtime's `TextTyper`.

Article XI's transitional clause 6 was explicit: it and the register
expire together when the register is empty. This is the phase that
meets that condition without pretending a Python package is a
general-purpose OS sandbox.

Two operational debts ride because they directly affect whether the
kernel tells the truth: approved work needed a generic deadline when an
executor disappears, and `tests/e2e/test_live_bus.py` needed to become a
mandatory built-bundle browser gate instead of an optional local skip.

## The honest boundary

**The production desktop typing path now has process confinement. The
whole Python installation is not an arbitrary-code sandbox.**

`TextTyper` is a warrant-only proxy. An anonymous pipe reaches a small
spawned child. The child independently validates the signed warrant,
current policy version, exact request shape, operation, target,
placement, payload hash, claim/execution deadlines, one-use ID, and
focused-window generation before importing the raw keyboard/clipboard
driver. A timeout is indeterminate and never retried.

Same-user Python can still launch OS processes, open sockets, and read
installed source. Therefore this phase does not authorize untrusted
plugins or agent-authored Python to execute inside the ordinary web
runtime. RFC §5b's complete process/OS-isolation threshold remains the
prerequisite for adding that capability. The stronger claim earned here
is precise: every known production route in the ratified census has an
enforcement or exemption proof, and desktop typing has an independently
validating process boundary.

## Constitutional grounding

- **Article V:** text and key delivery still use the existing owner
  gesture/grant semantics; the migration adds no second confirmation.
- **Article VI:** malformed, forged, expired, replayed, stale-focus, and
  silent-executor outcomes are named. No failure quietly retries.
- **Article IX:** the raw executor ran against a real TextEdit window on
  this Mac; the owner supplied the closeout verdict after the corrected
  machine sitting.
- **Article XI.2-5:** universal terminal admission, mandatory read
  principals, immutable signed warrants, and effect-free read treatment
  are enforced at the audited entry points.
- **Former Article XI.6:** its owner-ratified sunset fired when the
  checked-in debt register reached zero. Recording that mechanical
  sunset is not an agent amendment.

## Goal

Empty the Article XI transitional effect debt register honestly. Every
T01/T02 transport act enters `process.input@1`; every C02/C03/C05 read
begins with an authenticated principal; A01-A10 are deleted or reachable
only after an independently validated one-use warrant in the spawned
desktop executor. Silent operations terminalize generically, and the
live browser bus can no longer skip in CI.

## Scope

- **In:** A01-A10 desktop confinement/deletion; T01/T02 universal
  process-input routing; C02/C03/C05 mandatory read principals; the
  generic operation liveness rider; the live-bus CI gate; the empty
  debt register and constitutional/security documentation; closeout.
- **Out:** executing untrusted Python in the ordinary runtime; a
  general OS sandbox for subprocess/network authority; new user
  capability; changes to dictation's commit semantics; changing the
  owner's Phase 107 N10-N12 computation ruling.

## Exit criteria

- [x] `TextTyper` contains no raw keyboard, clipboard, Accessibility,
      or AppleScript primitive and refuses a direct unwarranted call.
- [x] The spawned child validates exact, payload-bound, expiring,
      one-use warrants and focus immediately before the raw act.
- [x] A real marker lands in a real TextEdit window through that child
      and produces matching native and kernel success receipts.
- [x] Every production call to `coder_steering.deliver` and
      `deliver_keys` originates in the claimed `process.input@1`
      executor; both text and keys have terminal-receipt tests.
- [x] GitHub/Jira/mission-control reads have no ambient owner default
      and refuse an unauthenticated principal before subprocess.
- [x] Unclaimed and claimed-silent operations terminalize generically;
      the built-bundle Playwright live-bus proof is mandatory in CI.
- [x] The zero-row debt register, fence, SECURITY, kernel RFC, and
      Constitution agree; clause 6's automatic sunset is recorded.
- [x] HS-108-07 machine half: all eight assembled beats pass in one
      session, including complete Python/web sweeps and real desktop metal.
- [x] HS-108-07 owner half: the live sitting/verdict is recorded verbatim.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-108-01 | The warrant room - a real executor boundary | done | [story-01-warrant-executor](./story-01-warrant-executor.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-108-02 | Confine the desktop primitives | done | [story-02-confine-desktop](./story-02-confine-desktop.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-108-03 | Terminal input has one door | done | [story-03-universal-terminal-input](./story-03-universal-terminal-input.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-108-04 | Reads arrive with a principal | done | [story-04-mandatory-read-principals](./story-04-mandatory-read-principals.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-108-05 | Silence ends, and CI watches | done | [story-05-liveness-and-live-bus](./story-05-liveness-and-live-bus.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-108-06 | Empty means empty | done | [story-06-empty-register-and-docs](./story-06-empty-register-and-docs.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-108-07 | Closeout - open the locked room | done | [story-07-closeout](./story-07-closeout.md) | [evidence-story-07](./evidence-story-07.md) |

## Sequencing

01 defines the warrant protocol and child boundary. 02 moves the raw
desktop driver through it and deletes the dormant helper. 03 and 04
close the five audited side doors independently. 05 lands the two
operational carryovers. 06 empties the register only after every
closing proof exists. 07 runs the one-command beats and the owner
sitting.

## Active risks

| Risk | Mitigation | Stop signal |
|---|---|---|
| Calling import discipline “confinement” | Independent child validation, anonymous IPC, and precise SECURITY wording; untrusted execution remains prohibited | A doc calls HoldSpeak a general Python sandbox |
| Forged or swapped payload reaches keyboard | Exact shape + HMAC + payload/target/placement binding inside child; negative tests | Raw driver factory invoked by any negative case |
| Focus changes between approval and typing | Focus generation re-read inside child; refusal spends warrant | Parent-only focus check |
| Executor disappears after acting | Signed execution deadline; claimed silence becomes indeterminate; never retry | Work becomes retryable after claim |
| Fence turns green by forgetting history | 21 migrated/read/exempt/confined statements pinned separately from zero-row debt ledger | A known statement disappears without a failing test |

## Decisions made

- 2026-07-29 - Candidate Y's post-ruling count is 15 debt, not its
  original 18-site headline; Phase 108 closes exactly T01/T02,
  C02/C03/C05, and A01-A10 - inherited from the Phase 107 owner
  sitting and machine register.
- 2026-07-29 - Desktop raw effects use an anonymous
  `multiprocessing` pipe and a spawned child. No filesystem socket,
  discoverable port, or caller-supplied authority surface is added -
  implementation.
- 2026-07-29 - One-use is consumed before the focus check or raw
  driver call. A focus refusal cannot be replayed after the user moves
  back to the old window - implementation.
- 2026-07-29 - Claim and execution deadlines are distinct and both
  signed. Never-claimed is a known refusal; claimed silence is
  indeterminate - Article VI / two-sided-ledger rule.
- 2026-07-29 - The clause-6 sunset is recorded as execution of the
  already owner-ratified clause, not a new constitutional amendment -
  Article X / XI.
- 2026-07-30 - The adversarial closeout re-audit found that a timed-out
  executor could accept a later operation while its old response was still
  pending. Broken state now permanently closes that endpoint; a regression
  proves no later message is sent - implementation.
- 2026-07-30 - The owner accepted the delivered phase after the corrected
  8/8 sitting: "'s all's good, moyt." - Article IX.4.

## Where we are

**CLOSED 7/7.** The exact closeout command passes **8/8 machine beats in
one session**. Its real TextEdit act landed once through the child with
both receipts succeeded (`op_b73ba81d0fdc41c98a0ed092d4c74681`);
the mandatory live-bus run passed 3/3; the complete broad sweep passed
4,382 Python tests (37 expected optional/platform skips, no deselection)
and 373 web tests plus typecheck/build. The owner's verdict is recorded
verbatim in [evidence-story-07](./evidence-story-07.md); see the
[final summary](./final-summary.md).
