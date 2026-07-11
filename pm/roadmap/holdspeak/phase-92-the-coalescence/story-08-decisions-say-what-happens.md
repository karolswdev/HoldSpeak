# HS-92-08 — Decisions say what happens next

- **Project:** holdspeak
- **Phase:** 92
- **Status:** backlog
- **Depends on:** HS-92-02, HS-92-07
- **Unblocks:** HS-92-09, HS-92-10
- **Owner:** unassigned

## Problem

Review, accept, approve, apply, arm, and run currently encode different human
decisions, but generic buttons and combined proposal states hide the difference.
Some routes send on approval, some only mark approved, and some remain blocked by
another gate. Repeated prompts can be reduced only after exact consequence,
destination, and invariant enforcement are uniform.

## Scope

- **In:** Typed OperationDescriptor/effect classes and central policy result;
  separate ReviewDecision, AuthorizationState, and ExecutionState; exact
  commitment verbs; scoped destination/data/project/time/count grants;
  `ControlMode=safe|neutral|yolo` presets applied first to dictation preview,
  steering TTL, fixed-destination Slack/webhook/GitHub writes, and sync cadence;
  receipts/reason codes; Web/Swift/CLI controls.
- **Out:** Mode branches scattered through features; automatic arbitrary shell
  commands; grants to newly discovered destinations; eliminating content review
  or hard invariants.
- **Paths:** `holdspeak/plugins/actuators.py`,
  `holdspeak/plugins/actuator_executor.py`, `holdspeak/db/actuators.py`,
  `holdspeak/coder_steering.py`, `holdspeak/cadence/`,
  `holdspeak/web/routes/meetings/aftercare.py`,
  `holdspeak/web/routes/desk_actuators.py`,
  `holdspeak/web/routes/system/coder_steering_routes.py`,
  `web/src/pages/HistoryPage.tsx`, Desk proposal/session components,
  `apple/App/MeetingCapture/DeskDioramaStage.swift`, CLI/config entry points,
  and policy/authority/UAT tests.

## Acceptance criteria

- [ ] Review acceptance changes content state only; approving an EffectRequest
      changes authority only; execution attempts and outcomes have separate
      state and are queryable without interpreting one overloaded `status`.
- [ ] Buttons state commitment and destination, for example `Approve and send to
      Slack`, `Approve for desktop executor`, `Run shell command`, or `Arm pane
      %7 for 15 minutes`; generic verbs remain only where no consequence is
      ambiguous.
- [ ] Safe, Neutral, and YOLO resolve typed policy once, show source/precedence,
      affect future operations only, and snapshot the decision on each run.
- [ ] Every mode passes identical authentication, secret, destination, payload,
      pane-identity, audit/receipt, configuration-integrity, and schema-safety
      invariant tests.
- [ ] A Grant binds actor, operation/effect, destination, data class, project or
      resource scope, TTL/count, issue/revoke times; every use is visible and
      revocable, and identity/config changes revoke incompatible grants.
- [ ] Safe/Neutral/YOLO behavior is implemented and explained for the four
      initial operation families in Scope; unsupported operation families
      remain current behavior rather than inheriting a permissive default.
- [ ] Approval cards appear on their source Desk subject and state whether the
      decision executes now, queues an executor, or remains blocked/unavailable.

## Test plan

- **Unit:** Policy matrix across modes/effect/destination/initiator/grant states;
  `uv run pytest -q tests/unit/test_actuator_executor.py tests/unit/test_coder_steering_grants.py tests/unit/test_dictation_preview.py tests/unit/test_cadence_next_action.py tests/unit/test_slack_export.py`.
- **Integration:** Meeting, Desk actuator, steering, sync, settings, and Qlippy
  route tests; UAT `pack-g-connectors/01-04`, `pack-b-steering/05-07`,
  `pack-a-aftercare/04`, and proposal review scenarios, rewritten from registry
  reason codes.
- **Manual / device:** Switch stricter/permissive modes on Web and Swift; inspect
  widened dimensions, grant/revoke a fixed Slack batch and Coder session, change
  destination/payload/pane, and prove refusal plus receipt in every mode.

## Notes / open questions

The wire values stay `safe`, `neutral`, and `yolo`. HS-92-10 owner evidence
decides whether YOLO is the final visible label or an expert alias. It never
means bypassing invariants.
