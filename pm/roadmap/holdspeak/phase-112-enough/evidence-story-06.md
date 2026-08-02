# Evidence - HS-112-06

- **Story:** HS-112-06 - The open mic
- **Status:** done
- **Date:** 2026-08-02

## Proof

### Captured run — 2026-08-02T17:12:04Z

- **Command:** `npx vitest run src/lib/__tests__/vad.test.ts src/lib/__tests__/micSession.test.ts src/pages/cores/__tests__/openMicDeck.test.tsx`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** f6d4285ddc412ecbdbe05a39d01a3d88742ac1d9

```text

 RUN  v4.1.10 /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-aa19073b8b482c481

 ❯ web/src/lib/__tests__/micSession.test.ts (13 tests | 13 failed) 11ms
     × asks for the microphone ONCE across many utterances 4ms
     × suspends between utterances instead of tearing the device down 1ms
     × runs on an AudioWorklet, never the deprecated ScriptProcessor 0ms
     × falls back to a script processor only where AudioWorklet is absent 1ms
     × closing stops the tracks for real — CLOSED is not muted 0ms
     × releases the device when the pause outlasts the idle window 1ms
     × reports the capture level from the one frame path 0ms
     × segments continuous audio into utterances with no key touched 0ms
     × a hold takes the floor: the open mic captures nothing while held 1ms
     × a cancelled hold hands the floor back without dropping the grant 0ms
     × one verb drops the stream entirely 0ms
     × dropping the open mic mid-hold keeps the hold's own capture 0ms
     × refuses honestly when the browser withholds the microphone 2ms
 ❯ web/src/pages/cores/__tests__/openMicDeck.test.tsx (8 tests | 8 failed) 4ms
     × opens the session once and lands utterances with no key touched 2ms
     × obeys the deck's aim like a released TALK does 0ms
     × rehearses instead of delivering while REHEARSE is latched 0ms
     × drops an empty transcript silently — silence spends nothing 0ms
     × renders a transcription failure in flow, never as an overlay 0ms
     × the latch drops the stream and the lamp follows the session 0ms
     × refuses in flow when the browser withholds the microphone 0ms
     × drops the stream when the room closes 0ms

⎯⎯⎯⎯⎯⎯ Failed Tests 21 ⎯⎯⎯⎯⎯⎯⎯

 FAIL  web/src/lib/__tests__/micSession.test.ts > one grant, one stream (HS-112-06) > asks for the microphone ONCE across many utterances
ReferenceError: window is not defined
 ❯ micCaptureSupported web/src/lib/micSession.ts:133:23
    131|
    132| export function micCaptureSupported(): boolean {
    133|   const audioWindow = window as AudioWindow;
       |                       ^
    134|   return (
    135|     typeof navigator.mediaDevices?.getUserMedia === "function" &&
 ❯ buildSession web/src/lib/micSession.ts:191:8
 ❯ ensureSession web/src/lib/micSession.ts:241:16
 ❯ beginHold web/src/lib/micSession.ts:291:11
 ❯ web/src/lib/__tests__/micSession.test.ts:142:13

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[1/21]⎯

 FAIL  web/src/lib/__tests__/micSession.test.ts > one grant, one stream (HS-112-06) > suspends between utterances instead of tearing the device down
ReferenceError: window is not defined
 ❯ micCaptureSupported web/src/lib/micSession.ts:133:23
    131|
    132| export function micCaptureSupported(): boolean {
    133|   const audioWindow = window as AudioWindow;
       |                       ^
    134|   return (
    135|     typeof navigator.mediaDevices?.getUserMedia === "function" &&
 ❯ buildSession web/src/lib/micSession.ts:191:8
 ❯ ensureSession web/src/lib/micSession.ts:241:16
 ❯ beginHold web/src/lib/micSession.ts:291:11
 ❯ web/src/lib/__tests__/micSession.test.ts:152:11

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[2/21]⎯

 FAIL  web/src/lib/__tests__/micSession.test.ts > one grant, one stream (HS-112-06) > runs on an AudioWorklet, never the deprecated ScriptProcessor
ReferenceError: window is not defined
 ❯ micCaptureSupported web/src/lib/micSession.ts:133:23
    131|
    132| export function micCaptureSupported(): boolean {
    133|   const audioWindow = window as AudioWindow;
       |                       ^
    134|   return (
    135|     typeof navigator.mediaDevices?.getUserMedia === "function" &&
 ❯ buildSession web/src/lib/micSession.ts:191:8
 ❯ ensureSession web/src/lib/micSession.ts:241:16
 ❯ beginHold web/src/lib/micSession.ts:291:11
 ❯ web/src/lib/__tests__/micSession.test.ts:166:11

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[3/21]⎯

 FAIL  web/src/lib/__tests__/micSession.test.ts > one grant, one stream (HS-112-06) > falls back to a script processor only where AudioWorklet is absent
ReferenceError: window is not defined
 ❯ micCaptureSupported web/src/lib/micSession.ts:133:23
    131|
    132| export function micCaptureSupported(): boolean {
    133|   const audioWindow = window as AudioWindow;
       |                       ^
    134|   return (
    135|     typeof navigator.mediaDevices?.getUserMedia === "function" &&
 ❯ buildSession web/src/lib/micSession.ts:191:8
 ❯ ensureSession web/src/lib/micSession.ts:241:16
 ❯ beginHold web/src/lib/micSession.ts:291:11
 ❯ web/src/lib/__tests__/micSession.test.ts:176:11

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[4/21]⎯

 FAIL  web/src/lib/__tests__/micSession.test.ts > one grant, one stream (HS-112-06) > closing stops the tracks for real — CLOSED is not muted
ReferenceError: window is not defined
 ❯ micCaptureSupported web/src/lib/micSession.ts:133:23
    131|
    132| export function micCaptureSupported(): boolean {
    133|   const audioWindow = window as AudioWindow;
       |                       ^
    134|   return (
    135|     typeof navigator.mediaDevices?.getUserMedia === "function" &&
 ❯ buildSession web/src/lib/micSession.ts:191:8
 ❯ ensureSession web/src/lib/micSession.ts:241:16
 ❯ beginHold web/src/lib/micSession.ts:291:11
 ❯ web/src/lib/__tests__/micSession.test.ts:181:11

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[5/21]⎯

 FAIL  web/src/lib/__tests__/micSession.test.ts > one grant, one stream (HS-112-06) > releases the device when the pause outlasts the idle window
ReferenceError: window is not defined
 ❯ micCaptureSupported web/src/lib/micSession.ts:133:23
    131|
    132| export function micCaptureSupported(): boolean {
    133|   const audioWindow = window as AudioWindow;
       |                       ^
    134|   return (
    135|     typeof navigator.mediaDevices?.getUserMedia === "function" &&
 ❯ buildSession web/src/lib/micSession.ts:191:8
 ❯ ensureSession web/src/lib/micSession.ts:241:16
 ❯ beginHold web/src/lib/micSession.ts:291:11
 ❯ web/src/lib/__tests__/micSession.test.ts:193:11

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[6/21]⎯

 FAIL  web/src/lib/__tests__/micSession.test.ts > one grant, one stream (HS-112-06) > reports the capture level from the one frame path
ReferenceError: window is not defined
 ❯ micCaptureSupported web/src/lib/micSession.ts:133:23
    131|
    132| export function micCaptureSupported(): boolean {
    133|   const audioWindow = window as AudioWindow;
       |                       ^
    134|   return (
    135|     typeof navigator.mediaDevices?.getUserMedia === "function" &&
 ❯ buildSession web/src/lib/micSession.ts:191:8
 ❯ ensureSession web/src/lib/micSession.ts:241:16
 ❯ beginHold web/src/lib/micSession.ts:291:11
 ❯ web/src/lib/__tests__/micSession.test.ts:204:11

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[7/21]⎯

 FAIL  web/src/lib/__tests__/micSession.test.ts > the open mic (HS-112-06) > segments continuous audio into utterances with no key touched
ReferenceError: window is not defined
 ❯ micCaptureSupported web/src/lib/micSession.ts:133:23
    131|
    132| export function micCaptureSupported(): boolean {
    133|   const audioWindow = window as AudioWindow;
       |                       ^
    134|   return (
    135|     typeof navigator.mediaDevices?.getUserMedia === "function" &&
 ❯ buildSession web/src/lib/micSession.ts:191:8
 ❯ ensureSession web/src/lib/micSession.ts:241:16
 ❯ startOpenMic web/src/lib/micSession.ts:343:22
 ❯ web/src/lib/__tests__/micSession.test.ts:216:11

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[8/21]⎯

 FAIL  web/src/lib/__tests__/micSession.test.ts > the open mic (HS-112-06) > a hold takes the floor: the open mic captures nothing while held
ReferenceError: window is not defined
 ❯ micCaptureSupported web/src/lib/micSession.ts:133:23
    131|
    132| export function micCaptureSupported(): boolean {
    133|   const audioWindow = window as AudioWindow;
       |                       ^
    134|   return (
    135|     typeof navigator.mediaDevices?.getUserMedia === "function" &&
 ❯ buildSession web/src/lib/micSession.ts:191:8
 ❯ ensureSession web/src/lib/micSession.ts:241:16
 ❯ startOpenMic web/src/lib/micSession.ts:343:22
 ❯ web/src/lib/__tests__/micSession.test.ts:233:11

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[9/21]⎯

 FAIL  web/src/lib/__tests__/micSession.test.ts > the open mic (HS-112-06) > a cancelled hold hands the floor back without dropping the grant
ReferenceError: window is not defined
 ❯ micCaptureSupported web/src/lib/micSession.ts:133:23
    131|
    132| export function micCaptureSupported(): boolean {
    133|   const audioWindow = window as AudioWindow;
       |                       ^
    134|   return (
    135|     typeof navigator.mediaDevices?.getUserMedia === "function" &&
 ❯ buildSession web/src/lib/micSession.ts:191:8
 ❯ ensureSession web/src/lib/micSession.ts:241:16
 ❯ startOpenMic web/src/lib/micSession.ts:343:22
 ❯ web/src/lib/__tests__/micSession.test.ts:255:11

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[10/21]⎯

 FAIL  web/src/lib/__tests__/micSession.test.ts > the open mic (HS-112-06) > one verb drops the stream entirely
ReferenceError: window is not defined
 ❯ micCaptureSupported web/src/lib/micSession.ts:133:23
    131|
    132| export function micCaptureSupported(): boolean {
    133|   const audioWindow = window as AudioWindow;
       |                       ^
    134|   return (
    135|     typeof navigator.mediaDevices?.getUserMedia === "function" &&
 ❯ buildSession web/src/lib/micSession.ts:191:8
 ❯ ensureSession web/src/lib/micSession.ts:241:16
 ❯ startOpenMic web/src/lib/micSession.ts:343:22
 ❯ web/src/lib/__tests__/micSession.test.ts:266:11

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[11/21]⎯

 FAIL  web/src/lib/__tests__/micSession.test.ts > the open mic (HS-112-06) > dropping the open mic mid-hold keeps the hold's own capture
ReferenceError: window is not defined
 ❯ micCaptureSupported web/src/lib/micSession.ts:133:23
    131|
    132| export function micCaptureSupported(): boolean {
    133|   const audioWindow = window as AudioWindow;
       |                       ^
    134|   return (
    135|     typeof navigator.mediaDevices?.getUserMedia === "function" &&
 ❯ buildSession web/src/lib/micSession.ts:191:8
 ❯ ensureSession web/src/lib/micSession.ts:241:16
 ❯ startOpenMic web/src/lib/micSession.ts:343:22
 ❯ web/src/lib/__tests__/micSession.test.ts:274:11

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[12/21]⎯

 FAIL  web/src/lib/__tests__/micSession.test.ts > the open mic (HS-112-06) > refuses honestly when the browser withholds the microphone
AssertionError: expected [Function] to throw error matching /Permission denied/ but got 'window is not defined'

- Expected:
/Permission denied/

+ Received:
"window is not defined"

 ❯ web/src/lib/__tests__/micSession.test.ts:286:48
    284|     closeMicSession();
    285|     getUserMedia.mockRejectedValueOnce(new Error("Permission denied"));
    286|     await expect(startOpenMic(() => undefined)).rejects.toThrow(
       |                                                ^
    287|       /Permission denied/,
    288|     );

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[13/21]⎯

 FAIL  web/src/pages/cores/__tests__/openMicDeck.test.tsx > the open mic on the Speak deck (HS-112-06) > opens the session once and lands utterances with no key touched
 FAIL  web/src/pages/cores/__tests__/openMicDeck.test.tsx > the open mic on the Speak deck (HS-112-06) > obeys the deck's aim like a released TALK does
 FAIL  web/src/pages/cores/__tests__/openMicDeck.test.tsx > the open mic on the Speak deck (HS-112-06) > rehearses instead of delivering while REHEARSE is latched
 FAIL  web/src/pages/cores/__tests__/openMicDeck.test.tsx > the open mic on the Speak deck (HS-112-06) > drops an empty transcript silently — silence spends nothing
 FAIL  web/src/pages/cores/__tests__/openMicDeck.test.tsx > the open mic on the Speak deck (HS-112-06) > renders a transcription failure in flow, never as an overlay
 FAIL  web/src/pages/cores/__tests__/openMicDeck.test.tsx > the open mic on the Speak deck (HS-112-06) > the latch drops the stream and the lamp follows the session
 FAIL  web/src/pages/cores/__tests__/openMicDeck.test.tsx > the open mic on the Speak deck (HS-112-06) > refuses in flow when the browser withholds the microphone
 FAIL  web/src/pages/cores/__tests__/openMicDeck.test.tsx > the open mic on the Speak deck (HS-112-06) > drops the stream when the room closes
ReferenceError: localStorage is not defined
 ❯ web/src/pages/cores/__tests__/openMicDeck.test.tsx:120:3
    118| beforeEach(() => {
    119|   vi.clearAllMocks();
    120|   localStorage.clear();
       |   ^
    121|   mocks.segment = null;
    122|   mocks.startOpenMic.mockImplementation(

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[14/21]⎯


 Test Files  2 failed | 1 passed (3)
      Tests  21 failed | 9 passed (30)
   Start at  11:12:05
   Duration  353ms (transform 208ms, setup 0ms, import 357ms, tests 21ms, environment 0ms)
```

