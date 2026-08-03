# Evidence - HS-115-06

- **Story:** HS-115-06 - The rails window
- **Status:** done
- **Date:** 2026-08-03

## Proof

### Captured run — 2026-08-03T23:46:01Z

- **Command:** `npx vitest run`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 0ee9da2480a778b7b618fbd9ac6fa72289a17c26

```text

 RUN  v4.1.10 /Users/karol/dev/tools/HoldSpeak

 ❯ .claude/worktrees/agent-aa0b20489ad20af48/web/src/runtime/RuntimeBus.test.tsx (1 test | 1 failed) 12ms
     × owns one socket and removes it with the provider 11ms
 ❯ .claude/worktrees/agent-a912768e6305fc3dc/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 21ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a3a3e870a12496cea/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 23ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a9e46b0f4a53a0b97/web/src/desk/surface/__tests__/stream.test.tsx (4 tests | 1 failed) 18ms
     × head leads with the count at display step; entries carry when/said/meta/verbs 2ms
 ❯ .claude/worktrees/agent-ace7e51320a364b7d/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 20ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a63ec577c1e3341a3/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 25ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 2ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a55cc05af5578a9dd/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 33ms
     × exposes no setter for status, target, policy, grant, or attempt state 6ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a448123bea1af8070/web/src/lib/__tests__/micSession.test.ts (13 tests | 13 failed) 14ms
     × asks for the microphone ONCE across many utterances 6ms
     × suspends between utterances instead of tearing the device down 1ms
     × runs on an AudioWorklet, never the deprecated ScriptProcessor 0ms
     × refuses where AudioWorklet is absent — no deprecated fallback 1ms
     × closing stops the tracks for real — CLOSED is not muted 0ms
     × releases the device when the pause outlasts the idle window 1ms
     × reports the capture level from the one frame path 0ms
     × segments continuous audio into utterances with no key touched 0ms
     × a hold takes the floor: the open mic captures nothing while held 1ms
     × a cancelled hold hands the floor back without dropping the grant 0ms
     × one verb drops the stream entirely 0ms
     × dropping the open mic mid-hold keeps the hold's own capture 0ms
     × refuses honestly when the browser withholds the microphone 2ms
 ❯ .claude/worktrees/agent-a297a81f50e1dac2b/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 21ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 0ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-aa19073b8b482c481/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 19ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 1ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a448123bea1af8070/web/src/desk/surface/__tests__/stream.test.tsx (4 tests | 1 failed) 17ms
     × head leads with the count at display step; entries carry when/said/meta/verbs 2ms
 ❯ .claude/worktrees/agent-a5f9c1331117b619e/web/src/desk/surface/__tests__/stream.test.tsx (4 tests | 1 failed) 17ms
     × head leads with the count at display step; entries carry when/said/meta/verbs 2ms
 ❯ .claude/worktrees/agent-aa0b20489ad20af48/web/src/desk/surface/__tests__/stream.test.tsx (4 tests | 1 failed) 23ms
     × head leads with the count at display step; entries carry when/said/meta/verbs 3ms
 ❯ .claude/worktrees/agent-a48a6c7e3915d09e6/web/src/desk/surface/gadgets.test.tsx (16 tests | 16 failed) 10ms
     × CheckGadget is a real checkbox 4ms
     × CycleGadget is a real select and keeps an off-roster value visible 1ms
     × StepperGadget arrows step and clamp 0ms
     × MxRadio reveals only the selected option's gadgets 0ms
     × SecretRow shows the chip, arms an in-row replace, Enter commits 0ms
     × SecretRow Escape reverts the armed replace without committing 0ms
     × GadgetRow carries the label and a token fact 0ms
     × LedMeter is a labeled meter: lit segments follow the value, hot above 0.8 0ms
     × LedMeter scanning posture reads as scanning, not a level 0ms
     × LampGadget is never color-only: the axis label rides with the lamp 0ms
     × TransportKey: held = pressed (inverted video is the CSS contract) 0ms
     × GadgetTable verbs slot renders per-row verbs in place of the bare × 0ms
     × GadgetTable default delete ARMS: × → DELETE? → gone 1ms
     × the armed face self-disarms after 3s (a late press only re-arms) 0ms
     × PadGadget is a real textarea 0ms
     × FoldGadget keeps details semantics and carries the token slot 0ms
 ❯ .claude/worktrees/agent-a48a6c7e3915d09e6/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 20ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 0ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-a0160236356b756a8/web/src/lib/__tests__/micSession.test.ts (13 tests | 13 failed) 11ms
     × asks for the microphone ONCE across many utterances 4ms
     × suspends between utterances instead of tearing the device down 1ms
     × runs on an AudioWorklet, never the deprecated ScriptProcessor 0ms
     × refuses where AudioWorklet is absent — no deprecated fallback 1ms
     × closing stops the tracks for real — CLOSED is not muted 0ms
     × releases the device when the pause outlasts the idle window 1ms
     × reports the capture level from the one frame path 0ms
     × segments continuous audio into utterances with no key touched 0ms
     × a hold takes the floor: the open mic captures nothing while held 1ms
     × a cancelled hold hands the floor back without dropping the grant 0ms
     × one verb drops the stream entirely 0ms
     × dropping the open mic mid-hold keeps the hold's own capture 0ms
     × refuses honestly when the browser withholds the microphone 2ms
 ❯ .claude/worktrees/agent-ace7e51320a364b7d/web/src/desk/surface/__tests__/stream.test.tsx (4 tests | 1 failed) 17ms
     × head leads with the count at display step; entries carry when/said/meta/verbs 2ms
 ❯ .claude/worktrees/agent-a64d33e0ee274a344/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 22ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a578ae0294a20dc2e/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 21ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 1ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-ace7e51320a364b7d/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 20ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 0ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-a0160236356b756a8/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 21ms
     × exposes no setter for status, target, policy, grant, or attempt state 3ms
     × refresh derives every field from the server snapshot, not any argument 1ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ web/src/desk/surface/gadgets.test.tsx (16 tests | 16 failed) 10ms
     × CheckGadget is a real checkbox 4ms
     × CycleGadget is a real select and keeps an off-roster value visible 1ms
     × StepperGadget arrows step and clamp 0ms
     × MxRadio reveals only the selected option's gadgets 0ms
     × SecretRow shows the chip, arms an in-row replace, Enter commits 0ms
     × SecretRow Escape reverts the armed replace without committing 0ms
     × GadgetRow carries the label and a token fact 0ms
     × LedMeter is a labeled meter: lit segments follow the value, hot above 0.8 0ms
     × LedMeter scanning posture reads as scanning, not a level 0ms
     × LampGadget is never color-only: the axis label rides with the lamp 0ms
     × TransportKey: held = pressed (inverted video is the CSS contract) 0ms
     × GadgetTable verbs slot renders per-row verbs in place of the bare × 0ms
     × GadgetTable default delete ARMS: × → DELETE? → gone 1ms
     × the armed face self-disarms after 3s (a late press only re-arms) 0ms
     × PadGadget is a real textarea 0ms
     × FoldGadget keeps details semantics and carries the token slot 0ms
 ❯ .claude/worktrees/agent-a2d29ca16535a1a8f/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 19ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a55cc05af5578a9dd/web/src/lib/durableDraft.test.tsx (2 tests | 2 failed) 3ms
     × writes synchronously and restores after a remount 2ms
     × clears only the persisted copy while retaining the live editor value 0ms
 ❯ .claude/worktrees/agent-a5e3a987f4d1e8805/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 20ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 1ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-a8cba81cd3029ac82/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 24ms
     × exposes no setter for status, target, policy, grant, or attempt state 4ms
     × refresh derives every field from the server snapshot, not any argument 1ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 1ms
 ❯ .claude/worktrees/agent-a0160236356b756a8/web/src/desk/surface/__tests__/stream.test.tsx (4 tests | 1 failed) 20ms
     × head leads with the count at display step; entries carry when/said/meta/verbs 2ms
 ❯ .claude/worktrees/agent-a3a3e870a12496cea/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 21ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 1ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-aa0b20489ad20af48/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 21ms
     × exposes no setter for status, target, policy, grant, or attempt state 4ms
     × refresh derives every field from the server snapshot, not any argument 1ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a48a6c7e3915d09e6/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 27ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 25ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a297a81f50e1dac2b/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 20ms
     × exposes no setter for status, target, policy, grant, or attempt state 3ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a5f9c1331117b619e/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 20ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 1ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-a0160236356b756a8/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 20ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 1ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-a6e82786f8899031f/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 18ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a64d33e0ee274a344/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 23ms
     × loading is a status, error an alert with retry, empty a quiet label 3ms
     × a row carries title, detail, meta, and a verb slot 1ms
     × onOpen makes the row body one press target 1ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-aeb023a4f3a91aa8b/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 22ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 1ms
     × onOpen makes the row body one press target 1ms
     × MetricStrip omits empty figures (never zero-theater) 1ms
     × SurfaceFacts de-snakes keys and omits meaningless values 1ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-a448123bea1af8070/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 23ms
     × exposes no setter for status, target, policy, grant, or attempt state 3ms
     × refresh derives every field from the server snapshot, not any argument 2ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-aeb023a4f3a91aa8b/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 22ms
     × exposes no setter for status, target, policy, grant, or attempt state 3ms
     × refresh derives every field from the server snapshot, not any argument 1ms
   
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```
