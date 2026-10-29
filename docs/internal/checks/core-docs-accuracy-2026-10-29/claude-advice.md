# Extended documentation advisory

UNCHECKED — awaiting Muad'Dib. These are read-only `claude -p` responses invoked by Astra, not Muad'Dib's check. The current fast cycle places the separate review after merge.

The first advisory found three material defects in the source-audit draft. Root checked each finding against the actual production call sites and corrected the guides. A bounded re-check confirmed the corrected seam and found no remaining material error in it. The second pass is not a whole-documentation accuracy certification.

The source still has a stale private helper docstring at `holdspeak/web/routes/actuator_shared.py:168` that lists the meeting decision route as an execution caller. Actual service code does not execute there. This product-source comment was left unchanged and is recorded for follow-up.

## First advisory

```text
I made no edits and ran no tests or live calls. I checked the source myself rather than trusting the audit JSONs, and found three material defects.

**Findings, most serious first**

1. **The meeting decision route never sends anything** (`docs/ACTUATOR_DEVELOPMENT.md:193-196`). The doc says the route "can also call the executor", and that nothing is sent unless the actuator is registered and its capability is on.
   - Source: `holdspeak/web/routes/meetings/aftercare.py:49` calls `MeetingAftercareService.decide_proposal` (`holdspeak/services/meeting_aftercare_service.py:106-135`).
   - That method checks the policy, calls `transition_proposal` and emits a result only on rejection. It never builds an `ActuatorExecutor` or touches `PluginHost` capabilities.
   - Fix: "This route records the decision and the policy snapshot. It does not execute. Execution happens only through the Desk actuator routes (`/api/desk/actuators/{webhook,github,slack}/{id}/decision`) and Mission Control." Then check that the sequence diagram does not show a meeting approval going out.

2. **The `meeting.allow_actuators` / `allowed_actuators` keys are shown as governance, but nothing enforces them** (`docs/ACTUATOR_DEVELOPMENT.md:125-134`, "A project can narrow its meeting policy").
   - The only runtime read is `holdspeak/setup_status.py:223`, a status flag.
   - Every executor built in production passes a literal `allow_actuators=True` and no `allowed_actuator_ids`: `holdspeak/web/routes/actuator_shared.py:263` and `:291`, and `holdspeak/services/mission_control_service.py:221`. The `meeting_plugins.py` hosts pass `allow_actuators=False` no matter what the config says.
   - So setting `allow_actuators: false` or narrowing the list changes no execution path. An owner who follows the doc gets no protection they can see.
   - Fix: say that both keys are validated and shown in setup status, but no executor reads them today. Execution is gated by the stored proposal binding, the operation policy and the per-route destination checks. Drop "can narrow".

3. **The Calls adapter auto-selection is stated too loosely** (`docs/calls.md:22-25`). Per `holdspeak/calls/service.py:80-98`:
   - `HOLDSPEAK_LINE=off` forces ai-phone or none, whatever the setting says.
   - A non-empty ai-phone command environment variable (`COMMAND_ENV`) beats auto-detection.
   - The Line is picked when `find_baresip()` succeeds or `calls.line.where` starts with `node:`. That is a configured node, not an enrolled or reachable one.

   The doc's "enrolled node is available" overstates it, and someone fixing a "why is it using the Line?" problem would be misled. Fix: state those three rules.

**Checked and found accurate**
- **iPad** (`docs/IPAD.md:32-35`): `VoiceNoteComposer.send()` (`apple/Sources/RuntimeCore/Companion/VoiceNoteComposer.swift:112`) calls `sendRemoteDictation(text:)`. The protocol extension (`Providers.swift:176`) and `HTTPDesktopClient.swift:180-182` pass `deliveryID: nil`. The overload at `:187-199` sends `delivery_id` only when a value is given, and the composer has no retry. The new text is correct.
- **Core inference vs Line speech** (`docs/SYSTEM_ARCHITECTURE.md:82`): `holdspeak/line/speech.py` uses Parakeet (onnx-asr) and Pocket directly, with no assignment or receipt import, and audio stays off the hub wire. Correct.
- **"Your numbers"**: matches `web/src/desk/calls/CallsSettings.tsx:323`.
- **The Slack refusal** (`slack_moved_to_channel`) on the export and approve paths is confirmed.
- **Plugin host** (`docs/PLUGIN_AUTHORING.md`): `PluginHost` defaults to `allow_actuators=False` (`host.py:146`), and a missing version is recorded as `"unknown"` (`host.py:468`). Correct.
- **Generators**: `gen_api_surface.py` imports `holdspeak` lazily inside functions (`:52-53`), after the `sys.path.insert(0, REPO)`. `scripts/` has no `__init__.py`, so it is a namespace package and the first entry on `sys.path` wins. Hatchling editable installs use a `.pth` path entry, which an insert at position 0 also beats. The fix and the probe test are sound. One gap: the test covers only `PYTHONPATH`, not a meta-path editable finder. That is low risk with Hatchling.

**Not verified**
- I did not check the idempotency key composition (`repo|title|text`, webhook body without the URL) in the desk actuator service.
- I did not check that the web runtime enables only `llm` (`web_runtime.py:264`); I saw the constructor but not its arguments.
- I did not check the retention or day-count claims in the memory and pipeline guides.
- I did not check `meeting.disabled_plugins` being applied by the dispatcher and not the host.
- I did not check the route count of 877.
```

