# Evidence - HS-115-04

- **Story:** HS-115-04 - System surfaces
- **Status:** done
- **Date:** 2026-08-03

## Proof

### Captured run — 2026-08-03T23:43:15Z

- **Command:** `npx vitest run`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 0ee9da2480a778b7b618fbd9ac6fa72289a17c26

```text

 RUN  v4.1.10 /Users/karol/dev/tools/HoldSpeak

 ❯ .claude/worktrees/agent-a5e3a987f4d1e8805/web/src/desk/surface/__tests__/citations.test.tsx (3 tests | 2 failed) 4ms
     × renders one openable token per source ref 3ms
     × renders nothing for an empty receipt (no zero-theater) 0ms
 ❯ .claude/worktrees/agent-ace7e51320a364b7d/web/src/desk/surface/__tests__/citations.test.tsx (3 tests | 2 failed) 4ms
     × renders one openable token per source ref 2ms
     × renders nothing for an empty receipt (no zero-theater) 0ms
 ❯ .claude/worktrees/agent-a5e3a987f4d1e8805/web/src/components/AppShell.test.tsx (1 test | 1 failed) 3ms
     × renders the immersive frame with no flat header or nav 2ms
 ❯ web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 20ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-ace7e51320a364b7d/web/src/desk/components/PrReceiptsSection.test.tsx (3 tests | 3 failed) 4ms
     × keeps unavailable verbs visible with their named reason 2ms
     × marks an ungated agent on the row and in Info 0ms
     × shows the complete proposed comment before approval and offers deny 0ms
 ❯ .claude/worktrees/agent-af90eea2d5bfb90ad/web/src/meetings/MeetingIntelRecovery.test.tsx (3 tests | 3 failed) 4ms
     × names completed and remaining work without claiming Ready 2ms
     × skips only remaining work and keeps Retry available 0ms
     × protects a running attempt from competing recovery actions 0ms
 ❯ .claude/worktrees/agent-aa95e20ba9e8eac56/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 18ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-aa95e20ba9e8eac56/web/src/desk/surface/__tests__/stream.test.tsx (4 tests | 1 failed) 16ms
     × head leads with the count at display step; entries carry when/said/meta/verbs 2ms
 ❯ .claude/worktrees/agent-a48a6c7e3915d09e6/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 19ms
     × exposes no setter for status, target, policy, grant, or attempt state 3ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a54d6bf2eb4162eec/web/src/desk/surface/__tests__/stream.test.tsx (4 tests | 1 failed) 17ms
     × head leads with the count at display step; entries carry when/said/meta/verbs 2ms
 ❯ .claude/worktrees/agent-a54d6bf2eb4162eec/web/src/desk/__tests__/a11y.test.tsx (3 tests | 3 failed) 3ms
     × opening moves focus into the window; closing returns it 2ms
     × Escape inside the window closes it 0ms
     × window + dock: no serious or critical violations 0ms
 ❯ .claude/worktrees/agent-addf5256665a9e069/web/src/meetings/MeetingIntelRecovery.test.tsx (3 tests | 3 failed) 5ms
     × tokens the state, the retained work, and the remaining work 3ms
     × skips only remaining work and keeps Retry available 1ms
     × protects a running attempt from competing recovery actions 0ms
 ❯ .claude/worktrees/agent-a3a3e870a12496cea/web/src/desk/__tests__/a11y.test.tsx (3 tests | 3 failed) 3ms
     × opening moves focus into the window; closing returns it 2ms
     × Escape inside the window closes it 0ms
     × window + dock: no serious or critical violations 0ms
 ❯ .claude/worktrees/agent-a3a3e870a12496cea/web/src/components/signal/Signal.test.tsx (2 tests | 2 failed) 3ms
     × associates field label, description and error 2ms
     × exposes semantic busy and disabled states 0ms
 ❯ .claude/worktrees/agent-a2d29ca16535a1a8f/web/src/desk/components/AgentAvatar.test.tsx (4 tests | 4 failed) 5ms
     × empty avatar wears the deterministic automaton sprite 3ms
     × the legacy 🤖 default also wears the sprite (never the emoji) 0ms
     × a user-set custom avatar stays text 0ms
     × model kind wears the cartridge sprite 0ms
 ❯ .claude/worktrees/agent-aa95e20ba9e8eac56/web/src/pages/cores/__tests__/cores.test.tsx (4 tests | 4 failed) 4ms
     × ActivityCore: content without page chrome; verbs in the surface bar 2ms
     × CommandsCore: content without page chrome 0ms
     × maps every former flat route to its desk surface 0ms
     × carries subject decoding where deep links need scope 0ms
 ❯ .claude/worktrees/agent-a9e46b0f4a53a0b97/web/src/lib/durableDraft.test.tsx (2 tests | 2 failed) 3ms
     × writes synchronously and restores after a remount 2ms
     × clears only the persisted copy while retaining the live editor value 0ms
 ❯ .claude/worktrees/agent-a8cba81cd3029ac82/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 25ms
     × exposes no setter for status, target, policy, grant, or attempt state 3ms
     × refresh derives every field from the server snapshot, not any argument 1ms
     × setFocusSource only touches the view preference and localStorage 1ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-aeb023a4f3a91aa8b/web/src/components/signal/Signal.test.tsx (2 tests | 2 failed) 4ms
     × associates field label, description and error 2ms
     × exposes semantic busy and disabled states 0ms
 ❯ .claude/worktrees/agent-aa95e20ba9e8eac56/web/src/desk/__tests__/a11y.test.tsx (3 tests | 3 failed) 3ms
     × opening moves focus into the window; closing returns it 2ms
     × Escape inside the window closes it 0ms
     × window + dock: no serious or critical violations 0ms
 ❯ .claude/worktrees/agent-aeb023a4f3a91aa8b/web/src/desk/components/__tests__/gateShade.test.tsx (2 tests | 2 failed) 4ms
     × renders the held call with its redacted preview and Approve lands the decision 2ms
     × Deny reveals the in-place reason line and sends it verbatim 0ms
 ❯ .claude/worktrees/agent-aeb023a4f3a91aa8b/web/src/desk/components/__tests__/systemShade.test.tsx (2 tests | 2 failed) 4ms
     × groups honestly: needs-you verbs inline, finished with Open, learned zero says zero 2ms
     × closed renders nothing; Escape closes when open 1ms
 ❯ .claude/worktrees/agent-a55cc05af5578a9dd/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 21ms
     × exposes no setter for status, target, policy, grant, or attempt state 3ms
     × refresh derives every field from the server snapshot, not any argument 1ms
     × setFocusSource only touches the view preference and localStorage 1ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-af90eea2d5bfb90ad/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 21ms
     × loading is a status, error an alert with retry, empty a quiet label 3ms
     × a row carries title, detail, meta, and a verb slot 1ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-aa95e20ba9e8eac56/web/src/pages/cores/__tests__/speakRoom.test.tsx (12 tests | 12 failed) 7ms
     × posts a released utterance through the delivery contract with one delivery id 3ms
     × shows release-to-landed latency on the footer receipt and the register 0ms
     × mints a fresh delivery id for each utterance 0ms
     × aims at the awaiting agent and requires one to be awaiting 0ms
     × THIS FIELD fills the well and delivers nothing 0ms
     × remembers the aim across a remount 0ms
     × previews through the dry run and delivers nothing when armed 0ms
     × names the well's verb after the mode it is in 0ms
     × names an unresolved desktop focus in the receipt bar and the register 0ms
     × names an aimed agent with nothing awaiting 0ms
     × names a transcription failure without losing the deck 1ms
     × refuses honestly when the hub has nothing to deliver into 0ms
 ❯ .claude/worktrees/agent-a578ae0294a20dc2e/web/src/components/AppShell.test.tsx (1 test | 1 failed) 3ms
     × renders the immersive frame with no flat header or nav 2ms
 ❯ .claude/worktrees/agent-a448123bea1af8070/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 23ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a54d6bf2eb4162eec/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 19ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-aeb023a4f3a91aa8b/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 28ms
     × loading is a status, error an alert with retry, empty a quiet label 3ms
     × a row carries title, detail, meta, and a verb slot 0ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 1ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 2ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-a880577fce625816c/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 30ms
     × exposes no setter for status, target, policy, grant, or attempt state 8ms
     × refresh derives every field from the server snapshot, not any argument 1ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a297a81f50e1dac2b/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 19ms
     × exposes no setter for status, target, policy, grant, or attempt state 3ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-aeb023a4f3a91aa8b/web/src/desk/surface/__tests__/stream.test.tsx (4 tests | 1 failed) 16ms
     × head leads with the count at display step; entries carry when/said/meta/verbs 2ms
 ❯ .claude/worktrees/agent-a5e3a987f4d1e8805/web/src/desk/components/__tests__/zoneWindow.test.tsx (3 tests | 3 failed) 3ms
     × opens as a coexisting window and persists the open set 2ms
     × closes one window and persists the remainder 0ms
     × remembers view and sort per zone, persisted 0ms
 ❯ .claude/worktrees/agent-a2d29ca16535a1a8f/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 20ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a448123bea1af8070/web/src/desk/surface/__tests__/citations.test.tsx (3 tests | 2 failed) 3ms
     × renders one openable token per source ref 2ms
     × renders nothing for an empty receipt (no zero-theater) 0ms
 ❯ .claude/worktrees/agent-a63ec577c1e3341a3/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 23ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 1ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-aa95e20ba9e8eac56/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 20ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 0ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-ace7e51320a364b7d/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 18ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-aa0b20489ad20af48/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 19ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a912768e6305fc3dc/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 21ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 0ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-a3a3e870a12496cea/web/src/pages/cores/__tests__/projectMemoryCore.test.tsx (8 tests | 6 failed) 14ms
     × wears every lifecycle and names a supersession successor 2ms
     × renders openable citation chips and derives the honest overflow count 1ms
     × renders the named comparison and lifecycle in the timeline 0ms
     × shows an honest empty timeline 0ms
     × shows an honest zero state after a project-scoped search 0ms
     × registers and restores the scoped Project Memory surface 0ms
 ❯ .claude/worktrees/agent-a5e3a987f4d1e8805/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 19ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a8cba81cd3029ac82/web/src/desk/surface/__tests__/stream.test.tsx (4 tests | 1 failed) 18ms
     × head leads with the count at display step; entries carry when/said/meta/verbs 2ms
 ❯ .claude/worktrees/agent-aa19073b8b482c481/web/src/meetings/MeetingConflictRecovery.test.tsx (3 tests | 3 failed) 4ms
     × shows both retained versions and applies only the explicit choice 2ms
     × names an incoming tombstone as a destructive Meeting deletion 0ms
     × states that both versions remain when recovery cannot load 0ms
 ❯ .claude/worktrees/agent-a9e46b0f4a53a0b97/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 21ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 0ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-ace7e51320a364b7d/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 19ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 1ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 1ms
 ❯ .claude/worktrees/agent-a3d8e9e821063f0fa/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 19ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a880577fce625816c/web/src/desk/surface/__tests__/wings.test.tsx (3 tests | 3 failed) 6ms
     × is a tablist with a roving Tab stop on the active wing 4ms
     × ArrowRight/ArrowLeft/Home/End walk the wings 1ms
     × the gear door is a pressed-state gadget, not a tab 0ms
 ❯ .claude/worktrees/agent-a3d8e9e821063f0fa/web/src/desk/__tests__/surface-windows.test.tsx (4 tests | 4 failed) 3ms
     × opening writes the key+scope to hs.desk.open-windows 2ms
     × closing drops the key from storage 0ms
     × a fresh module load rehydrates the same windows (the reload case) 0ms
     × a corrupt/missing slot starts with nothing open 0ms
 ❯ .claude/worktrees/agent-a48a6c7e3915d09e6/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 21ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 0ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```
