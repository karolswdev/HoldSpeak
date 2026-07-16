# HS-93-07 progress record — Secure, Normal, or YOLO

**Captured:** 2026-07-11<br>
**Baseline:** `main` at `6a93e494` (merged HS-93-06 recovery slices)<br>
**After build:** current `agent/hs-93-07-secure-normal-yolo` working tree; no
commit identity claimed<br>
**Acceptance status:** in progress — configured-Integration and registered
Coder-steering policy slices are implemented across Hub, React, and flagship
Swift. The complete operation-family matrix, owner walks, and physical-device
evidence remain open.

## First vertical slice: configured Integration authority is the posture

The Phase-92 resolver had two behaviors that contradicted the Phase-93 product
contract: YOLO required a reusable external-write grant before a configured
destination could run, and an unknown family inherited `current_behavior`.
Policy was also re-resolved when the owner approved, so changing the setting
could silently alter an already-visible proposal.

This slice makes one bounded path truthful:

1. `operation-policy/v2` snapshots mode, source, effect, destination,
   consequence, eligibility, reason, authority basis, and next state when the
   proposal is first recorded. An idempotent repeat returns the original
   snapshot unchanged.
2. Secure and Normal keep exact per-action decisions. A matching bounded grant
   may authorize them; grants are no longer a YOLO prerequisite.
3. YOLO immediately authorizes only a fixed configured Slack, Webhook, or
   GitHub destination. The posture is recorded as the authority basis and the
   existing executor still verifies the durable payload, destination, preview,
   effect, configuration, and audit binding immediately before egress.
4. The effect produces the same executed/failed actuator record and a
   source-linked Desk Receipt. Repeating an idempotency key never repeats an
   executed effect.
5. An unregistered destination or unknown operation family resolves to a named
   refusal. It does not enter the Web or native pending-approval queue, and a
   forged decision call cannot widen it.
6. Changing posture revokes active grants but does not alter existing proposal
   snapshots. A Normal proposal remains Normal and still requires its original
   decision after the global posture becomes YOLO.

No new registry, receipt store, side-effect path, or client-specific policy
matrix was added.

## Second vertical slice: registered Coder steering uses the posture

The existing steering path already had the right hard boundary—one text
chokepoint, one allowed-key chokepoint, canonical tmux pane identity, and an
audit—but every posture still required an arm grant. This slice carries that
path through operation-policy v2 without turning YOLO into general shell
authority:

1. Peek names the exact pane, operation, policy decision, commitment, authority
   basis, and Receipt promise. Secure and Normal continue to require their
   bounded exact-pane grant. Eligible YOLO text and allowed-key delivery uses
   the registered pane and Control posture directly, with no HoldSpeak arm
   prompt or synthetic grant.
2. The client sends the pane identity from its read-side snapshot. Immediately
   before text or keys reach tmux, the hub re-resolves the registry target and
   sends only to the verified canonical `%N`. A missing, malformed, gone,
   recycled, or changed pane refuses before one keystroke.
3. YOLO does not widen the terminal payload. Text still uses the literal text
   transport and named keys still pass the existing allow-list. The Desk keeps
   rename/kill in a separate deliberate control window while their full policy
   classification remains open. An exact `pane:%N` attachment is eligible; an
   unresolved destination is not.
4. The machine that types owns policy and audit. The relay forwards the
   expected identity, but a configured far node resolves its own posture or
   grant, re-verifies its own pane, executes locally, and records the result.
5. Every attempt records the operation and immutable policy snapshot in the
   existing steering audit and projects a source-linked Coder Receipt with
   destination, authority, posture, effect, and outcome. Coder frames refresh
   Desk memory after both delivery and refusal.
6. A posture change clears in-memory Coder grants through both Web and CLI
   control paths. Grant matching also refuses a grant minted under another
   posture, so a stale authority object cannot silently widen a later attempt.

No alternate transport, client-side policy resolver, durable shell capability,
or second Receipt store was added.

## Shared client expression

- Web Settings names Control posture, its shared policy version, future-only
  effect, retained proposal snapshots, and any grant revocation.
- The Desk Integration action point names practical posture before the action,
  then renders the exact effect, normalized destination, authority basis, and
  next state returned by the Hub. A YOLO response goes directly to its Receipt;
  it never renders an approval button.
- Meeting History consumes the same proposal policy and does not offer an
  approval action for a refused operation.
- Desk Receipt details include control posture, policy version, effect,
  destination, authority basis, reason, outcome, and source.