## Bounded re-check

```text
I re-checked only the corrected seam, and every claimed correction matches the source. I found no remaining material error.

1. **Meeting decision route doesn't execute: true.** `POST /api/meetings/{id}/proposals/{pid}/decision` (`holdspeak/web/routes/meetings/aftercare.py:49`) calls `MeetingAftercareService.decide_proposal`. That method only calls `transition_proposal` (`holdspeak/services/meeting_aftercare_service.py:131`) and runs no executor. This supports `docs/INTEGRATIONS.md:78` and `docs/ACTUATOR_DEVELOPMENT.md:201-203`. One stale comment remains in the source, not the docs: the `actuator_shared.py:168` docstring still lists the meeting route among the four routes that share the execute lifecycle. It doesn't, so a reader could be misled.

2. **`meeting.allow_actuators` / `allowed_actuators` not enforced: true.** The defaults are `True` and `["*"]` (`holdspeak/config/meeting.py:124-125`), and the config only validates them (`:225-239`). The production executors at `actuator_shared.py:263` and `:291` and `mission_control_service.py:221` hard-code `allow_actuators=True` and pass no `allowed_actuator_ids`. This supports `ACTUATOR_DEVELOPMENT.md:127-130` and `MEETING_MODE_GUIDE.md:251`. The only other code that reads the setting is `setup_status.py:223`, for a display flag.

3. **Optional kernel receipts: true.** The Desk webhook and GitHub executors pass `operation_broker` from `_kernel_executor_binding`, which can be `None`. Mission Control passes no broker at all, so it is a bare executor. `ACTUATOR_DEVELOPMENT.md:113-114` and `:214` are right.

4. **Slack refusals: true.** Source raises `slack_moved_to_channel` at `actuator_service.py:94` and `:106`, `meeting_aftercare_service.py:114` and `aftercare.py:59`. The routes are at `desk_actuators.py:45`.

5. **Calls adapter order: true.** `pick_adapter` (`holdspeak/calls/service.py:80-98`) checks, in order:
   - `line_on()` off → ai-phone if detected, otherwise none
   - an explicit `line` or `ai-phone` choice
   - a non-empty `COMMAND_ENV` (`HOLDSPEAK_AI_PHONE`)
   - `find_baresip()` or `where` starting with `node:`
   - otherwise ai-phone if detected, or none

   `docs/calls.md:25-31` matches this, including the note that `node:` is not proof of readiness.

Two small points are not material errors:
- `line_on()` (`holdspeak/line/__init__.py:20`) also accepts `0`, `false` and `no`, not just `off`.
- An explicit **ai-phone** choice wins even when no ai-phone is detected. In that case `default_phone()` returns `None` (`service.py:119-121`). The docs say "an explicit choice wins", which is accurate but doesn't spell out this case.

I made no edits and ran no tests.
```
