# Evidence - HS-115-03

- **Story:** HS-115-03 - Object windows
- **Status:** done
- **Date:** 2026-08-03

## Proof

### Captured run — 2026-08-03T23:41:33Z

- **Command:** `npx vitest run`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 0ee9da2480a778b7b618fbd9ac6fa72289a17c26

```text

 RUN  v4.1.10 /Users/karol/dev/tools/HoldSpeak

 ❯ .claude/worktrees/agent-a880577fce625816c/web/src/lib/__tests__/micSession.test.ts (13 tests | 13 failed) 15ms
     × asks for the microphone ONCE across many utterances 5ms
     × suspends between utterances instead of tearing the device down 1ms
     × runs on an AudioWorklet, never the deprecated ScriptProcessor 2ms
     × refuses where AudioWorklet is absent — no deprecated fallback 0ms
     × closing stops the tracks for real — CLOSED is not muted 0ms
     × releases the device when the pause outlasts the idle window 1ms
     × reports the capture level from the one frame path 0ms
     × segments continuous audio into utterances with no key touched 0ms
     × a hold takes the floor: the open mic captures nothing while held 1ms
     × a cancelled hold hands the floor back without dropping the grant 0ms
     × one verb drops the stream entirely 0ms
     × dropping the open mic mid-hold keeps the hold's own capture 0ms
     × refuses honestly when the browser withholds the microphone 2ms
 ❯ web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 27ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a54d6bf2eb4162eec/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 23ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a880577fce625816c/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 23ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 3ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a8cba81cd3029ac82/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 25ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a297a81f50e1dac2b/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 23ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ web/src/components/signal/Signal.test.tsx (2 tests | 2 failed) 4ms
     × associates field label, description and error 3ms
     × exposes semantic busy and disabled states 1ms
 ❯ .claude/worktrees/agent-a9e46b0f4a53a0b97/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 20ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a5e3a987f4d1e8805/web/src/desk/surface/__tests__/stream.test.tsx (4 tests | 1 failed) 17ms
     × head leads with the count at display step; entries carry when/said/meta/verbs 2ms
 ❯ .claude/worktrees/agent-ace7e51320a364b7d/web/src/desk/surface/__tests__/stream.test.tsx (4 tests | 1 failed) 16ms
     × head leads with the count at display step; entries carry when/said/meta/verbs 2ms
 ❯ .claude/worktrees/agent-a64d33e0ee274a344/web/src/pages/cores/__tests__/openMicDeck.test.tsx (11 tests | 11 failed) 5ms
     × opens the session once and lands utterances with no key touched 3ms
     × obeys the deck's aim like a released TALK does 0ms
     × rehearses instead of delivering while REHEARSE is latched 0ms
     × drops an empty transcript silently — silence spends nothing 0ms
     × renders a transcription failure in flow, never as an overlay 0ms
     × the latch drops the stream and the lamp follows the session 0ms
     × refuses in flow when the browser withholds the microphone 0ms
     × takes the audio floor before the device opens 0ms
     × refuses BY NAME when a meeting holds the floor, and never opens 0ms
     × releases the floor when the latch drops the stream 0ms
     × drops the stream when the room closes 0ms
 ❯ .claude/worktrees/agent-a6e82786f8899031f/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 19ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a297a81f50e1dac2b/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 20ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 0ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-a3d8e9e821063f0fa/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 19ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 0ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-a55cc05af5578a9dd/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 20ms
     × loading is a status, error an alert with retry, empty a quiet label 3ms
     × a row carries title, detail, meta, and a verb slot 1ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-af90eea2d5bfb90ad/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 18ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-addf5256665a9e069/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 18ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a8cba81cd3029ac82/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 20ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 0ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-a3d8e9e821063f0fa/web/src/desk/__tests__/commandDeck.test.tsx (6 tests | 6 failed) 5ms
     × prefix(3) beats recents(2) beats substring(1) 3ms
     × Enter runs the TOP hit — the palette dead-end is gone 0ms
     × ArrowDown moves the selection index; Enter runs the moved hit 0ms
     × meetings sit in their own MEETINGS band 0ms
     × Escape clears the query first, closes second 0ms
     × the empty deck lists every program (the launcher truth) 0ms
 ❯ .claude/worktrees/agent-a3a3e870a12496cea/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 20ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 0ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-a64d33e0ee274a344/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 18ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a578ae0294a20dc2e/web/src/desk/surface/__tests__/stream.test.tsx (4 tests | 1 failed) 16ms
     × head leads with the count at display step; entries carry when/said/meta/verbs 2ms
 ❯ .claude/worktrees/agent-a578ae0294a20dc2e/web/src/pages/cores/__tests__/projectMemoryCore.test.tsx (8 tests | 6 failed) 14ms
     × wears every lifecycle and names a supersession successor 2ms
     × renders openable citation chips and derives the honest overflow count 1ms
     × renders the named comparison and lifecycle in the timeline 0ms
     × shows an honest empty timeline 0ms
     × shows an honest zero state after a project-scoped search 0ms
     × registers and restores the scoped Project Memory surface 0ms
 ❯ .claude/worktrees/agent-a578ae0294a20dc2e/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 19ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 0ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-a578ae0294a20dc2e/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 18ms
     × exposes no setter for status, target, policy, grant, or attempt state 2ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a5e3a987f4d1e8805/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 20ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 1ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-a5f9c1331117b619e/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 21ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 0ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-a448123bea1af8070/web/src/desk/__tests__/shell.test.tsx (23 tests | 23 failed) 6ms
     × shows a chip per open window; the four applications ride always 3ms
     × tap focuses; a parked window's chip restores it 0ms
     × the dock close affordance drives the window's own close 0ms
     × Ctrl+` cycles focus in MRU order, restoring as it lands 0ms
     × reset layout forgets rects and lifecycle and persists the wipe 0ms
     × left/right flanks take halves below the chrome band 0ms
     × corners take quarters 0ms
     × the open middle is a free park (no snap) 0ms
     × a free stage keeps the seed 0ms
     × a second window at the same home moves off the first title bar 0ms
     × an off-viewport seed lands whole inside the working band 0ms
     × an oversize window shrinks to the band 0ms
     × a window may shade another's body but never its title bar 0ms
     × a saturated stage cascades off the home seat, still in band 0ms
     × right and bottom edges grow with the pointer 0ms
     × the left edge moves x and shrinks w together 0ms
     × the left edge keeps the right edge fixed at the minimum 0ms
     × the bottom-left corner drives both axes 0ms
     × four windows tile 2x2 inside the working band, no overlap 0ms
     × a last-row straggler centers 0ms
     × a rect persisted on a larger viewport lands whole 0ms
     × an in-band rect is untouched 0ms
     × routes a registered surface and reports unregistered ones 0ms
 ❯ .claude/worktrees/agent-a0160236356b756a8/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 20ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 0ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-a448123bea1af8070/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 24ms
     × exposes no setter for status, target, policy, grant, or attempt state 3ms
     × refresh derives every field from the server snapshot, not any argument 1ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 0ms
 ❯ .claude/worktrees/agent-a9e46b0f4a53a0b97/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 21ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 0ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ web/src/desk/surface/__tests__/stream.test.tsx (4 tests | 1 failed) 18ms
     × head leads with the count at display step; entries carry when/said/meta/verbs 2ms
 ❯ web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 20ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 0ms
     × onOpen makes the row body one press target 0ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-a2d29ca16535a1a8f/web/src/pages/ComponentsPage.test.tsx (1 test | 1 failed) 3ms
     × has no automatically detectable accessibility violations 2ms
 ❯ .claude/worktrees/agent-a880577fce625816c/web/src/desk/surface/__tests__/stream.test.tsx (4 tests | 1 failed) 17ms
     × head leads with the count at display step; entries carry when/said/meta/verbs 2ms
 ❯ .claude/worktrees/agent-a5f9c1331117b619e/web/src/desk/surface/__tests__/stream.test.tsx (4 tests | 1 failed) 16ms
     × head leads with the count at display step; entries carry when/said/meta/verbs 2ms
 ❯ .claude/worktrees/agent-aa0b20489ad20af48/web/src/desk/__tests__/delivery.test.ts (17 tests | 4 failed) 21ms
     × exposes no setter for status, target, policy, grant, or attempt state 3ms
     × refresh derives every field from the server snapshot, not any argument 0ms
     × setFocusSource only touches the view preference and localStorage 0ms
     × polls economically: the second refresh carries the revision as If-None-Match and a 304 keeps the frame 1ms
 ❯ .claude/worktrees/agent-a448123bea1af8070/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 21ms
     × loading is a status, error an alert with retry, empty a quiet label 3ms
     × a row carries title, detail, meta, and a verb slot 1ms
     × onOpen makes the row body one press target 1ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/worktrees/agent-a880577fce625816c/web/src/desk/surface/__tests__/surface.test.tsx (10 tests | 7 failed) 20ms
     × loading is a status, error an alert with retry, empty a quiet label 2ms
     × a row carries title, detail, meta, and a verb slot 0ms
     × onOpen makes the row body one press target 1ms
     × MetricStrip omits empty figures (never zero-theater) 0ms
     × SurfaceFacts de-snakes keys and omits meaningless values 0ms
     × ConfirmVerb: first press arms, second fires, arming self-disarms 1ms
     × renders loops as surface rows with zero page grammar in the DOM 0ms
 ❯ .claude/work
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```
