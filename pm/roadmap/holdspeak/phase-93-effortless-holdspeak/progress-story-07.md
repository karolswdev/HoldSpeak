# HS-93-07 progress record — Secure, Normal, or YOLO

**Captured:** 2026-07-11<br>
**Baseline:** `main` at `6a93e494` (merged HS-93-06 recovery slices)<br>
**After build:** current `agent/hs-93-07-secure-normal-yolo` working tree; no
commit identity claimed<br>
**Acceptance status:** in progress — one configured-Integration policy slice is
implemented across Hub, React, and flagship Swift. The complete operation-family
matrix, owner walks, and physical-device evidence remain open.

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

## Verification completed for this slice

| Lane | Result |
|---|---|
| Full Python unit suite | 2,899 passed |
| Configured Slack/Webhook/GitHub plus Meeting Slack Integration routes | 65 passed |
| Full Web architecture, type, component, and production-build check | 113 sources; 31 files / 162 tests passed; typecheck and build passed |
| Full flagship Swift package | 545 passed, 9 skipped, 0 failed |
| Product-copy and API-surface guards | 12 passed; 3,939 census candidates, 0 violations |
| Docs and backend/frontend density guards | 28 passed |
| Python lint, whitespace, and roadmap validation | clean |

The PMO commit gate is run against the final staged tree before this slice is
committed.

## Acceptance still required

No HS-93-07 acceptance checkbox changes in this slice. Still required:

- complete central coverage for dictation delivery, inference, Coder
  steering/factory operations, Mission Control/workflows, sync, cadence, and
  destructive Desk mutations;
- zero-prompt YOLO execution for every eligible registered operation, including
  Coder session authority without weakening pane identity or key/payload checks;
- Secure/Normal bounded grant issue/use/revoke presentation and source-linked
  use Receipts;
- shared Qlippy, Mission Control, Coder, Cadence, History, Desk, and native Queue
  treatment with no consequential fallback verb;
- control/treatment production walks, exact prompt counts, owner prediction and
  Receipt-findability verdicts;
- physical Web/iPhone/iPad evidence with exact build, device, destination, and
  operation provenance.

The next autonomous development slice should carry registered Coder steering
through policy v2: YOLO must require no HoldSpeak arm prompt while pane identity,
registered capability, changed-target refusal, bounded execution, and the
source-linked Receipt remain mandatory. Secure and Normal keep their deliberate,
bounded authority paths.
