# Evidence - HS-115-05

- **Story:** HS-115-05 - Hosted cores
- **Status:** done
- **Date:** 2026-08-03

## Proof

### Captured run — 2026-08-03T23:44:34Z

- **Command:** `npx vitest run`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 0ee9da2480a778b7b618fbd9ac6fa72289a17c26

```text

 RUN  v4.1.10 /Users/karol/dev/tools/HoldSpeak

 ❯ .claude/worktrees/agent-af90eea2d5bfb90ad/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 20ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a0160236356b756a8/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 33ms
     × exposes no setter for status, target, policy, grant, or attempt state 3ms
     × refresh derives every field from the server snapshot, not any argument 1ms
     × setFocusSource only touches the view preference and localStorage 1ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 1ms
 ❯ .claude/worktrees/agent-a880577fce625816c/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 25ms
     × exposes no setter for status, target, policy, grant, or attempt state 4ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a8cba81cd3029ac82/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 33ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a55cc05af5578a9dd/web/src/lib/durableDraft.test.tsx (2 tests | 2 failed) 33ms
     × writes synchronously and restores after a remount 17ms
     × clears only the persisted copy while retaining the live editor value 1ms
 ❯ .claude/worktrees/agent-a297a81f50e1dac2b/web/src/desk/surface/__tests__/stream.test.tsx (4 tests | 1 failed) 20ms
     × head leads with the count at display step; entries carry when/said/meta/verbs 2ms
 ❯ .claude/worktrees/agent-a880577fce625816c/web/src/desk/surface/__tests__/stream.test.tsx (4 tests | 1 failed) 17ms
     × head leads with the count at display step; entries carry when/said/meta/verbs 2ms
 ❯ .claude/worktrees/agent-a448123bea1af8070/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 28ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 7ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a63ec577c1e3341a3/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 21ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 0ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-aeb023a4f3a91aa8b/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 28ms
     × exposes no setter for status, target, policy, grant, or attempt state 5ms
     × refresh derives every field from the server snapshot, not any argument 1ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a0160236356b756a8/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 30ms
     × loading is a status, error an alert with retry, empty a quiet label 6ms
     × a row carries title, detail, meta, and a verb slot 1ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-a578ae0294a20dc2e/web/src/desk/surface/__tests__/stream.test.tsx (4 tests | 1 failed) 25ms
     × head leads with the count at display step; entries carry when/said/meta/verbs 2ms
 ❯ .claude/worktrees/agent-a48a6c7e3915d09e6/web/src/desk/surface/__tests__/stream.test.tsx (4 tests | 1 failed) 19ms
     × head leads with the count at display step; entries carry when/said/meta/verbs 2ms
 ❯ .claude/worktrees/agent-aeb023a4f3a91aa8b/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 34ms
     × loading is a status, error an alert with retry, empty a quiet label 8ms
     × a row carries title, detail, meta, and a verb slot 1ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-addf5256665a9e069/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 22ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 0ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-a578ae0294a20dc2e/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 39ms
     × loading is a status, error an alert with retry, empty a quiet label 7ms
     × a row carries title, detail, meta, and a verb slot 1ms
     × onOpen makes the row body one press target 1ms
     × MetricStrip omits empty figures (never zero-theater) 1ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 2ms
     × renders loops as surface rows with zero page grammar in the DOM 2ms
 ❯ .claude/worktrees/agent-a5f9c1331117b619e/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 30ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 3ms
     × onOpen makes the row body one press target 1ms
     × MetricStrip omits empty figures (never zero-theater) 1ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-a5f9c1331117b619e/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 19ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-addf5256665a9e069/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 24ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a48a6c7e3915d09e6/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 36ms
     × loading is a status, error an alert with retry, empty a quiet label 3ms
     × a row carries title, detail, meta, and a verb slot 1ms
     × onOpen makes the row body one press target 1ms
     × MetricStrip omits empty figures (never zero-theater) 1ms
     × SurfaceFacts de-snakes keys and omits meaningless values 1ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 3ms
     × renders loops as surface rows with zero page grammar in the DOM 1ms
 ❯ .claude/worktrees/agent-a2d29ca16535a1a8f/web/src/desk/surface/__tests__/stream.test.tsx (4 tests | 1 failed) 21ms
     × head leads with the count at display step; entries carry when/said/meta/verbs 2ms
 ❯ .claude/worktrees/agent-a55cc05af5578a9dd/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 40ms
     × exposes no setter for status, target, policy, grant, or attempt state 12ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-aa19073b8b482c481/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 27ms
     × loading is a status, error an alert with retry, empty a quiet label 4ms
     × a row carries title, detail, meta, and a verb slot 1ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 2ms
     × renders loops as surface rows with zero page grammar in the DOM 1ms
 ❯ .claude/worktrees/agent-af90eea2d5bfb90ad/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 21ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 0ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 1ms
 ❯ .claude/worktrees/agent-a9e46b0f4a53a0b97/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 24ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 0ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-a912768e6305fc3dc/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 22ms
     × loading is a status, error an alert with retry, empty a quiet label 3ms
     × a row carries title, detail, meta, and a verb slot 0ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-a3a3e870a12496cea/web/src/desk/surface/__tests__/stream.test.tsx (4 tests | 1 failed) 24ms
     × head leads with the count at display step; entries carry when/said/meta/verbs 3ms
 ❯ web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 32ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a448123bea1af8070/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 25ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 0ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 20ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 0ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-a3a3e870a12496cea/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 35ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 1ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 3ms
     × renders loops as surface rows with zero page grammar in the DOM 12ms
 ❯ .claude/worktrees/agent-a5e3a987f4d1e8805/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 35ms
     × loading is a status, error an alert with retry, empty a quiet label 6ms
     × a row carries title, detail, meta, and a verb slot 1ms
     × onOpen makes the row body one press target 1ms
     × MetricStrip omits empty figures (never zero-theater) 1ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 3ms
     × renders loops as surface rows with zero page grammar in the DOM 1ms
 ❯ .claude/worktrees/agent-a2d29ca16535a1a8f/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 33ms
     × exposes no setter for status, target, policy, grant, or attempt state 5ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a2d29ca16535a1a8f/web/src/pages/cores/__tests__/projectMemoryCore.test.tsx (8 tests | 6 failed) 17ms
     × wears every lifecycle and names a supersession successor 2ms
     × renders openable citation chips and derives the honest overflow count 2ms
     × renders the named comparison and lifecycle in the timeline 0ms
     × shows an honest empty timeline 0ms
     × shows an honest zero state after a project-scoped search 0ms
     × registers and restores the scoped Project Memory surface 0ms
 ❯ .claude/worktrees/agent-aa95e20ba9e8eac56/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 24ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 0ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-a578ae0294a20dc2e/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 23ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a9e46b0f4a53a0b97/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 27ms
     × exposes no setter for status, target, policy, grant, or attempt state 3ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a55cc05af5578a9dd/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 32ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 0ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 3ms
     × renders loops as surface rows with zero page grammar in the DOM 3ms
 ❯ .claude/worktrees/agent-a297a81f50e1dac2b/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 50ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 4ms
     × onOpen makes the row body one press target 9ms
     × MetricStrip omits empty figures (never zero-theater) 10ms
     × SurfaceFacts de-snakes keys and omits meaningless values 2ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 6ms
     × renders loops as surface rows with zero page grammar in the DOM 1ms
 ❯ web/src/desk/surface/__tests__/stream.test.tsx (4 tests | 1 failed) 26ms
     × head leads with the count at display step; entries carry when/said/meta/verbs 2ms
 ❯ .claude/worktrees/agent-a2d29ca16535a1a8f/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 22ms
     × loading is a status, error an alert with retry, empty a quiet label 3ms
     × a row carries title, detail, meta, and a verb slot 0ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-a297a81f50e1dac2b/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 30ms
     × exposes no setter for status, target, poli
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```