- Flagship Swift decodes the same policy snapshot in Queue and the same Receipt
  fields in Desk memory. Its authority client now correctly uses the shared
  snake-case decoder rather than conflicting explicit coding keys.
- Web and flagship Swift Coder pull-outs consume the Hub's pane, operation,
  policy, and commitment. Both show direct YOLO steering without an arm control,
  keep Secure/Normal arm and revoke behavior, and show the exact authority and
  Receipt fate beside the action.
- Both Desk clients keep session rename/kill in a separate explicit control
  window; this slice does not grant those factory operations posture authority.
  A changed-target refusal clears the local binding and requires a fresh peek;
  clients cannot infer posture eligibility from their own settings.

## Verification completed for this slice

| Lane | Result |
|---|---|
| Canonical Python suite (`test_metal.py` excluded per repo contract) | 3,802 passed, 37 skipped; 2 non-failing transcript-import teardown warnings recorded |
| Full Python unit suite on the final tree | 2,911 passed |
| Coder policy, identity, key, route, audit, projection, migration, and mode-revocation lane | 108 passed |
| Configured Slack/Webhook/GitHub plus Meeting Slack Integration routes | 65 passed |
| Full Web architecture, type, component, and production-build check | 113 sources; 31 files / 166 tests passed; typecheck and build passed |
| Full flagship Swift package | 545 passed, 9 skipped, 0 failed |
| Generated flagship iOS app | Debug iPhoneSimulator build succeeded with code signing disabled |
| Mobile steering contract fixtures | JSON Schema validator passed |
| Product-copy, language, docs-drift, API-surface, and density guards | 45 passed; controlled census has 0 violations |
| Python lint, whitespace, and roadmap validation | clean |

The PMO commit gate is run against the final staged tree before this slice is
committed.

## Acceptance still required

No HS-93-07 acceptance checkbox changes in this slice. Still required:

- complete central coverage for dictation delivery, inference, Coder
  factory/destructive operations, Mission Control/workflows, sync, cadence, and
  destructive Desk mutations;
- zero-prompt YOLO execution for the eligible operation families still outside
  the two implemented slices;
- Secure/Normal bounded grant issue/use/revoke presentation and source-linked
  use Receipts;
- shared Qlippy, Mission Control, Cadence, History, Desk, and native Queue
  treatment with no consequential fallback verb, plus production/device proof
  for the implemented Coder treatment;
- control/treatment production walks, exact prompt counts, owner prediction and
  Receipt-findability verdicts;
- physical Web/iPhone/iPad evidence with exact build, device, destination, and
  operation provenance.

The next autonomous development slice should classify Coder factory and
destructive operations through policy v2. Spawn's optional command, rename, and
kill have materially different consequences; each must state its exact effect
and destination, preserve name/argument and pane-identity invariants, and avoid
inheriting text-steering posture authority by accident.

## Closure — 2026-07-15 (owner-rescoped)

The owner directed that HS-93-07 close at the two delivered authority families
so the phase can proceed to the cross-client UI consistency remediation. The
acceptance section of the story file was rescoped accordingly; everything in
"Acceptance still required" above moved verbatim to BACKLOG candidate X and is
not claimed by this closure. The phase exit criterion "every control mode
passes the invariant matrix" still gates the phase close.

Fresh verification lanes were captured at close through
`dw evidence capture` into [evidence-story-07](./evidence-story-07.md):

- Canonical Python suite (`uv run pytest -q --ignore=tests/e2e/test_metal.py`):
  3,798 passed, 42 skipped (documented opt-in e2e, missing local models, and
  unreachable LAN endpoints), exit 0.
- Full Web gate (`npm --prefix web run check`): architecture guard, typecheck,
  vitest, and production build, exit 0.
- Full flagship Swift package (`swift test --package-path apple`): exit 0
  (output truncated by the capture byte cap; the exit code is
  machine-recorded).

One verification-rail repair ships with this close (phase scope:
"verification-rail repairs required to make the product and UAT suites
bounded, repeatable, and honest"). The Swift lane hung indefinitely twice:
`MeetingCaptureTests.testReopenSurvivesAFreshViewModel` drives
`MeetingCapture.stop()` → `MeetingAudioJournal.finalize()`, which deletes
files under the user's real `~/Documents/meeting-audio/`; on a Mac with cloud-
synced Documents the `unlink` blocks in the kernel on the file provider and
the suite never finishes. `MeetingAudioStore` now exposes
`baseDirectoryOverride`, and `MeetingCaptureTests`/`SlidingWindowTests` point
it at a per-run temp directory, so the suite is bounded and never touches the
operator's synced folders. Product behavior is unchanged (the override is nil
outside tests).