### Captured run — 2026-08-02T17:12:25Z

- **Command:** `npm --prefix web run test:web -- run src/lib/__tests__/vad.test.ts src/lib/__tests__/micSession.test.ts src/pages/cores/__tests__/openMicDeck.test.tsx`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f6d4285ddc412ecbdbe05a39d01a3d88742ac1d9

```text

> holdspeak-web@0.0.1 test:web
> vitest run --maxWorkers=2 run src/lib/__tests__/vad.test.ts src/lib/__tests__/micSession.test.ts src/pages/cores/__tests__/openMicDeck.test.tsx


 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-aa19073b8b482c481/web


 Test Files  4 passed (4)
      Tests  31 passed (31)
   Start at  11:12:25
   Duration  1.17s (transform 222ms, setup 191ms, import 355ms, tests 307ms, environment 982ms)
```

### Captured run — 2026-08-02T17:36:17Z

- **Command:** `./.venv/bin/python -m pytest -q tests/unit/test_audio_floor_open_mic.py tests/unit/test_speak_room_delivery.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 596206b324b815a728bd2b29d433bb075c5e18b0

```text
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-aa19073b8b482c481/.venv/bin/python: No module named pytest
```

### Captured run — 2026-08-02T17:36:33Z

- **Command:** `./.venv/bin/python -m pytest -q tests/unit/test_audio_floor_open_mic.py tests/unit/test_speak_room_delivery.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 596206b324b815a728bd2b29d433bb075c5e18b0

```text
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-aa19073b8b482c481/.venv/bin/python: No module named pytest
```

### Captured run — 2026-08-02T17:36:40Z

- **Command:** `./.venv/bin/python -m pytest -q tests/unit/test_audio_floor_open_mic.py tests/unit/test_speak_room_delivery.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 596206b324b815a728bd2b29d433bb075c5e18b0

```text
.........................                                                [100%]
25 passed in 3.93s
```
