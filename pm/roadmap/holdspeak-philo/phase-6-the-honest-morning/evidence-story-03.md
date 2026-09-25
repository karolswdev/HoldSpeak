# Evidence - PHILO-6-03

- **Story:** PHILO-6-03 - The toast that does not cover
- **Status:** done
- **Date:** 2026-09-24

## Proof

### Captured run — 2026-09-25T04:25:00Z

- **Command:** `bash -c set -euo pipefail
export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH
export HOME=$(mktemp -d)
cd web
./node_modules/.bin/vitest list src/desk/chair/ChairHome.test.tsx
./node_modules/.bin/vitest run src/desk/chair/ChairHome.test.tsx --maxWorkers=2`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 437406883fdc8f4f09697fd79249752a26703459

```text
src/desk/chair/ChairHome.test.tsx > Chair write recovery > keeps a failed generation actionable and clears the receipt after retry

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-6-03/web


 Test Files  1 passed (1)
      Tests  1 passed (1)
   Start at  22:25:01
   Duration  929ms (transform 348ms, setup 59ms, import 463ms, tests 152ms, environment 179ms)
```

### Captured run — 2026-09-25T04:39:07Z

- **Command:** `bash -c set -euo pipefail
export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH
export HOME=$(mktemp -d)
export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright
export HOLDSPEAK_EVIDENCE_WRITE=1
cd /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo603-red-z5r_bw9b
uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.philo603.toast.arrival --brain astra --viewport 393 --engine replayed --no-build --out /Users/karol/dev/tools/wt-philo-6-03/pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/red/`
- **Cwd:** .
- **Exit code:** 143
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text
node:events:486
      throw er; // Unhandled 'error' event
      ^

Error: write EPIPE
    at WriteWrap.onWriteComplete [as oncomplete] (node:internal/stream_base_commons:87:19)
Emitted 'error' event on Socket instance at:
    at emitErrorNT (node:internal/streams/destroy:170:8)
    at emitErrorCloseNT (node:internal/streams/destroy:129:3)
    at process.processTicksAndRejections (node:internal/process/task_queues:89:21) {
  errno: -32,
  code: 'EPIPE',
  syscall: 'write'
}

Node.js v24.11.1
```

### Captured run — 2026-09-25T04:43:21Z

- **Command:** `bash -c set -euo pipefail
export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH
export HOME=$(mktemp -d)
cd /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo603-red-z5r_bw9b/web
./node_modules/.bin/vitest list src/components/AmbientLayer.test.tsx src/components/aftercarePlacement.test.tsx
./node_modules/.bin/vitest run src/components/AmbientLayer.test.tsx src/components/aftercarePlacement.test.tsx --maxWorkers=2`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text
src/components/aftercarePlacement.test.tsx > PHILO-6-03 aftercare rendered placement > publishes the real aftercare signal into the actual ChairHome slot
src/components/aftercarePlacement.test.tsx > PHILO-6-03 aftercare rendered placement > renders into the actual active SurfaceWindowHost slot
src/components/aftercarePlacement.test.tsx > PHILO-6-03 aftercare rendered placement > renders into the actual Floor list host when no window is open
src/components/aftercarePlacement.test.tsx > PHILO-6-03 aftercare rendered placement > keeps the fixed fallback only when the spatial Floor has no slot
src/components/aftercarePlacement.test.tsx > PHILO-6-03 aftercare rendered placement > scrolls an obscured phone slot once and does not scroll a desktop slot
src/components/aftercarePlacement.test.tsx > PHILO-6-03 aftercare rendered placement > scrolls an off-Arrival phone slot once even when it is already visible
src/components/aftercarePlacement.test.tsx > PHILO-6-03 aftercare rendered placement > scrolls an active window phone slot once
src/components/aftercarePlacement.test.tsx > PHILO-6-03 aftercare rendered placement > does not move the owner while a field has focus
src/components/AmbientLayer.test.tsx > posture-aware dictation preview gate > Secure and Normal-with-preference: the hub-armed preview gates before any commit
src/components/AmbientLayer.test.tsx > posture-aware dictation preview gate > Type it commits exactly once, by token only, and closes the gate
src/components/AmbientLayer.test.tsx > posture-aware dictation preview gate > Discard burns the preview without ever committing
src/components/AmbientLayer.test.tsx > posture-aware dictation preview gate > a failed commit keeps the words and the gate for an explicit retry
src/components/AmbientLayer.test.tsx > posture-aware dictation preview gate > YOLO and Normal-without-preference: no hub frame means no HoldSpeak prompt
src/components/AmbientLayer.test.tsx > meeting aftercare counts > renders only nonzero count tokens (0 open, 0 decided)
src/components/AmbientLayer.test.tsx > meeting aftercare counts > renders only nonzero count tokens (3 open, 0 decided)
src/components/AmbientLayer.test.tsx > meeting aftercare counts > renders only nonzero count tokens (0 open, 2 decided)
src/components/AmbientLayer.test.tsx > meeting aftercare counts > renders only nonzero count tokens (3 open, 2 decided)

 RUN  v4.1.9 /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo603-red-z5r_bw9b/web

 ❯ src/components/aftercarePlacement.test.tsx (8 tests | 8 failed) 7197ms
     × publishes the real aftercare signal into the actual ChairHome slot 1019ms
     × renders into the actual active SurfaceWindowHost slot 1130ms
     × renders into the actual Floor list host when no window is open 1009ms
     × keeps the fixed fallback only when the spatial Floor has no slot 4ms
     × scrolls an obscured phone slot once and does not scroll a desktop slot 1004ms
     × scrolls an off-Arrival phone slot once even when it is already visible 1006ms
     × scrolls an active window phone slot once 1018ms
     × does not move the owner while a field has focus 1006ms

⎯⎯⎯⎯⎯⎯⎯ Failed Tests 8 ⎯⎯⎯⎯⎯⎯⎯

 FAIL  src/components/aftercarePlacement.test.tsx > PHILO-6-03 aftercare rendered placement > publishes the real aftercare signal into the actual ChairHome slot
TestingLibraryElementError: Unable to find an element by: [data-testid="arrival-aftercare-slot"]

Ignored nodes: comments, script, style
[36m<body>[39m
  [36m<div>[39m
    [36m<div[39m
      [33mclass[39m=[32m"chair"[39m
      [33mdata-testid[39m=[32m"chair"[39m
    [36m>[39m
      [36m<div[39m
        [33mclass[39m=[32m"arrival-headline"[39m
        [33mdata-testid[39m=[32m"arrival-headline"[39m
      [36m>[39m
        [36m<h1[39m
          [33mclass[39m=[32m"arrival-display arrival-display--muted"[39m
          [33mdata-testid[39m=[32m"arrival-display"[39m
        [36m>[39m
          [0mNothing needs you[0m
        [36m</h1>[39m
        [36m<div[39m
          [33mclass[39m=[32m"arrival-head-tokens"[39m
          [33mdata-testid[39m=[32m"arrival-head-tokens"[39m
        [36m>[39m
          [36m<span[39m
            [33mclass[39m=[32m"arrival-next"[39m
            [33mdata-testid[39m=[32m"arrival-no-calendar"[39m
          [36m>[39m
            [36m<span[39m
              [33mclass[39m=[32m"arrival-no-calendar-token"[39m
            [36m>[39m
              [0mNO CALENDAR[0m
            [36m</span>[39m
            [0m [0m
            [36m<button[39m
              [33mclass[39m=[32m"btn btn--ghost btn--sm "[39m
              [33mdata-testid[39m=[32m"arrival-connect-calendar"[39m
              [33mtype[39m=[32m"button"[39m
            [36m>[39m
              [0mConnect calendar[0m
            [36m</button>[39m
          [36m</span>[39m
        [36m</div>[39m
      [36m</div>[39m
      [36m<div[39m
        [33mdata-testid[39m=[32m"arrival-brief"[39m
      [36m>[39m
        [36m<section[39m
          [33mclass[39m=[32m"surface-section"[39m
        [36m>[39m
          [36m<header[39m
            [33mclass[39m=[32m"surface-section-head"[39m
          [36m>[39m
            [36m<h3>[39m
              [0mBRIEF[0m
            [36m</h3>[39m
            [36m<span[39m
              [33mclass[39m=[32m"gadget-chip gadget-chip-egress"[39m
              [33mdata-scope[39m=[32m"local"[39m
              [33mtitle[39m=[32m"The brief is built from this desk's own records."[39m
            [36m>[39m
              [0mTHIS DEVICE[0m
            [36m</span>[39m
            [36m<button[39m
              [33mclass[39m=[32m"btn btn--ghost btn--sm "[39m
              [33mdata-testid[39m=[32m"arrival-brief-generate"[39m
              [33mtype[39m=[32m"button"[39m
            [36m>[39m
              [0mGenerate[0m
            [36m</button>[39m
          [36m</header>[39m
          [36m<span[39m
            [33mclass[39m=[32m"arrival-brief-empty"[39m
          [36m>[39m
            [0mNo brief yet[0m
          [36m</span>[39m
        [36m</section>[39m
      [36m</div>[39m
      [36m<footer[39m
        [33mclass[39m=[32m"arrival-capture-bar"[39m
        [33mdata-testid[39m=[32m"arrival-capture-bar"[39m
      [36m>[39m
        [36m<span[39m
          [33mclass[39m=[32m"arrival-capture-talk"[39m
        [36m/>[39m
        [36m<button[39m
          [33mclass[39m=[32m"btn btn--ghost "[39m
          [33mdata-testid[39m=[32m"arrival-develop-thought"[39m
          [33mtype[39m=[32m"button"[39m
        [36m>[39m
          [0mWrite a thought[0m
        [36m</button>[39m
        [36m<button[39m
          [33mclass[39m=[32m"btn btn--ghost "[39m
          [33mdata-testid[39m=[32m"arrival-record-meeting"[39m
          [33mtype[39m=[32m"button"[39m
        [36m>[39m
          [0mRecord meeting[0m
        [36m</button>[39m
        [36m<button[39m
          [33mclass[39m=[32m"btn btn--ghost "[39m
          [33mdata-testid[39m=[32m"arrival-schedule"[39m
          [33mtype[39m=[32m"button"[39m
        [36m>[39m
          [0mSchedule[0m
        [36m</button>[39m
      [36m</footer>[39m
    [36m</div>[39m
  [36m</div>[39m
[36m</body>[39m

Ignored nodes: comments, script, style
[36m<body>[39m
  [36m<div>[39m
    [36m<div[39m
      [33mclass[39m=[32m"chair"[39m
      [33mdata-testid[39m=[32m"chair"[39m
    [36m>[39m
      [36m<div[39m
        [33mclass[39m=[32m"arrival-headline"[39m
        [33mdata-testid[39m=[32m"arrival-headline"[39m
      [36m>[39m
        [36m<h1[39m
          [33mclass[39m=[32m"arrival-display arrival-display--muted"[39m
          [33mdata-testid[39m=[32m"arrival-display"[39m
        [36m>[39m
          [0mNothing needs you[0m
        [36m</h1>[39m
        [36m<div[39m
          [33mclass[39m=[32m"arrival-head-tokens"[39m
          [33mdata-testid[39m=[32m"arrival-head-tokens"[39m
        [36m>[39m
          [36m<span[39m
            [33mclass[39m=[32m"arrival-next"[39m
            [33mdata-testid[39m=[32m"arrival-no-calendar"[39m
          [36m>[39m
            [36m<span[39m
              [33mclass[39m=[32m"arrival-no-calendar-token"[39m
            [36m>[39m
              [0mNO CALENDAR[0m
            [36m</span>[39m
            [0m [0m
            [36m<button[39m
              [33mclass[39m=[32m"btn btn--ghost btn--sm "[39m
              [33mdata-testid[39m=[32m"arrival-connect-calendar"[39m
              [33mtype[39m=[32m"button"[39m
            [36m>[39m
              [0mConnect calendar[0m
            [36m</button>[39m
          [36m</span>[39m
        [36m</div>[39m
      [36m</div>[39m
      [36m<div[39m
        [33mdata-testid[39m=[32m"arrival-brief"[39m
      [36m>[39m
        [36m<section[39m
          [33mclass[39m=[32m"surface-section"[39m
        [36m>[39m
          [36m<header[39m
            [33mclass[39m=[32m"surface-section-head"[39m
          [36m>[39m
            [36m<h3>[39m
              [0mBRIEF[0m
            [36m</h3>[39m
            [36m<span[39m
              [33mclass[39m=[32m"gadget-chip gadget-chip-egress"[39m
              [33mdata-scope[39m=[32m"local"[39m
              [33mtitle[39m=[32m"The brief is built from this desk's own records."[39m
            [36m>[39m
              [0mTHIS DEVICE[0m
            [36m</span>[39m
            [36m<button[39m
              [33mclass[39m=[32m"btn btn--ghost btn--sm "[39m
              [33mdata-testid[39m=[32m"arrival-brief-generate"[39m
              [33mtype[39m=[32m"button"[39m
            [36m>[39m
              [0mGenerate[0m
            [36m</button>[39m
          [36m</header>[39m
          [36m<span[39m
            [33mclass[39m=[32m"arrival-brief-empty"[39m
          [36m>[39m
            [0mNo brief yet[0m
          [36m</span>[39m
        [36m</section>[39m
      [36m</div>[39m
      [36m<footer[39m
        [33mclass[39m=[32m"arrival-capture-bar"[39m
        [33mdata-testid[39m=[32m"arrival-capture-bar"[39m
      [36m>[39m
        [36m<span[39m
          [33mclass[39m=[32m"arrival-capture-talk"[39m
        [36m/>[39m
        [36m<button[39m
          [33mclass[39m=[32m"btn btn--ghost "[39m
          [33mdata-testid[39m=[32m"arrival-develop-thought"[39m
          [33mtype[39m=[32m"button"[39m
        [36m>[39m
          [0mWrite a thought[0m
        [36m</button>[39m
        [36m<button[39m
          [33mclass[39m=[32m"btn btn--ghost "[39m
          [33mdata-testid[39m=[32m"arrival-record-meeting"[39m
          [33mtype[39m=[32m"button"[39m
        [36m>[39m
          [0mRecord meeting[0m
        [36m</button>[39m
        [36m<button[39m
          [33mclass[39m=[32m"btn btn--ghost "[39m
          [33mdata-testid[39m=[32m"arrival-schedule"[39m
          [33mtype[39m=[32m"button"[39m
        [36m>[39m
          [0mSchedule[0m
        [36m</button>[39m
      [36m</footer>[39m
    [36m</div>[39m
  [36m</div>[39m
[36m</body>[39m
 ❯ waitForWrapper node_modules/@testing-library/dom/dist/wait-for.js:163:27
 ❯ node_modules/@testing-library/dom/dist/query-helpers.js:86:33
 ❯ src/components/aftercarePlacement.test.tsx:113:31
    111|       </>,
    112|     );
    113|     const slot = await screen.findByTestId("arrival-aftercare-slot");
       |                               ^
    114|
    115|     publish();

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[1/8]⎯

 FAIL  src/components/aftercarePlacement.test.tsx > PHILO-6-03 aftercare rendered placement > renders into the actual active SurfaceWindowHost slot
AssertionError: expected null to be truthy

Ignored nodes: comments, script, style
[36m<html>[39m
  [36m<head />[39m
  [36m<body>[39m
    [36m<div[39m
      [33mdata-aftercare-slot[39m=[32m"before-capture"[39m
    [36m/>[39m
    [36m<div>[39m
      [36m<aside[39m
        [33maria-label[39m=[32m"Meeting aftercare"[39m
        [33mclass[39m=[32m"ambient-preview ambient-aftercare"[39m
        [33mstyle[39m=[32m"bottom: 104px;"[39m
      [36m>[39m
        [36m<span[39m
          [33mclass[39m=[32m"signal-eyebrow"[39m
        [36m>[39m
          [0mMeeting ready[0m
        [36m</span>[39m
        [36m<strong>[39m
          [0mArchitecture review[0m
        [36m</strong>[39m
        [36m<p>[39m
          [0m3 open[0m
        [36m</p>[39m
        [36m<div[39m
          [33mclass[39m=[32m"button-row"[39m
        [36m>[39m
          [36m<button[39m
            [33mclass[39m=[32m"btn btn--primary btn--sm "[39m
            [33mtype[39m=[32m"button"[39m
          [36m>[39m
            [0mOpen proposals[0m
          [36m</button>[39m
          [36m<button[39m
            [33mclass[39m=[32m"btn btn--ghost btn--sm "[39m
            [33mtype[39m=[32m"button"[39m
          [36m>[39m
            [0mDismiss[0m
          [36m</button>[39m
        [36m</div>[39m
      [36m</aside>[39m
      [36m<div[39m
        [33maria-label[39m=[32m"Meetings"[39m
        [33mclass[39m=[32m"desk-surface-window desk-window desk-window-shell is-floating is-front"[39m
        [33mid[39m=[32m"test-aftercare-window"[39m
        [33mrole[39m=[32m"region"[39m
        [33mstyle[39m=[32m"z-index: 42; opacity: 1; transform: none; top: 64px; left: 10px; width: 400px; right: auto; bottom: auto; height: 480px; max-height: none;"[39m
        [33mtabindex[39m=[32m"-1"[39m
      [36m>[39m
        [36m<header[39m
          [33mclass[39m=[32m"desk-pullout-head desk-window-handle"[39m
        [36m>[39m
          [36m<span[39m
            [33mclass[39m=[32m"desk-traffic"[39m
          [36m>[39m
            [36m<button[39m
              [33maria-label[39m=[32m"Close Meetings"[39m
              [33mclass[39m=[32m"btn--chrome desk-light desk-light-close"[39m
              [33mtype[39m=[32m"button"[39m
            [36m>[39m
              [36m<svg[39m
                [33maria-hidden[39m=[32m"true"[39m
                [33mfill[39m=[32m"none"[39m
                [33mstroke[39m=[32m"currentColor"[39m
                [33mstroke-linecap[39m=[32m"round"[39m
                [33mstroke-linejoin[39m=[32m"round"[39m
                [33mstroke-width[39m=[32m"1.3"[39m
                [33mviewBox[39m=[32m"0 0 14 14"[39m
              [36m>[39m
                [36m<path[39m
                  [33md[39m=[32m"M3.6 3.6l6.8 6.8M10.4 3.6l-6.8 6.8"[39m
                [36m/>[39m
              [36m</svg>[39m
            [36m</button>[39m
            [36m<button[39m
              [33maria-label[39m=[32m"Minimize Meetings"[39m
              [33mclass[39m=[32m"btn--chrome desk-light desk-light-min"[39m
              [33mtype[39m=[32m"button"[39m
            [36m>[39m
              [36m<svg[39m
                [33maria-hidden[39m=[32m"true"[39m
                [33mfill[39m=[32m"none"[39m
                [33mstroke[39m=[32m"currentColor"[39m
                [33mstroke-linecap[39m=[32m"round"[39m
                [33mstroke-linejoin[39m=[32m"round"[39m
                [33mstroke-width[39m=[32m"1.3"[39m
                [33mviewBox[39m=[32m"0 0 14 14"[39m
              [36m>[39m
                [36m<path[39m
                  [33md[39m=[32m"M3 7h8"[39m
                [36m/>[39m
              [36m</svg>[39m
            [36m</button>[39m
            [36m<button[39m
              [33maria-label[39m=[32m"Maximize Meetings"[39m
              [33mclass[39m=[32m"btn--chrome desk-light desk-light-max"[39m
              [33mtype[39m=[32m"button"[39m
            [36m>[39m
              [36m<svg[39m
                [33maria-hidden[39m=[32m"true"[39m
                [33mfill[39m=[32m"none"[39m
                [33mstroke[39m=[32m"currentColor"[39m
                [33mstroke-linecap[39m=[32m"round"[39m
                [33mstroke-linejoin[39m=[32m"round"[39m
                [33mstroke-width[39m=[32m"1.3"[39m
                [33mviewBox[39m=[32m"0 0 14 14"[39m
              [36m>[39m
                [36m<path[39m
                  [33md[39m=[32m"M7 3v8M3 7h8"[39m
                [36m/>[39m
              [36m</svg>[39m
            [36m</button>[39m
          [36m</span>[39m
          [36m<span[39m
            [33mclass[39m=[32m"desk-pullout-title desk-window-title"[39m
          [36m>[39m
            [0mMeetings[0m
          [36m</span>[39m
        [36m</header>[39m
        [36m<div[39m
          [33mclass[39m=[32m"desk-surface-body"[39m
        [36m>[39m
          [36m<p>[39m
            [0mWindow body[0m
          [36m</p>[39m
        [36m</div>[39m
        [36m<footer[39m
          [33mclass[39m=[32m"desk-surface-foot surface-footer"[39m
        [36m/>[39m
        [36m<span[39m
          [33maria-hidden[39m=[32m"true"[39m
          [33mclass[39m=[32m"desk-window-grip"[39m
        [36m/>[39m
        [36m<span[39m
          [33maria-hidden[39m=[32m"true"[39m
          [33mclass[39m=[32m"desk-window-edge desk-window-edge-l"[39m
        [36m/>[39m
        [36m<span[39m
          [33maria-hidden[39m=[32m"true"[39m
          [33mclass[39m=[32m"desk-window-edge desk-window-edge-r"[39m
        [36m/>[39m
        [36m<span[39m
          [33maria-hidden[39m=[32m"true"[39m
          [33mclass[39m=[32m"desk-window-edge desk-window-edge-b"[39m
        [36m/>[39m
        [36m<span[39m
          [33maria-hidden[39m=[32m"true"[39m
          [33mclass[39m=[32m"desk-window-corner desk-window-corner-bl"[39m
        [36m/>[39m
      [36m</div>[39m
    [36m</div>[39m
  [36m</body>[39m
[36m</html>[39m...

- Expected:
true

+ Received:
null

 ❯ src/components/aftercarePlacement.test.tsx:150:9
    148|       expect(
    149|         container.querySelector('[data-aftercare-window-slot="top"] as…
    150|       ).toBeTruthy(),
       |         ^
    151|     );
    152|     const slot = container.querySelector('[data-aftercare-window-slot=…
 ❯ runWithExpensiveErrorDiagnosticsDisabled node_modules/@testing-library/dom/dist/config.js:47:12
 ❯ checkCallback node_modules/@testing-library/dom/dist/wait-for.js:124:77
 ❯ Timeout.checkRealTimersCallback node_modules/@testing-library/dom/dist/wait-for.js:118:16

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[2/8]⎯

 FAIL  src/components/aftercarePlacement.test.tsx > PHILO-6-03 aftercare rendered placement > renders into the actual Floor list host when no window is open
AssertionError: expected null to be truthy

Ignored nodes: comments, script, style
[36m<html>[39m
  [36m<head />[39m
  [36m<body>[39m
    [36m<div>[39m
      [36m<aside[39m
        [33maria-label[39m=[32m"Meeting aftercare"[39m
        [33mclass[39m=[32m"ambient-preview ambient-aftercare"[39m
        [33mstyle[39m=[32m"bottom: 104px;"[39m
      [36m>[39m
        [36m<span[39m
          [33mclass[39m=[32m"signal-eyebrow"[39m
        [36m>[39m
          [0mMeeting ready[0m
        [36m</span>[39m
        [36m<strong>[39m
          [0mArchitecture review[0m
        [36m</strong>[39m
        [36m<p>[39m
          [0m3 open[0m
        [36m</p>[39m
        [36m<div[39m
          [33mclass[39m=[32m"button-row"[39m
        [36m>[39m
          [36m<button[39m
            [33mclass[39m=[32m"btn btn--primary btn--sm "[39m
            [33mtype[39m=[32m"button"[39m
          [
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-09-25T04:44:26Z

- **Command:** `bash -c set -uo pipefail
export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH
export HOME=$(mktemp -d)
export NO_COLOR=1
export DEBUG_PRINT_LIMIT=300
cd /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo603-red-z5r_bw9b/web
./node_modules/.bin/vitest list src/components/AmbientLayer.test.tsx src/components/aftercarePlacement.test.tsx
./node_modules/.bin/vitest run src/components/AmbientLayer.test.tsx src/components/aftercarePlacement.test.tsx --maxWorkers=2 > /Users/karol/dev/tools/wt-philo-6-03/docs/internal/philo/phase-6/toast/placement-proof/red-rendered.txt 2>&1
result=$?
cat /Users/karol/dev/tools/wt-philo-6-03/docs/internal/philo/phase-6/toast/placement-proof/red-rendered.txt
exit $result`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text
src/components/AmbientLayer.test.tsx > posture-aware dictation preview gate > Secure and Normal-with-preference: the hub-armed preview gates before any commit
src/components/AmbientLayer.test.tsx > posture-aware dictation preview gate > Type it commits exactly once, by token only, and closes the gate
src/components/AmbientLayer.test.tsx > posture-aware dictation preview gate > Discard burns the preview without ever committing
src/components/AmbientLayer.test.tsx > posture-aware dictation preview gate > a failed commit keeps the words and the gate for an explicit retry
src/components/AmbientLayer.test.tsx > posture-aware dictation preview gate > YOLO and Normal-without-preference: no hub frame means no HoldSpeak prompt
src/components/AmbientLayer.test.tsx > meeting aftercare counts > renders only nonzero count tokens (0 open, 0 decided)
src/components/AmbientLayer.test.tsx > meeting aftercare counts > renders only nonzero count tokens (3 open, 0 decided)
src/components/AmbientLayer.test.tsx > meeting aftercare counts > renders only nonzero count tokens (0 open, 2 decided)
src/components/AmbientLayer.test.tsx > meeting aftercare counts > renders only nonzero count tokens (3 open, 2 decided)
src/components/aftercarePlacement.test.tsx > PHILO-6-03 aftercare rendered placement > publishes into the actual ChairHome slot and Dismiss clears it at 1440
src/components/aftercarePlacement.test.tsx > PHILO-6-03 aftercare rendered placement > publishes into the actual ChairHome slot and Dismiss clears it at 393
src/components/aftercarePlacement.test.tsx > PHILO-6-03 aftercare rendered placement > renders into the actual active SurfaceWindowHost slot
src/components/aftercarePlacement.test.tsx > PHILO-6-03 aftercare rendered placement > renders into the actual Floor list host when no window is open
src/components/aftercarePlacement.test.tsx > PHILO-6-03 aftercare rendered placement > keeps the fixed fallback only when the spatial Floor has no slot
src/components/aftercarePlacement.test.tsx > PHILO-6-03 aftercare rendered placement > scrolls an obscured phone slot once and does not scroll a desktop slot
src/components/aftercarePlacement.test.tsx > PHILO-6-03 aftercare rendered placement > scrolls an off-Arrival phone slot once even when it is already visible
src/components/aftercarePlacement.test.tsx > PHILO-6-03 aftercare rendered placement > scrolls an active window phone slot once
src/components/aftercarePlacement.test.tsx > PHILO-6-03 aftercare rendered placement > does not move the owner while a field has focus

 RUN  v4.1.9 /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo603-red-z5r_bw9b/web

 ❯ src/components/aftercarePlacement.test.tsx (9 tests | 8 failed) 8233ms
     × publishes into the actual ChairHome slot and Dismiss clears it at 1440 1022ms
     × publishes into the actual ChairHome slot and Dismiss clears it at 393 1006ms
     × renders into the actual active SurfaceWindowHost slot 1137ms
     × renders into the actual Floor list host when no window is open 1018ms
     × scrolls an obscured phone slot once and does not scroll a desktop slot 1006ms
     × scrolls an off-Arrival phone slot once even when it is already visible 1006ms
     × scrolls an active window phone slot once 1019ms
     × does not move the owner while a field has focus 1010ms

⎯⎯⎯⎯⎯⎯⎯ Failed Tests 8 ⎯⎯⎯⎯⎯⎯⎯

 FAIL  src/components/aftercarePlacement.test.tsx > PHILO-6-03 aftercare rendered placement > publishes into the actual ChairHome slot and Dismiss clears it at 1440
 FAIL  src/components/aftercarePlacement.test.tsx > PHILO-6-03 aftercare rendered placement > publishes into the actual ChairHome slot and Dismiss clears it at 393
TestingLibraryElementError: Unable to find an element by: [data-testid="arrival-aftercare-slot"]

Ignored nodes: comments, script, style
[36m<body>[39m
  [36m<div>[39m
    [36m<div[39m
      [33mclass[39m=[32m"chair"[39m
      [33mdata-testid[39m=[32m"chair"[39m
    [36m>[39m
      [36m<div[39m
        [33mclass[39m=[32m"arrival-headline"[39m
        [33mdata-testid[39m=[32m"arrival-headline"[39m
      [36m...

Ignored nodes: comments, script, style
[36m<body>[39m
  [36m<div>[39m
    [36m<div[39m
      [33mclass[39m=[32m"chair"[39m
      [33mdata-testid[39m=[32m"chair"[39m
    [36m>[39m
      [36m<div[39m
        [33mclass[39m=[32m"arrival-headline"[39m
        [33mdata-testid[39m=[32m"arrival-headline"[39m
      [36m...
 ❯ waitForWrapper node_modules/@testing-library/dom/dist/wait-for.js:163:27
 ❯ node_modules/@testing-library/dom/dist/query-helpers.js:86:33
 ❯ src/components/aftercarePlacement.test.tsx:114:31
    112|       </>,
    113|     );
    114|     const slot = await screen.findByTestId("arrival-aftercare-slot");
       |                               ^
    115|
    116|     publish();

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[1/8]⎯

 FAIL  src/components/aftercarePlacement.test.tsx > PHILO-6-03 aftercare rendered placement > renders into the actual active SurfaceWindowHost slot
AssertionError: expected null to be truthy

Ignored nodes: comments, script, style
[36m<html>[39m
  [36m<head />[39m
  [36m<body>[39m
    [36m<div[39m
      [33mdata-aftercare-slot[39m=[32m"before-capture"[39m
    [36m/>[39m
    [36m<div>[39m
      [36m<aside[39m
        [33maria-label[39m=[32m"Meeting aftercare"[39m
        [33mclass[39m=[32m"ambient-prev...

- Expected:
true

+ Received:
null

 ❯ src/components/aftercarePlacement.test.tsx:154:9
    152|       expect(
    153|         container.querySelector('[data-aftercare-window-slot="top"] as…
    154|       ).toBeTruthy(),
       |         ^
    155|     );
    156|     const slot = container.querySelector('[data-aftercare-window-slot=…
 ❯ runWithExpensiveErrorDiagnosticsDisabled node_modules/@testing-library/dom/dist/config.js:47:12
 ❯ checkCallback node_modules/@testing-library/dom/dist/wait-for.js:124:77
 ❯ Timeout.checkRealTimersCallback node_modules/@testing-library/dom/dist/wait-for.js:118:16

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[2/8]⎯

 FAIL  src/components/aftercarePlacement.test.tsx > PHILO-6-03 aftercare rendered placement > renders into the actual Floor list host when no window is open
AssertionError: expected null to be truthy

Ignored nodes: comments, script, style
[36m<html>[39m
  [36m<head />[39m
  [36m<body>[39m
    [36m<div>[39m
      [36m<aside[39m
        [33maria-label[39m=[32m"Meeting aftercare"[39m
        [33mclass[39m=[32m"ambient-preview ambient-aftercare"[39m
        [33mstyle[39m=[32m"bottom: 104px;"[39m
      [36m>[39m
  ...

- Expected:
true

+ Received:
null

 ❯ src/components/aftercarePlacement.test.tsx:174:9
    172|       expect(
    173|         container.querySelector('[data-aftercare-floor-slot="top"] asi…
    174|       ).toBeTruthy(),
       |         ^
    175|     );
    176|     const slot = container.querySelector('[data-aftercare-floor-slot="…
 ❯ runWithExpensiveErrorDiagnosticsDisabled node_modules/@testing-library/dom/dist/config.js:47:12
 ❯ checkCallback node_modules/@testing-library/dom/dist/wait-for.js:124:77
 ❯ Timeout.checkRealTimersCallback node_modules/@testing-library/dom/dist/wait-for.js:118:16

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[3/8]⎯

 FAIL  src/components/aftercarePlacement.test.tsx > PHILO-6-03 aftercare rendered placement > scrolls an obscured phone slot once and does not scroll a desktop slot
AssertionError: expected "vi.fn()" to be called 1 times, but got 0 times

Ignored nodes: comments, script, style
[36m<html>[39m
  [36m<head />[39m
  [36m<body>[39m
    [36m<div[39m
      [33mdata-aftercare-slot[39m=[32m"before-capture"[39m
    [36m/>[39m
    [36m<footer[39m
      [33mdata-testid[39m=[32m"arrival-capture-bar"[39m
    [36m/>[39m
    [36m<div>[39m
      [36m<aside[39m
  ...
 ❯ src/components/aftercarePlacement.test.tsx:233:40
    231|     publish("meeting-placement-phone", "Architecture review phone");
    232|
    233|     await waitFor(() => expect(scroll).toHaveBeenCalledTimes(1));
       |                                        ^
    234|     expect(scroll).toHaveBeenCalledWith({ block: "nearest", behavior: …
    235|     publish("meeting-placement-phone", "Architecture review phone");
 ❯ runWithExpensiveErrorDiagnosticsDisabled node_modules/@testing-library/dom/dist/config.js:47:12
 ❯ checkCallback node_modules/@testing-library/dom/dist/wait-for.js:124:77
 ❯ Timeout.checkRealTimersCallback node_modules/@testing-library/dom/dist/wait-for.js:118:16

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[4/8]⎯

 FAIL  src/components/aftercarePlacement.test.tsx > PHILO-6-03 aftercare rendered placement > scrolls an off-Arrival phone slot once even when it is already visible
AssertionError: expected null to be truthy

Ignored nodes: comments, script, style
[36m<html>[39m
  [36m<head />[39m
  [36m<body>[39m
    [36m<div>[39m
      [36m<div[39m
        [33mclass[39m=[32m"desk-listmode"[39m
      [36m>[39m
        [36m<section[39m
          [33maria-labelledby[39m=[32m"desk-list-title"[39m
          [33mclass[39m=[32m"desk-list-f...

- Expected:
true

+ Received:
null

 ❯ src/components/aftercarePlacement.test.tsx:264:21
    262|         '[data-aftercare-floor-slot="top"]',
    263|       );
    264|       expect(found).toBeTruthy();
       |                     ^
    265|       return found!;
    266|     });
 ❯ runWithExpensiveErrorDiagnosticsDisabled node_modules/@testing-library/dom/dist/config.js:47:12
 ❯ checkCallback node_modules/@testing-library/dom/dist/wait-for.js:124:77
 ❯ Timeout.checkRealTimersCallback node_modules/@testing-library/dom/dist/wait-for.js:118:16

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[5/8]⎯

 FAIL  src/components/aftercarePlacement.test.tsx > PHILO-6-03 aftercare rendered placement > scrolls an active window phone slot once
AssertionError: expected null to be truthy

Ignored nodes: comments, script, style
[36m<html>[39m
  [36m<head />[39m
  [36m<body>[39m
    [36m<div[39m
      [33mdata-aftercare-slot[39m=[32m"before-capture"[39m
    [36m/>[39m
    [36m<div>[39m
      [36m<div[39m
        [33maria-label[39m=[32m"Meetings"[39m
        [33mclass[39m=[32m"desk-surface-window des...

- Expected:
true

+ Received:
null

 ❯ src/components/aftercarePlacement.test.tsx:303:21
    301|         '[data-aftercare-window-slot="top"]',
    302|       );
    303|       expect(found).toBeTruthy();
       |                     ^
    304|       return found!;
    305|     });
 ❯ runWithExpensiveErrorDiagnosticsDisabled node_modules/@testing-library/dom/dist/config.js:47:12
 ❯ checkCallback node_modules/@testing-library/dom/dist/wait-for.js:124:77
 ❯ Timeout.checkRealTimersCallback node_modules/@testing-library/dom/dist/wait-for.js:118:16

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[6/8]⎯

 FAIL  src/components/aftercarePlacement.test.tsx > PHILO-6-03 aftercare rendered placement > does not move the owner while a field has focus
AssertionError: expected null to be truthy

Ignored nodes: comments, script, style
[36m<html>[39m
  [36m<head />[39m
  [36m<body>[39m
    [36m<div[39m
      [33mdata-aftercare-slot[39m=[32m"before-capture"[39m
    [36m/>[39m
    [36m<footer[39m
      [33mdata-testid[39m=[32m"arrival-capture-bar"[39m
    [36m/>[39m
    [36m<input />[39m
    [36m<div>[39m
 ...

- Expected:
true

+ Received:
null

 ❯ src/components/aftercarePlacement.test.tsx:356:61
    354|     publish();
    355|
    356|     await waitFor(() => expect(slot.querySelector("aside")).toBeTruthy…
       |                                                             ^
    357|     expect(scroll).not.toHaveBeenCalled();
    358|   });
 ❯ runWithExpensiveErrorDiagnosticsDisabled node_modules/@testing-library/dom/dist/config.js:47:12
 ❯ checkCallback node_modules/@testing-library/dom/dist/wait-for.js:124:77
 ❯ Timeout.checkRealTimersCallback node_modules/@testing-library/dom/dist/wait-for.js:118:16

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[7/8]⎯


 Test Files  1 failed | 1 passed (2)
      Tests  8 failed | 10 passed (18)
   Start at  22:44:28
   Duration  9.63s (transform 924ms, setup 125ms, import 1.36s, tests 8.39s, environment 374ms)
```

### Captured run — 2026-09-25T04:45:25Z

- **Command:** `bash -c set -uo pipefail
export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH
export HOME=$(mktemp -d)
export NO_COLOR=1
export DEBUG_PRINT_LIMIT=300
cd web
./node_modules/.bin/vitest list src/components/AmbientLayer.test.tsx src/components/aftercarePlacement.test.tsx src/desk/chair src/desk/pullouts src/desk/__tests__/shell.test.tsx src/desk/DeskApp.test.tsx > ../docs/internal/philo/phase-6/toast/placement-proof/scoped-collect.txt
./node_modules/.bin/vitest run src/components/AmbientLayer.test.tsx src/components/aftercarePlacement.test.tsx src/desk/chair src/desk/pullouts src/desk/__tests__/shell.test.tsx src/desk/DeskApp.test.tsx --maxWorkers=2 > ../docs/internal/philo/phase-6/toast/placement-proof/scoped-run.txt 2>&1
result=$?
cat ../docs/internal/philo/phase-6/toast/placement-proof/scoped-run.txt
exit $result`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-6-03/web

⎯⎯⎯⎯⎯⎯ Unhandled Errors ⎯⎯⎯⎯⎯⎯

Vitest caught 1 unhandled error during the test run.
This might cause false positive tests. Resolve unhandled errors to make sure your tests are not affected.

⎯⎯⎯⎯ Unhandled Rejection ⎯⎯⎯⎯⎯
TypeError: currentBucket is not iterable
 ❯ mergeRefreshItems src/desk/store/dataSlice.ts:191:26
    189|       const protectedItems = new Map<string, IdentifiedItem>();
    190|       const kindName = String(kind);
    191|       for (const item of currentBucket) {
       |                          ^
    192|         const id = item.id;
    193|         const key = writeKey(kindName, id);
 ❯ runRefresh src/desk/store/dataSlice.ts:246:25

This error originated in "src/desk/chair/arrivalSummaryRun.test.tsx" test file. It doesn't mean the error was thrown inside the file itself, but while it was running.
The latest test that might've caused the error is "shows a 409 as ONE short refusal fact, the reason on its title". It might mean one of the following:
- The error was thrown, while Vitest was running this test.
- If the error occurred after the test had been completed, this was the last documented test before it was thrown.
⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯


 Test Files  31 passed (31)
      Tests  223 passed (223)
     Errors  1 error
   Start at  22:45:29
   Duration  11.49s (transform 1.43s, setup 1.30s, import 5.57s, tests 7.88s, environment 5.57s)
```

### Captured run — 2026-09-25T04:45:03Z

- **Command:** `bash -c set -euo pipefail
export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH
export HOME=$(mktemp -d)
export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright
export HOLDSPEAK_EVIDENCE_WRITE=1
cd /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo603-red-z5r_bw9b
uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.philo603.toast.arrival --brain astra --viewport 393 --engine replayed --no-build --out /Users/karol/dev/tools/wt-philo-6-03/pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/red/`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text
PASS: live
BRAIN: astra
SOURCE:  dirty=False
CONTRACT: rig=1.3.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-C2JQr2p9.js'] hub=http://127.0.0.1:62854 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-kzg_9g2k/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j6
VERDICT: fail terminal=settled
EVIDENCE: ['/Users/karol/dev/tools/wt-philo-6-03/pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/red/20260925T044503Z-case.philo603.toast.arrival-astra-393/before.png', '/Users/karol/dev/tools/wt-philo-6-03/pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/red/20260925T044503Z-case.philo603.toast.arrival-astra-393/after.png']
NOTE: predicate: the card is not rendered inside its declared slot '[data-testid=arrival-aftercare-slot]': {'selector': '[data-testid=arrival-aftercare-slot]', 'present': False, 'contains_card': False}
NOTE: a nonzero diff with the wrong result is a finding, not a pass (changed: ['api_reads', 'attrs', 'document_text_len', 'document_text_sha256', 'rect', 'target_present', 'text', 'visible']).
```

### Captured run — 2026-09-25T04:46:45Z

- **Command:** `bash -c set -euo pipefail
export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH
export HOME=$(mktemp -d)
uv run --extra dev pytest --collect-only -q tests/unit/test_philo_graph_atlas.py
uv run --extra dev pytest -q tests/unit/test_philo_graph_atlas.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text
tests/unit/test_philo_graph_atlas.py::test_every_atlas_file_is_read
tests/unit/test_philo_graph_atlas.py::test_schema_is_a_valid_2020_12_schema
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas-phase3.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase3.json]
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas.json]
tests/unit/test_philo_graph_atlas.py::test_ids_are_unique
tests/unit/test_philo_graph_atlas.py::test_every_case_state_id_resolves
tests/unit/test_philo_graph_atlas.py::test_every_case_reference_inside_the_atlas_resolves
tests/unit/test_philo_graph_atlas.py::test_every_clock_a_case_uses_is_declared
tests/unit/test_philo_graph_atlas.py::test_every_applicable_case_carries_one_trigger
tests/unit/test_philo_graph_atlas.py::test_no_timer_edge_is_triggered_by_a_substitute_button
tests/unit/test_philo_graph_atlas.py::test_every_api_setup_step_exists_in_the_generated_openapi
tests/unit/test_philo_graph_atlas.py::test_every_fixture_step_exists_and_hashes_as_claimed
tests/unit/test_philo_graph_atlas.py::test_every_phase1_reference_resolves_to_a_record
tests/unit/test_philo_graph_atlas.py::test_every_selected_job_has_an_applicable_case_except_j8
tests/unit/test_philo_graph_atlas.py::test_every_brief_family_is_present
tests/unit/test_philo_graph_atlas.py::test_quiet_is_never_an_attention_state
tests/unit/test_philo_graph_atlas.py::test_face_cases_carry_both_ruled_viewports
tests/unit/test_philo_graph_atlas.py::test_unexercised_states_name_a_mechanism_and_a_cost
tests/unit/test_philo_graph_atlas.py::test_source_commit_is_the_revision_the_atlas_was_derived_from
tests/unit/test_philo_graph_atlas.py::test_every_applicable_predicate_is_a_kind_the_rig_implements
tests/unit/test_philo_graph_atlas.py::test_every_predicate_observes_a_selector_or_a_route
tests/unit/test_philo_graph_atlas.py::test_protocol_predicates_ask_for_a_new_row
tests/unit/test_philo_graph_atlas.py::test_every_case_keeps_its_human_sentence
tests/unit/test_philo_graph_atlas.py::test_operation_siblings_use_headless_reads_and_canonical_steps
tests/unit/test_philo_graph_atlas.py::test_named_pair_observations_bind_their_read_arguments
tests/unit/test_philo_graph_atlas.py::test_all_handled_operation_maps_items_by_decision_source
tests/unit/test_philo_graph_atlas.py::test_breakage_cases_use_evening_wrapper_and_shelf_old_item
tests/unit/test_philo_graph_atlas.py::test_every_ui_action_is_one_the_rig_implements
tests/unit/test_philo_graph_atlas.py::test_every_boundary_names_its_substitution
tests/unit/test_philo_graph_atlas.py::test_summary_cases_use_the_retained_architect_import_fixture
tests/unit/test_philo_graph_atlas.py::test_summary_run_cases_have_one_run_trigger
tests/unit/test_philo_graph_atlas.py::test_summary_running_reads_the_claimed_job_wire_status
tests/unit/test_philo_graph_atlas.py::test_summary_queued_reads_the_run_admission_response
tests/unit/test_philo_graph_atlas.py::test_summary_preconditions_do_not_require_future_or_consumed_run_state
tests/unit/test_philo_graph_atlas.py::test_summary_state_reads_do_not_require_a_new_row_after_setup_run
tests/unit/test_philo_graph_atlas.py::test_summary_manual_retry_requires_failed_producer_and_current_route
tests/unit/test_philo_graph_atlas.py::test_summary_planned_host_cases_check_real_text_and_control_ownership
tests/unit/test_philo_graph_atlas.py::test_summary_failure_cases_retain_reply_at_the_provider_boundary
tests/unit/test_philo_graph_atlas.py::test_summary_imports_wait_for_real_completion_and_retain_title
tests/unit/test_philo_graph_atlas.py::test_summary_arrival_observations_name_the_rendered_states
tests/unit/test_philo_graph_atlas.py::test_summary_models_window_closes_before_arrival_steps
tests/unit/test_philo_graph_atlas.py::test_summary_restart_proof_retains_summary_receipt_and_identity
tests/unit/test_philo_graph_atlas.py::test_summary_microphone_cases_keep_the_lawful_blocked_boundary
tests/unit/test_philo_graph_atlas.py::test_summary_cases_do_not_claim_the_old_pangram
tests/unit/test_philo_graph_atlas.py::test_summary_stop_cases_require_a_real_active_meeting
tests/unit/test_philo_graph_atlas.py::test_the_two_schemas_agree_on_the_case_contract
tests/unit/test_philo_graph_atlas.py::test_every_case_validates_against_the_graph_case_schema
tests/unit/test_philo_graph_atlas.py::test_the_graph_predicate_enum_does_not_outrun_the_rig
tests/unit/test_philo_graph_atlas.py::test_a_case_without_a_predicate_is_unreachable_with_a_reason
tests/unit/test_philo_graph_atlas.py::test_every_council_reading_names_its_sources
tests/unit/test_philo_graph_atlas.py::test_no_precondition_check_compares_two_snapshots
tests/unit/test_philo_graph_atlas.py::test_every_precondition_check_observes_a_selector_or_a_route
tests/unit/test_philo_graph_atlas.py::test_no_check_asserts_the_result_the_trigger_must_produce
tests/unit/test_philo_graph_atlas.py::test_every_protocol_field_path_with_a_placeholder_is_a_json_pointer
tests/unit/test_philo_graph_atlas.py::test_no_step_acts_on_a_root_placeholder
tests/unit/test_philo_graph_atlas.py::test_navigation_steps_carry_no_selector
tests/unit/test_philo_graph_atlas.py::test_every_click_and_fill_names_a_control
tests/unit/test_philo_graph_atlas.py::test_every_desk_face_case_crosses_the_gate_first
tests/unit/test_philo_graph_atlas.py::test_no_gate_case_crosses_the_gate_in_setup
tests/unit/test_philo_graph_atlas.py::test_gate_cases_check_the_gate_not_the_desk
tests/unit/test_philo_graph_atlas.py::test_every_captured_id_names_the_field_it_reads
tests/unit/test_philo_graph_atlas.py::test_same_day_generate_again_binds_returned_displayed_and_retained
tests/unit/test_philo_graph_atlas.py::test_no_populated_brief_case_reads_the_headline
tests/unit/test_philo_graph_atlas.py::test_the_brief_recipe_fence_refuses_its_mutations
tests/unit/test_philo_graph_atlas.py::test_the_populated_brief_predicate_needs_the_minted_row
tests/unit/test_philo_graph_atlas.py::test_j11_kept_verifies_the_saved_words_in_the_store
tests/unit/test_philo_graph_atlas.py::test_same_day_same_id_fails_a_different_id_by_machine
tests/unit/test_philo_graph_atlas.py::test_j10_retention_is_proven_after_another_reload
tests/unit/test_philo_graph_atlas.py::test_summary_failure_settings_reach_the_real_drainer_after_restart
tests/unit/test_philo_graph_atlas.py::test_summary_no_engine_absence_is_read_inside_the_existing_meetings_scope
tests/unit/test_philo_graph_atlas.py::test_summary_reload_reads_the_same_already_persisted_summary
tests/unit/test_philo_graph_atlas.py::test_summary_terminal_cases_read_durable_meeting_not_active_queue[case.j6.run_summary.intel_ready-/intel_job/status]
tests/unit/test_philo_graph_atlas.py::test_summary_terminal_cases_read_durable_meeting_not_active_queue[case.j6.run_summary.host_named-/run_receipt/attempts/0/host]
tests/unit/test_philo_graph_atlas.py::test_no_assignment_op_reads_refusal_code_separately_from_error
tests/unit/test_philo_graph_atlas.py::test_thought_op_save_starts_from_different_working_text
tests/unit/test_philo_graph_atlas.py::test_philo603_cases_use_the_real_summary_producer_and_surface_slots
tests/unit/test_philo_graph_atlas.py::test_philo603_placement_fence_rejects_fixed_card_and_overlap
tests/unit/test_philo_graph_atlas.py::test_philo603_placement_fence_accepts_flow_card_with_nine_point_clearance
tests/unit/test_philo_graph_atlas.py::test_philo603_placement_fence_checks_every_matching_clear_target

81 tests collected in 0.06s
.....F.................................................................. [ 88%]
.........                                                                [100%]
=================================== FAILURES ===================================
_________ test_every_source_reference_lands_on_its_symbol[atlas.json] __________

every_atlas = {'cases': [{'applicability': 'applicable', 'completion_bound_s': 20, 'edge_ids': ['edge.face.first_words_continue_late...son': 'the gate holds ONE capture state and ONE failure (web/src/desk/components/FirstWords.tsx:50, :51).'}, ...], ...}

    def test_every_source_reference_lands_on_its_symbol(every_atlas: dict) -> None:
        """A line number is evidence, not identity (brief section 1).
    
        The cited line must still hold the cited symbol, or the reference has
        drifted and the claim behind it is no longer proven.
        """
        problems: list[str] = []
        for state in every_atlas["states"]:
            for ref in state["sources"]:
                target = REPO / ref["path"]
                if not target.is_file():
                    problems.append(f"{state['id']}: missing file {ref['path']}")
                    continue
                lines = target.read_text(errors="replace").splitlines()
                if not 1 <= ref["line"] <= len(lines):
                    problems.append(
                        f"{state['id']}: {ref['path']}:{ref['line']} is past the end of the file"
                    )
                    continue
                line = lines[ref["line"] - 1]
                if ref["symbol"] not in line:
                    problems.append(
                        f"{state['id']}: {ref['path']}:{ref['line']} no longer holds "
                        f"{ref['symbol']!r} (line reads {line.strip()[:80]!r})"
                    )
>       assert not problems, "\n".join(problems)
E       AssertionError: state.meetings.transcription.present: web/src/desk/chair/ChairHome.tsx:2305 no longer holds 'hasTranscript' (line reads ': "NOT DRAINING"')
E       assert not ['state.meetings.transcription.present: web/src/desk/chair/ChairHome.tsx:2305 no longer holds \'hasTranscript\' (line reads \': "NOT DRAINING"\')']

tests/unit/test_philo_graph_atlas.py:279: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas.json]
1 failed, 80 passed in 0.73s
```

### Captured run — 2026-09-25T04:50:18Z

- **Command:** `bash -c set -euo pipefail; export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH; export HOME=$(mktemp -d); export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright; export HOLDSPEAK_EVIDENCE_WRITE=1; uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.philo603.toast.arrival --brain astra --viewport 393 --engine replayed --no-build --out pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text
PASS: live
BRAIN: astra
SOURCE: d1e355f2bfc4acbaa7ec3ea1a7a38f1c742ae1c4 dirty=True
CONTRACT: rig=1.3.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-Ba2NesdW.js'] hub=http://127.0.0.1:63165 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-wvw5cdy0/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j6
VERDICT: fail terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/20260925T045018Z-case.philo603.toast.arrival-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/20260925T045018Z-case.philo603.toast.arrival-astra-393/after.png']
NOTE: predicate: a covering element owns hit points: [{'x': 14, 'y': 644, 'owned': False, 'owner': 'div#desk-next > div.chair > footer.arrival-capture-bar'}, {'x': 14, 'y': 732, 'owned': False, 'owner': 'div#desk-next > div.desk-dock'}, {'x': 14, 'y': 820, 'owned': False, 'owner': 'div#desk-next > div.desk-dock > button.btn--chrome.desk-dock-launch'}]
NOTE: a nonzero diff with the wrong result is a finding, not a pass (changed: ['api_reads', 'attrs', 'document_text_len', 'document_text_sha256', 'rect', 'target_present', 'text', 'visible']).
```

### Captured run — 2026-09-25T04:54:04Z

- **Command:** `bash -c set -euo pipefail; export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH; export HOME=$(mktemp -d); uv run --extra dev pytest --collect-only -q tests/unit/test_philo_graph_atlas.py tests/unit/test_graph_walk_first_paint.py tests/unit/test_graph_walk_http_fault.py tests/unit/test_graph_walk_producer_clock.py; uv run --extra dev pytest -q tests/unit/test_philo_graph_atlas.py tests/unit/test_graph_walk_first_paint.py tests/unit/test_graph_walk_http_fault.py tests/unit/test_graph_walk_producer_clock.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text
tests/unit/test_philo_graph_atlas.py::test_every_atlas_file_is_read
tests/unit/test_philo_graph_atlas.py::test_schema_is_a_valid_2020_12_schema
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas-phase3.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase3.json]
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas.json]
tests/unit/test_philo_graph_atlas.py::test_ids_are_unique
tests/unit/test_philo_graph_atlas.py::test_every_case_state_id_resolves
tests/unit/test_philo_graph_atlas.py::test_every_case_reference_inside_the_atlas_resolves
tests/unit/test_philo_graph_atlas.py::test_every_clock_a_case_uses_is_declared
tests/unit/test_philo_graph_atlas.py::test_every_applicable_case_carries_one_trigger
tests/unit/test_philo_graph_atlas.py::test_no_timer_edge_is_triggered_by_a_substitute_button
tests/unit/test_philo_graph_atlas.py::test_every_api_setup_step_exists_in_the_generated_openapi
tests/unit/test_philo_graph_atlas.py::test_every_fixture_step_exists_and_hashes_as_claimed
tests/unit/test_philo_graph_atlas.py::test_every_phase1_reference_resolves_to_a_record
tests/unit/test_philo_graph_atlas.py::test_every_selected_job_has_an_applicable_case_except_j8
tests/unit/test_philo_graph_atlas.py::test_every_brief_family_is_present
tests/unit/test_philo_graph_atlas.py::test_quiet_is_never_an_attention_state
tests/unit/test_philo_graph_atlas.py::test_face_cases_carry_both_ruled_viewports
tests/unit/test_philo_graph_atlas.py::test_unexercised_states_name_a_mechanism_and_a_cost
tests/unit/test_philo_graph_atlas.py::test_source_commit_is_the_revision_the_atlas_was_derived_from
tests/unit/test_philo_graph_atlas.py::test_every_applicable_predicate_is_a_kind_the_rig_implements
tests/unit/test_philo_graph_atlas.py::test_every_predicate_observes_a_selector_or_a_route
tests/unit/test_philo_graph_atlas.py::test_protocol_predicates_ask_for_a_new_row
tests/unit/test_philo_graph_atlas.py::test_every_case_keeps_its_human_sentence
tests/unit/test_philo_graph_atlas.py::test_operation_siblings_use_headless_reads_and_canonical_steps
tests/unit/test_philo_graph_atlas.py::test_named_pair_observations_bind_their_read_arguments
tests/unit/test_philo_graph_atlas.py::test_all_handled_operation_maps_items_by_decision_source
tests/unit/test_philo_graph_atlas.py::test_breakage_cases_use_evening_wrapper_and_shelf_old_item
tests/unit/test_philo_graph_atlas.py::test_every_ui_action_is_one_the_rig_implements
tests/unit/test_philo_graph_atlas.py::test_every_boundary_names_its_substitution
tests/unit/test_philo_graph_atlas.py::test_summary_cases_use_the_retained_architect_import_fixture
tests/unit/test_philo_graph_atlas.py::test_summary_run_cases_have_one_run_trigger
tests/unit/test_philo_graph_atlas.py::test_summary_running_reads_the_claimed_job_wire_status
tests/unit/test_philo_graph_atlas.py::test_summary_queued_reads_the_run_admission_response
tests/unit/test_philo_graph_atlas.py::test_summary_preconditions_do_not_require_future_or_consumed_run_state
tests/unit/test_philo_graph_atlas.py::test_summary_state_reads_do_not_require_a_new_row_after_setup_run
tests/unit/test_philo_graph_atlas.py::test_summary_manual_retry_requires_failed_producer_and_current_route
tests/unit/test_philo_graph_atlas.py::test_summary_planned_host_cases_check_real_text_and_control_ownership
tests/unit/test_philo_graph_atlas.py::test_summary_failure_cases_retain_reply_at_the_provider_boundary
tests/unit/test_philo_graph_atlas.py::test_summary_imports_wait_for_real_completion_and_retain_title
tests/unit/test_philo_graph_atlas.py::test_summary_arrival_observations_name_the_rendered_states
tests/unit/test_philo_graph_atlas.py::test_summary_models_window_closes_before_arrival_steps
tests/unit/test_philo_graph_atlas.py::test_summary_restart_proof_retains_summary_receipt_and_identity
tests/unit/test_philo_graph_atlas.py::test_summary_microphone_cases_keep_the_lawful_blocked_boundary
tests/unit/test_philo_graph_atlas.py::test_summary_cases_do_not_claim_the_old_pangram
tests/unit/test_philo_graph_atlas.py::test_summary_stop_cases_require_a_real_active_meeting
tests/unit/test_philo_graph_atlas.py::test_the_two_schemas_agree_on_the_case_contract
tests/unit/test_philo_graph_atlas.py::test_every_case_validates_against_the_graph_case_schema
tests/unit/test_philo_graph_atlas.py::test_the_graph_predicate_enum_does_not_outrun_the_rig
tests/unit/test_philo_graph_atlas.py::test_a_case_without_a_predicate_is_unreachable_with_a_reason
tests/unit/test_philo_graph_atlas.py::test_every_council_reading_names_its_sources
tests/unit/test_philo_graph_atlas.py::test_no_precondition_check_compares_two_snapshots
tests/unit/test_philo_graph_atlas.py::test_every_precondition_check_observes_a_selector_or_a_route
tests/unit/test_philo_graph_atlas.py::test_no_check_asserts_the_result_the_trigger_must_produce
tests/unit/test_philo_graph_atlas.py::test_every_protocol_field_path_with_a_placeholder_is_a_json_pointer
tests/unit/test_philo_graph_atlas.py::test_no_step_acts_on_a_root_placeholder
tests/unit/test_philo_graph_atlas.py::test_navigation_steps_carry_no_selector
tests/unit/test_philo_graph_atlas.py::test_every_click_and_fill_names_a_control
tests/unit/test_philo_graph_atlas.py::test_every_desk_face_case_crosses_the_gate_first
tests/unit/test_philo_graph_atlas.py::test_no_gate_case_crosses_the_gate_in_setup
tests/unit/test_philo_graph_atlas.py::test_gate_cases_check_the_gate_not_the_desk
tests/unit/test_philo_graph_atlas.py::test_every_captured_id_names_the_field_it_reads
tests/unit/test_philo_graph_atlas.py::test_same_day_generate_again_binds_returned_displayed_and_retained
tests/unit/test_philo_graph_atlas.py::test_no_populated_brief_case_reads_the_headline
tests/unit/test_philo_graph_atlas.py::test_the_brief_recipe_fence_refuses_its_mutations
tests/unit/test_philo_graph_atlas.py::test_the_populated_brief_predicate_needs_the_minted_row
tests/unit/test_philo_graph_atlas.py::test_j11_kept_verifies_the_saved_words_in_the_store
tests/unit/test_philo_graph_atlas.py::test_same_day_same_id_fails_a_different_id_by_machine
tests/unit/test_philo_graph_atlas.py::test_j10_retention_is_proven_after_another_reload
tests/unit/test_philo_graph_atlas.py::test_summary_failure_settings_reach_the_real_drainer_after_restart
tests/unit/test_philo_graph_atlas.py::test_summary_no_engine_absence_is_read_inside_the_existing_meetings_scope
tests/unit/test_philo_graph_atlas.py::test_summary_reload_reads_the_same_already_persisted_summary
tests/unit/test_philo_graph_atlas.py::test_summary_terminal_cases_read_durable_meeting_not_active_queue[case.j6.run_summary.intel_ready-/intel_job/status]
tests/unit/test_philo_graph_atlas.py::test_summary_terminal_cases_read_durable_meeting_not_active_queue[case.j6.run_summary.host_named-/run_receipt/attempts/0/host]
tests/unit/test_philo_graph_atlas.py::test_no_assignment_op_reads_refusal_code_separately_from_error
tests/unit/test_philo_graph_atlas.py::test_thought_op_save_starts_from_different_working_text
tests/unit/test_philo_graph_atlas.py::test_philo603_cases_use_the_real_summary_producer_and_surface_slots
tests/unit/test_philo_graph_atlas.py::test_philo603_placement_fence_rejects_fixed_card_and_overlap
tests/unit/test_philo_graph_atlas.py::test_philo603_placement_fence_accepts_flow_card_with_nine_point_clearance
tests/unit/test_philo_graph_atlas.py::test_philo603_placement_fence_checks_every_matching_clear_target
tests/unit/test_graph_walk_first_paint.py::test_first_read_paint_cannot_be_replaced_by_a_later_readable_frame[0-False-True]
tests/unit/test_graph_walk_first_paint.py::test_first_read_paint_cannot_be_replaced_by_a_later_readable_frame[200-False-False]
tests/unit/test_graph_walk_first_paint.py::test_first_read_paint_cannot_be_replaced_by_a_later_readable_frame[0-True-False]
tests/unit/test_graph_walk_first_paint.py::test_a_later_blank_cannot_hide_behind_a_good_first_paint
tests/unit/test_graph_walk_http_fault.py::test_http_fault_blocks_without_a_page
tests/unit/test_graph_walk_http_fault.py::test_http_fault_answers_only_the_named_request_times_then_falls_back
tests/unit/test_graph_walk_http_fault.py::test_http_fault_matches_the_hub_origin_only
tests/unit/test_graph_walk_http_fault.py::test_http_fault_lift_removes_the_faults_and_is_recorded
tests/unit/test_graph_walk_producer_clock.py::test_the_advance_writes_a_cumulative_offset_the_hub_clock_reads
tests/unit/test_graph_walk_producer_clock.py::test_no_offset_file_is_the_wall_clock
tests/unit/test_graph_walk_producer_clock.py::test_a_hub_without_the_seam_blocks
tests/unit/test_graph_walk_producer_clock.py::test_only_the_python_wall_clock_and_whole_days
tests/unit/test_graph_walk_producer_clock.py::test_a_case_with_the_step_boots_the_hub_with_the_seam
tests/unit/test_graph_walk_producer_clock.py::test_body_excludes_fails_a_body_that_carries_the_old_id

95 tests collected in 0.21s
........................................................................ [ 75%]
.........EEEE..........                                                  [100%]
==================================== ERRORS ====================================
_ ERROR at setup of test_first_read_paint_cannot_be_replaced_by_a_later_readable_frame[0-False-True] _

    @pytest.fixture
    def page():
        with sync_playwright() as play:
>           browser = play.chromium.launch()
                      ^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_graph_walk_first_paint.py:13: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
.venv/lib/python3.14/site-packages/playwright/sync_api/_generated.py:14568: in launch
    self._sync(
.venv/lib/python3.14/site-packages/playwright/_impl/_browser_type.py:98: in launch
    await self._channel.send(
.venv/lib/python3.14/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x10e720050>
cb = <function Channel.send.<locals>.<lambda> at 0x10e5ad640>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.Error: BrowserType.launch: Executable doesn't exist at /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.PbgUh6rVP8/Library/Caches/ms-playwright/chromium_headless_shell-1200/chrome-headless-shell-mac-arm64/chrome-headless-shell
E           ╔════════════════════════════════════════════════════════════╗
E           ║ Looks like Playwright was just installed or updated.       ║
E           ║ Please run the following command to download new browsers: ║
E           ║                                                            ║
E           ║     playwright install                                     ║
E           ║                                                            ║
E           ║ <3 Playwright Team                                         ║
E           ╚════════════════════════════════════════════════════════════╝

.venv/lib/python3.14/site-packages/playwright/_impl/_connection.py:559: Error
_ ERROR at setup of test_first_read_paint_cannot_be_replaced_by_a_later_readable_frame[200-False-False] _

    @pytest.fixture
    def page():
        with sync_playwright() as play:
>           browser = play.chromium.launch()
                      ^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_graph_walk_first_paint.py:13: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
.venv/lib/python3.14/site-packages/playwright/sync_api/_generated.py:14568: in launch
    self._sync(
.venv/lib/python3.14/site-packages/playwright/_impl/_browser_type.py:98: in launch
    await self._channel.send(
.venv/lib/python3.14/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x10f0bcf50>
cb = <function Channel.send.<locals>.<lambda> at 0x10e99e560>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.Error: BrowserType.launch: Executable doesn't exist at /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.PbgUh6rVP8/Library/Caches/ms-playwright/chromium_headless_shell-1200/chrome-headless-shell-mac-arm64/chrome-headless-shell
E           ╔════════════════════════════════════════════════════════════╗
E           ║ Looks like Playwright was just installed or updated.       ║
E           ║ Please run the following command to download new browsers: ║
E           ║                                                            ║
E           ║     playwright install                                     ║
E           ║                                                            ║
E           ║ <3 Playwright Team                                         ║
E           ╚════════════════════════════════════════════════════════════╝

.venv/lib/python3.14/site-packages/playwright/_impl/_connection.py:559: Error
_ ERROR at setup of test_first_read_paint_cannot_be_replaced_by_a_later_readable_frame[0-True-False] _

    @pytest.fixture
    def page():
        with sync_playwright() as play:
>           browser = play.chromium.launch()
                      ^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_graph_walk_first_paint.py:13: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
.venv/lib/python3.14/site-packages/playwright/sync_api/_generated.py:14568: in launch
    self._sync(
.venv/lib/python3.14/site-packages/playwright/_impl/_browser_type.py:98: in launch
    await self._channel.send(
.venv/lib/python3.14/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x10f0bfb10>
cb = <function Channel.send.<locals>.<lambda> at 0x10e9750c0>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.Error: BrowserType.launch: Executable doesn't exist at /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.PbgUh6rVP8/Library/Caches/ms-playwright/chromium_headless_shell-1200/chrome-headless-shell-mac-arm64/chrome-headless-shell
E           ╔════════════════════════════════════════════════════════════╗
E           ║ Looks like Playwright was just installed or updated.       ║
E           ║ Please run the following command to download new browsers: ║
E           ║                                                            ║
E           ║     playwright install                                     ║
E           ║                                                            ║
E           ║ <3 Playwright Team                                         ║
E           ╚════════════════════════════════════════════════════════════╝

.venv/lib/python3.14/site-packages/playwright/_impl/_connection.py:559: Error
__ ERROR at setup of test_a_later_blank_cannot_hide_behind_a_good_first_paint __

    @pytest.fixture
    def page():
        with sync_playwright() as play:
>           browser = play.chromium.launch()
                      ^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_graph_walk_first_paint.py:13: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
.venv/lib/python3.14/site-packages/playwright/sync_api/_generated.py:14568: in launch
    self._sync(
.venv/lib/python3.14/site-packages/playwright/_impl/_browser_type.py:98: in launch
    await self._channel.send(
.venv/lib/python3.14/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x10e6349d0>
cb = <function Channel.send.<locals>.<lambda> at 0x10e9531c0>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.Error: BrowserType.launch: Executable doesn't exist at /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.PbgUh6rVP8/Library/Caches/ms-playwright/chromium_headless_shell-1200/chrome-headless-shell-mac-arm64/chrome-headless-shell
E           ╔════════════════════════════════════════════════════════════╗
E           ║ Looks like Playwright was just installed or updated.     
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-09-25T04:54:55Z

- **Command:** `bash -c set -euo pipefail; export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH; export HOME=$(mktemp -d); export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright; uv run --extra dev pytest -q tests/unit/test_philo_graph_atlas.py tests/unit/test_graph_walk_first_paint.py tests/unit/test_graph_walk_http_fault.py tests/unit/test_graph_walk_producer_clock.py > docs/internal/philo/phase-6/toast/placement-proof/atlas-rig-tests.txt 2>&1; tail -20 docs/internal/philo/phase-6/toast/placement-proof/atlas-rig-tests.txt`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text
........................................................................ [ 75%]
.......................                                                  [100%]
95 passed in 4.49s
```

### Captured run — 2026-09-25T04:55:41Z

- **Command:** `bash -c set -euo pipefail; export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH; export HOME=$(mktemp -d); export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright; export HOLDSPEAK_EVIDENCE_WRITE=1; cd /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo603-red-z5r_bw9b; uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.philo603.toast.meetings_window --brain astra --viewport 393 --engine replayed --no-build --out /Users/karol/dev/tools/wt-philo-6-03/pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/red/`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text
PASS: live
BRAIN: astra
SOURCE:  dirty=False
CONTRACT: rig=1.3.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-C2JQr2p9.js'] hub=http://127.0.0.1:63580 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-aji4bi4r/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j6
VERDICT: fail terminal=settled
EVIDENCE: ['/Users/karol/dev/tools/wt-philo-6-03/pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/red/20260925T045541Z-case.philo603.toast.meetings_window-astra-393/before.png', '/Users/karol/dev/tools/wt-philo-6-03/pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/red/20260925T045541Z-case.philo603.toast.meetings_window-astra-393/after.png']
NOTE: predicate: the card is not rendered inside its declared slot '[data-aftercare-window-slot="top"]': {'selector': '[data-aftercare-window-slot="top"]', 'present': False, 'contains_card': False}
NOTE: a nonzero diff with the wrong result is a finding, not a pass (changed: ['api_reads', 'attrs', 'document_text_len', 'document_text_sha256', 'rect', 'target_present', 'text', 'values', 'visible']).
```

### Captured run — 2026-09-25T04:57:07Z

- **Command:** `bash -c set -euo pipefail; export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH; export HOME=$(mktemp -d); export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright; export HOLDSPEAK_EVIDENCE_WRITE=1; uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.philo603.toast.arrival --brain astra --viewport 393 --engine replayed --no-build --out pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text
PASS: live
BRAIN: astra
SOURCE: d1e355f2bfc4acbaa7ec3ea1a7a38f1c742ae1c4 dirty=True
CONTRACT: rig=1.3.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-ZDDpIAMw.js'] hub=http://127.0.0.1:63786 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-q_337_gz/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/20260925T045707Z-case.philo603.toast.arrival-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/20260925T045707Z-case.philo603.toast.arrival-astra-393/after.png']
NOTE: predicate: 'MEETING READY' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 12, 'y': 381, 'w': 369, 'h': 180}
```

### Captured run — 2026-09-25T04:58:13Z

- **Command:** `bash -c set -euo pipefail; export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH; export HOME=$(mktemp -d); export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright; export HOLDSPEAK_EVIDENCE_WRITE=1; uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.philo603.toast.arrival --brain astra --viewport 1440 --engine replayed --no-build --out pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text
PASS: live
BRAIN: astra
SOURCE: d1e355f2bfc4acbaa7ec3ea1a7a38f1c742ae1c4 dirty=True
CONTRACT: rig=1.3.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-ZDDpIAMw.js'] hub=http://127.0.0.1:63872 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-dpj3u7ey/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/20260925T045813Z-case.philo603.toast.arrival-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/20260925T045813Z-case.philo603.toast.arrival-astra-1440/after.png']
NOTE: predicate: 'MEETING READY' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 440, 'y': 577, 'w': 560, 'h': 152}
```

### Captured run — 2026-09-25T04:59:17Z

- **Command:** `bash -c set -euo pipefail; export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH; export HOME=$(mktemp -d); export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright; export HOLDSPEAK_EVIDENCE_WRITE=1; uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.philo603.toast.meetings_window --brain astra --viewport 393 --engine replayed --no-build --out pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text
PASS: live
BRAIN: astra
SOURCE: d1e355f2bfc4acbaa7ec3ea1a7a38f1c742ae1c4 dirty=True
CONTRACT: rig=1.3.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-ZDDpIAMw.js'] hub=http://127.0.0.1:63948 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-zpaxhdz5/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/20260925T045918Z-case.philo603.toast.meetings_window-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/20260925T045918Z-case.philo603.toast.meetings_window-astra-393/after.png']
NOTE: predicate: 'MEETING READY' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 151, 'w': 363, 'h': 180}
```

### Captured run — 2026-09-25T05:00:15Z

- **Command:** `bash -c set -euo pipefail; export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH; export HOME=$(mktemp -d); export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright; export HOLDSPEAK_EVIDENCE_WRITE=1; uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.philo603.toast.meetings_window --brain astra --viewport 1440 --engine replayed --no-build --out pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text
PASS: live
BRAIN: astra
SOURCE: d1e355f2bfc4acbaa7ec3ea1a7a38f1c742ae1c4 dirty=True
CONTRACT: rig=1.3.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-ZDDpIAMw.js'] hub=http://127.0.0.1:64040 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-sv9atfkc/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/20260925T050016Z-case.philo603.toast.meetings_window-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/20260925T050016Z-case.philo603.toast.meetings_window-astra-1440/after.png']
NOTE: predicate: 'MEETING READY' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 39, 'y': 133, 'w': 610, 'h': 152}
```

### Captured run — 2026-09-25T05:01:11Z

- **Command:** `bash -c set -euo pipefail; export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH; export HOME=$(mktemp -d); export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright; export HOLDSPEAK_EVIDENCE_WRITE=1; uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.philo603.toast.floor_list --brain astra --viewport 393 --engine replayed --no-build --out pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text
PASS: live
BRAIN: astra
SOURCE: d1e355f2bfc4acbaa7ec3ea1a7a38f1c742ae1c4 dirty=True
CONTRACT: rig=1.3.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-ZDDpIAMw.js'] hub=http://127.0.0.1:64120 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-kd3q5ood/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j6
VERDICT: blocked terminal=None
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/20260925T050111Z-case.philo603.toast.floor_list-astra-393/blocked.png']
NOTE: BLOCKED: ui step click_role on 'List view' failed: TimeoutError: Locator.click: Timeout 10000ms exceeded.
Call log:
  - waiting for get_by_role("menuitem", name="List view", exact=True).first
```

### Captured run — 2026-09-25T05:02:29Z

- **Command:** `bash -c set -euo pipefail; export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH; export HOME=$(mktemp -d); export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright; export HOLDSPEAK_EVIDENCE_WRITE=1; uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.philo603.toast.floor_list --brain astra --viewport 393 --engine replayed --no-build --out pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text
PASS: live
BRAIN: astra
SOURCE: d1e355f2bfc4acbaa7ec3ea1a7a38f1c742ae1c4 dirty=True
CONTRACT: rig=1.3.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-ZDDpIAMw.js'] hub=http://127.0.0.1:64201 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-l64lm85y/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j6
VERDICT: blocked terminal=None
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/20260925T050229Z-case.philo603.toast.floor_list-astra-393/blocked.png']
NOTE: BLOCKED: ui step click_role on 'List view' failed: TimeoutError: Locator.click: Timeout 10000ms exceeded.
Call log:
  - waiting for get_by_role("menuitem", name="List view", exact=True).first
```

### Captured run — 2026-09-25T05:04:06Z

- **Command:** `bash -c set -euo pipefail; export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH; export HOME=$(mktemp -d); export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright; export HOLDSPEAK_EVIDENCE_WRITE=1; uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.philo603.toast.floor_list --brain astra --viewport 393 --engine replayed --no-build --out pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text
PASS: live
BRAIN: astra
SOURCE: d1e355f2bfc4acbaa7ec3ea1a7a38f1c742ae1c4 dirty=True
CONTRACT: rig=1.3.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-ZDDpIAMw.js'] hub=http://127.0.0.1:64287 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-p0b6pg93/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j6
VERDICT: fail terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/20260925T050406Z-case.philo603.toast.floor_list-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/20260925T050406Z-case.philo603.toast.floor_list-astra-393/after.png']
NOTE: predicate: a covering element owns hit points: [{'x': 14, 'y': 72, 'owned': False, 'owner': 'div#desk-next > nav.desk-menu-list.desk-work-menu > button.btn--chrome.is-ghost'}, {'x': 14, 'y': 160, 'owned': False, 'owner': 'div#desk-next > nav.desk-menu-list.desk-work-menu > button.btn--chrome'}, {'x': 14, 'y': 248, 'owned': False, 'owner': 'div#desk-next > nav.desk-menu-list.desk-work-menu > button.btn--chrome'}]
NOTE: a nonzero diff with the wrong result is a finding, not a pass (changed: ['api_reads', 'attrs', 'document_text_len', 'document_text_sha256', 'rect', 'target_present', 'text', 'visible']).
```

### Captured run — 2026-09-25T05:06:00Z

- **Command:** `bash -c set -euo pipefail; export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH; export HOME=$(mktemp -d); export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright; export HOLDSPEAK_EVIDENCE_WRITE=1; uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.philo603.toast.floor_list --brain astra --viewport 393 --engine replayed --no-build --out pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text
PASS: live
BRAIN: astra
SOURCE: d1e355f2bfc4acbaa7ec3ea1a7a38f1c742ae1c4 dirty=True
CONTRACT: rig=1.3.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-ZDDpIAMw.js'] hub=http://127.0.0.1:64480 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-itm6tqof/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/20260925T050600Z-case.philo603.toast.floor_list-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/20260925T050600Z-case.philo603.toast.floor_list-astra-393/after.png']
NOTE: predicate: 'MEETING READY' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 12, 'y': 70, 'w': 369, 'h': 180}
```

### Captured run — 2026-09-25T05:06:54Z

- **Command:** `bash -c set -euo pipefail; export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH; export HOME=$(mktemp -d); export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright; export HOLDSPEAK_EVIDENCE_WRITE=1; uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.philo603.toast.floor_list --brain astra --viewport 1440 --engine replayed --no-build --out pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text
PASS: live
BRAIN: astra
SOURCE: d1e355f2bfc4acbaa7ec3ea1a7a38f1c742ae1c4 dirty=True
CONTRACT: rig=1.3.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-ZDDpIAMw.js'] hub=http://127.0.0.1:64561 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-lzawcug1/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/20260925T050654Z-case.philo603.toast.floor_list-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/20260925T050654Z-case.philo603.toast.floor_list-astra-1440/after.png']
NOTE: predicate: 'MEETING READY' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 440, 'y': 74, 'w': 560, 'h': 152}
```

### Captured run — 2026-09-25T05:07:50Z

- **Command:** `bash -c set -euo pipefail; export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH; export HOME=$(mktemp -d); export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright; export HOLDSPEAK_EVIDENCE_WRITE=1; uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.philo603.toast.floor_spatial_fallback --brain astra --viewport 393 --engine replayed --no-build --out pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text
PASS: live
BRAIN: astra
SOURCE: d1e355f2bfc4acbaa7ec3ea1a7a38f1c742ae1c4 dirty=True
CONTRACT: rig=1.3.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-ZDDpIAMw.js'] hub=http://127.0.0.1:64639 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-h2d7kx3i/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/20260925T050750Z-case.philo603.toast.floor_spatial_fallback-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/20260925T050750Z-case.philo603.toast.floor_spatial_fallback-astra-393/after.png']
NOTE: predicate: 'MEETING READY' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 16, 'y': 568, 'w': 361, 'h': 180}
```

### Captured run — 2026-09-25T05:09:03Z

- **Command:** `bash -c set -euo pipefail; export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH; export HOME=$(mktemp -d); export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright; export HOLDSPEAK_EVIDENCE_WRITE=1; cd /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo603-red-z5r_bw9b; uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.philo603.toast.floor_list --brain astra --viewport 393 --engine replayed --no-build --out /Users/karol/dev/tools/wt-philo-6-03/pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/red/`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text
PASS: live
BRAIN: astra
SOURCE:  dirty=False
CONTRACT: rig=1.3.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-C2JQr2p9.js'] hub=http://127.0.0.1:64715 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-hk7eo1oz/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j6
VERDICT: fail terminal=settled
EVIDENCE: ['/Users/karol/dev/tools/wt-philo-6-03/pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/red/20260925T050903Z-case.philo603.toast.floor_list-astra-393/before.png', '/Users/karol/dev/tools/wt-philo-6-03/pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/red/20260925T050903Z-case.philo603.toast.floor_list-astra-393/after.png']
NOTE: predicate: the card is not rendered inside its declared slot '[data-aftercare-floor-slot="top"]': {'selector': '[data-aftercare-floor-slot="top"]', 'present': False, 'contains_card': False}
NOTE: a nonzero diff with the wrong result is a finding, not a pass (changed: ['api_reads', 'attrs', 'document_text_len', 'document_text_sha256', 'rect', 'target_present', 'text', 'visible']).
```

### Captured run — 2026-09-25T05:11:50Z

- **Command:** `bash -c set -uo pipefail; export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH; export HOME=$(mktemp -d); export DEBUG_PRINT_LIMIT=300; export NO_COLOR=1; cd web; ./node_modules/.bin/vitest list src/components/AmbientLayer.test.tsx src/components/aftercarePlacement.test.tsx src/desk/chair src/desk/pullouts src/desk/__tests__/shell.test.tsx src/desk/DeskApp.test.tsx src/desk/components/DeskListView.test.tsx > ../docs/internal/philo/phase-6/toast/placement-proof/final-scoped-collect.txt 2>&1; ./node_modules/.bin/vitest run src/components/AmbientLayer.test.tsx src/components/aftercarePlacement.test.tsx src/desk/chair src/desk/pullouts src/desk/__tests__/shell.test.tsx src/desk/DeskApp.test.tsx src/desk/components/DeskListView.test.tsx --maxWorkers=2 > ../docs/internal/philo/phase-6/toast/placement-proof/final-scoped-run.txt 2>&1; result=$?; tail -35 ../docs/internal/philo/phase-6/toast/placement-proof/final-scoped-run.txt; exit "$result"`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-6-03/web

⎯⎯⎯⎯⎯⎯ Unhandled Errors ⎯⎯⎯⎯⎯⎯

Vitest caught 1 unhandled error during the test run.
This might cause false positive tests. Resolve unhandled errors to make sure your tests are not affected.

⎯⎯⎯⎯ Unhandled Rejection ⎯⎯⎯⎯⎯
TypeError: currentBucket is not iterable
 ❯ mergeRefreshItems src/desk/store/dataSlice.ts:191:26
    189|       const protectedItems = new Map<string, IdentifiedItem>();
    190|       const kindName = String(kind);
    191|       for (const item of currentBucket) {
       |                          ^
    192|         const id = item.id;
    193|         const key = writeKey(kindName, id);
 ❯ runRefresh src/desk/store/dataSlice.ts:246:25

This error originated in "src/desk/chair/arrivalSummaryRun.test.tsx" test file. It doesn't mean the error was thrown inside the file itself, but while it was running.
The latest test that might've caused the error is "shows a 409 as ONE short refusal fact, the reason on its title". It might mean one of the following:
- The error was thrown, while Vitest was running this test.
- If the error occurred after the test had been completed, this was the last documented test before it was thrown.
⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯


 Test Files  32 passed (32)
      Tests  235 passed (235)
     Errors  1 error
   Start at  23:11:54
   Duration  12.56s (transform 1.38s, setup 1.28s, import 5.57s, tests 10.33s, environment 5.46s)
```

### Captured run — 2026-09-25T05:12:43Z

- **Command:** `bash -c set -euo pipefail; export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH; export HOME=$(mktemp -d); export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright; export DEBUG_PRINT_LIMIT=300; export NO_COLOR=1; cd web; ./node_modules/.bin/vitest list src/components/AmbientLayer.test.tsx src/components/aftercarePlacement.test.tsx src/desk/components/DeskListView.test.tsx > ../docs/internal/philo/phase-6/toast/placement-proof/final-focused-collect.txt 2>&1; ./node_modules/.bin/vitest run src/components/AmbientLayer.test.tsx src/components/aftercarePlacement.test.tsx src/desk/components/DeskListView.test.tsx --maxWorkers=2 > ../docs/internal/philo/phase-6/toast/placement-proof/final-focused-run.txt 2>&1; tail -10 ../docs/internal/philo/phase-6/toast/placement-proof/final-focused-run.txt; npm run typecheck; cd ..; uv run --extra dev pytest --collect-only -q tests/unit/test_philo_graph_atlas.py tests/unit/test_graph_walk_first_paint.py tests/unit/test_graph_walk_http_fault.py tests/unit/test_graph_walk_producer_clock.py tests/unit/test_philo_architecture.py > docs/internal/philo/phase-6/toast/placement-proof/final-python-collect.txt 2>&1; uv run --extra dev pytest -q tests/unit/test_philo_graph_atlas.py tests/unit/test_graph_walk_first_paint.py tests/unit/test_graph_walk_http_fault.py tests/unit/test_graph_walk_producer_clock.py tests/unit/test_philo_architecture.py > docs/internal/philo/phase-6/toast/placement-proof/final-python-run.txt 2>&1; tail -12 docs/internal/philo/phase-6/toast/placement-proof/final-python-run.txt`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-6-03/web


 Test Files  3 passed (3)
      Tests  30 passed (30)
   Start at  23:12:45
   Duration  3.90s (transform 1.29s, setup 164ms, import 2.08s, tests 3.04s, environment 527ms)


> holdspeak-web@0.0.1 typecheck
> tsc --noEmit

npm notice
npm notice New minor version of npm available! 11.6.2 -> 11.20.0
npm notice Changelog: https://github.com/npm/cli/releases/tag/v11.20.0
npm notice To update run: npm install -g npm@11.20.0
npm notice
........................................................................ [ 69%]
................................                                         [100%]
104 passed in 4.44s
```

### Captured run — 2026-09-25T05:13:57Z

- **Command:** `bash -c set -euo pipefail; export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH; export HOME=$(mktemp -d); export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright; export HOLDSPEAK_EVIDENCE_WRITE=1; uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.philo603.toast.arrival --brain astra --viewport 393 --engine replayed --no-build --out pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text
PASS: live
BRAIN: astra
SOURCE: d1e355f2bfc4acbaa7ec3ea1a7a38f1c742ae1c4 dirty=True
CONTRACT: rig=1.3.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-ZDDpIAMw.js'] hub=http://127.0.0.1:64957 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-z57p0pmj/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T051357Z-case.philo603.toast.arrival-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T051357Z-case.philo603.toast.arrival-astra-393/after.png']
NOTE: predicate: 'MEETING READY' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 12, 'y': 381, 'w': 369, 'h': 180}
```

### Captured run — 2026-09-25T05:16:52Z

- **Command:** `bash -c set -euo pipefail; export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH; export HOME=$(mktemp -d); export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright; export HOLDSPEAK_EVIDENCE_WRITE=1; uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.philo603.toast.arrival --brain astra --viewport 1440 --engine replayed --no-build --out pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text
PASS: live
BRAIN: astra
SOURCE: d1e355f2bfc4acbaa7ec3ea1a7a38f1c742ae1c4 dirty=True
CONTRACT: rig=1.3.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-ZDDpIAMw.js'] hub=http://127.0.0.1:65107 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-wxdbuz10/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T051652Z-case.philo603.toast.arrival-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T051652Z-case.philo603.toast.arrival-astra-1440/after.png']
NOTE: predicate: 'MEETING READY' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 440, 'y': 577, 'w': 560, 'h': 152}
```

### Captured run — 2026-09-25T05:19:37Z

- **Command:** `bash -c set -euo pipefail; export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH; export HOME=$(mktemp -d); export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright; export HOLDSPEAK_EVIDENCE_WRITE=1; uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.philo603.toast.meetings_window --brain astra --viewport 393 --engine replayed --no-build --out pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text
PASS: live
BRAIN: astra
SOURCE: d1e355f2bfc4acbaa7ec3ea1a7a38f1c742ae1c4 dirty=True
CONTRACT: rig=1.3.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-ZDDpIAMw.js'] hub=http://127.0.0.1:65344 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-7t7ddgn9/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T051937Z-case.philo603.toast.meetings_window-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T051937Z-case.philo603.toast.meetings_window-astra-393/after.png']
NOTE: predicate: 'MEETING READY' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 151, 'w': 363, 'h': 180}
```

### Captured run — 2026-09-25T05:20:45Z

- **Command:** `bash -c set -euo pipefail; export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH; export HOME=$(mktemp -d); export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright; export HOLDSPEAK_EVIDENCE_WRITE=1; uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.philo603.toast.meetings_window --brain astra --viewport 1440 --engine replayed --no-build --out pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text
PASS: live
BRAIN: astra
SOURCE: d1e355f2bfc4acbaa7ec3ea1a7a38f1c742ae1c4 dirty=True
CONTRACT: rig=1.3.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-ZDDpIAMw.js'] hub=http://127.0.0.1:65508 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-she3q2dz/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T052045Z-case.philo603.toast.meetings_window-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T052045Z-case.philo603.toast.meetings_window-astra-1440/after.png']
NOTE: predicate: 'MEETING READY' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 39, 'y': 133, 'w': 610, 'h': 152}
```

### Captured run — 2026-09-25T05:22:07Z

- **Command:** `bash -c set -euo pipefail; export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH; export HOME=$(mktemp -d); export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright; export HOLDSPEAK_EVIDENCE_WRITE=1; uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.philo603.toast.floor_list --brain astra --viewport 393 --engine replayed --no-build --out pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text
PASS: live
BRAIN: astra
SOURCE: d1e355f2bfc4acbaa7ec3ea1a7a38f1c742ae1c4 dirty=True
CONTRACT: rig=1.3.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-ZDDpIAMw.js'] hub=http://127.0.0.1:49233 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-h0mowlap/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T052207Z-case.philo603.toast.floor_list-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T052207Z-case.philo603.toast.floor_list-astra-393/after.png']
NOTE: predicate: 'MEETING READY' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 12, 'y': 70, 'w': 369, 'h': 180}
```

### Captured run — 2026-09-25T05:27:27Z

- **Command:** `bash -c set -euo pipefail; export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH; export HOME=$(mktemp -d); export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright; export HOLDSPEAK_EVIDENCE_WRITE=1; uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.philo603.toast.floor_list --brain astra --viewport 1440 --engine replayed --no-build --out pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text
PASS: live
BRAIN: astra
SOURCE: d1e355f2bfc4acbaa7ec3ea1a7a38f1c742ae1c4 dirty=True
CONTRACT: rig=1.3.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-ZDDpIAMw.js'] hub=http://127.0.0.1:49395 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-mzhkecb3/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T052727Z-case.philo603.toast.floor_list-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T052727Z-case.philo603.toast.floor_list-astra-1440/after.png']
NOTE: predicate: 'MEETING READY' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 440, 'y': 74, 'w': 560, 'h': 152}
```

### Captured run — 2026-09-25T05:28:19Z

- **Command:** `bash -c set -euo pipefail; export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH; export HOME=$(mktemp -d); export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright; export HOLDSPEAK_EVIDENCE_WRITE=1; uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.philo603.toast.arrival --brain astra --viewport 393 --engine replayed --no-build --out pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text
PASS: live
BRAIN: astra
SOURCE: d1e355f2bfc4acbaa7ec3ea1a7a38f1c742ae1c4 dirty=True
CONTRACT: rig=1.3.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-ZDDpIAMw.js'] hub=http://127.0.0.1:49475 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-sak6wj28/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T052820Z-case.philo603.toast.arrival-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T052820Z-case.philo603.toast.arrival-astra-393/after.png', 'pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T052820Z-case.philo603.toast.arrival-astra-393/dismissed.png']
NOTE: predicate: 'MEETING READY' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 12, 'y': 381, 'w': 369, 'h': 180}
```

### Captured run — 2026-09-25T05:29:13Z

- **Command:** `bash -c set -euo pipefail; export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH; export HOME=$(mktemp -d); export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright; export HOLDSPEAK_EVIDENCE_WRITE=1; uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case case.philo603.toast.arrival --brain astra --viewport 1440 --engine replayed --no-build --out pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text
PASS: live
BRAIN: astra
SOURCE: d1e355f2bfc4acbaa7ec3ea1a7a38f1c742ae1c4 dirty=True
CONTRACT: rig=1.3.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas.json
RUNTIME: build=['index-ZDDpIAMw.js'] hub=http://127.0.0.1:49557 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-hmpuwzlr/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T052913Z-case.philo603.toast.arrival-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T052913Z-case.philo603.toast.arrival-astra-1440/after.png', 'pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/final/20260925T052913Z-case.philo603.toast.arrival-astra-1440/dismissed.png']
NOTE: predicate: 'MEETING READY' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 440, 'y': 577, 'w': 560, 'h': 152}
```

### Captured run — 2026-09-25T05:30:20Z

- **Command:** `bash docs/internal/philo/phase-6/toast/placement-proof/final-validation.sh`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text
tests/unit/test_philo_architecture.py::test_requirement_catalogue_checks_its_own_source_references
tests/unit/test_philo_architecture.py::test_existing_build_copy_is_not_source_evidence

104 tests collected in 0.23s
........................................................................ [ 69%]
................................                                         [100%]
104 passed in 4.43s
boundary census drift
```

### Captured run — 2026-09-25T05:31:40Z

- **Command:** `bash docs/internal/philo/phase-6/toast/placement-proof/final-validation.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text
tests/unit/test_philo_architecture.py::test_requirement_catalogue_checks_its_own_source_references
tests/unit/test_philo_architecture.py::test_existing_build_copy_is_not_source_evidence

104 tests collected in 0.20s
........................................................................ [ 69%]
................................                                         [100%]
104 passed in 4.40s
Architecture documentation checked (10 outputs).
Documentation coverage checked.
API reference checked
Boundary candidate census checked
philo_graph_reference.py --check: exit 0 (all graph rows checked; full console in .tmp/philo603/graph-check.txt)
```

## Story closure reading — Astra

Each acceptance box is paid in the [lane report](../../../../docs/internal/philo/phase-6/toast/placement-proof/lane-report.md). It links the six final actual runs and shots, per-surface 9-point samples, the pre-trigger scroll counts, and the three archived product reds. The report reproduces raw red/green tails; collection and run logs ship next to it.

The real 393 CaptureBar is 138 px high. In Chromium the Arrival card, summary and capture each own 9/9 points, with no card intersection against the summary, capture or generated BRIEF row. One phone scroll call moves the accepted reading position; desktop makes none. The Meetings window's hidden Arrival backdrop is not claimed readable; its foreground headline is 9/9, as is the Floor-list header.

Real Arrival Dismiss runs at 393 (`20260925T052820Z`) and 1440 (`20260925T052913Z`) retain before, after and dismissed shots. The card is absent, the slot empty and hidden, and CaptureBar 9/9 after Dismiss. Browser proof is Chromium only, not an owner sitting or physical phone. Spatial WebGL Floor remains fixed, backed by run `20260925T050750Z` and the phase-local ledger.

Relevant validation: 30 focused Vitest and 104 Python tests pass. The broad scoped Vitest run passes 235 assertions but exits 1 with the inherited `currentBucket is not iterable` error in `arrivalSummaryRun.test.tsx`; untouched origin/main archive reproduces it with 214 assertions passing. The phase-local ledger names a separate fixture repair. All five generated checks, typecheck and build pass. The ChairHome change is only the exact four-line patch in gated commit `d1e355f2`; lane A reconciles it. `intelligenceAttention.ts` and the product card's words are unchanged.

The [Astra-invoked built check](checks/story-03-placement-astra-invoked-claude.md) is labelled separately from the calling Muad'Dib's counsel, which remains before merge. Conditions C1 (browser scope) and C2 (Dismiss glass) are paid and its multi-window limit is ledgered. Phase-wide integration rehearsal remains open.

### Captured run — 2026-09-25T05:37:14Z

- **Command:** `bash -c set -euo pipefail; .githooks/dw check holdspeak-philo; .githooks/dw check; git diff --check; test -z "$(git status --porcelain -- pm/roadmap/holdspeak/)"`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text
dw check: ok
ERROR pm/roadmap/holdspeak/phase-101-the-native-innards/evidence-story-04.md: evidence exists but matching story is not done
ERROR pm/roadmap/holdspeak/phase-152-the-hands: all stories are done but final-summary.md is missing
ERROR pm/roadmap/holdspeak/phase-153-the-practice: all stories are done but final-summary.md is missing
ERROR pm/roadmap/holdspeak/phase-154-the-call: all stories are done but final-summary.md is missing
ERROR pm/roadmap/holdspeak/phase-156-the-front-door: all stories are done but final-summary.md is missing
ERROR pm/roadmap/holdspeak/phase-200-the-working-practice: all stories are done but final-summary.md is missing
```

### Captured run — 2026-09-25T05:38:01Z

- **Command:** `bash -c cd /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo603-red-z5r_bw9b; .githooks/dw check > /Users/karol/dev/tools/wt-philo-6-03/docs/internal/philo/phase-6/toast/placement-proof/dw-global-baseline.txt 2>&1; result=$?; cat /Users/karol/dev/tools/wt-philo-6-03/docs/internal/philo/phase-6/toast/placement-proof/dw-global-baseline.txt; exit "$result"`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text
ERROR pm/roadmap/holdspeak/phase-101-the-native-innards/evidence-story-04.md: evidence exists but matching story is not done
ERROR pm/roadmap/holdspeak/phase-152-the-hands: all stories are done but final-summary.md is missing
ERROR pm/roadmap/holdspeak/phase-153-the-practice: all stories are done but final-summary.md is missing
ERROR pm/roadmap/holdspeak/phase-154-the-call: all stories are done but final-summary.md is missing
ERROR pm/roadmap/holdspeak/phase-156-the-front-door: all stories are done but final-summary.md is missing
ERROR pm/roadmap/holdspeak/phase-200-the-working-practice: all stories are done but final-summary.md is missing
```

### Captured run — 2026-09-25T05:38:01Z

- **Command:** `bash -c set -euo pipefail; .githooks/dw check holdspeak-philo; git diff --check; test -z "$(git status --porcelain -- pm/roadmap/holdspeak/)"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 896ec831e66cff8d0eecf3020e4cfef17b97b473

```text
dw check: ok
```

Workbench closure: PHILO-only check is clean after the story-status CLI flip. The global check is not clean: six other-project errors match the pinned origin/main archive exactly (both failed commands retained above). Those files remain untouched; the phase-local ledger assigns existing roadmap maintenance. C3 is paid by the clean owning-project check.

## Publication

[PR #649](https://github.com/karolswdev/HoldSpeak/pull/649) is open, unmerged. The exact slot is gated in `d1e355f2`; the build, story flip and paired evidence are gated in `c6aafa8e6f424b0dbeced455ca490c15afdafd4b` (7/7 boxes, one story, contract digest `sha256:52ef8ad8406a3f1f80940b511b3e7280c903dee06ce93cd871480417fba39f67`). Post-commit `git log -1` was read. Calling Muad’Dib counsel and lane A reconciliation remain before merge.

### Captured run — 2026-09-25T05:41:16Z

- **Command:** `bash -c set -euo pipefail; bash -n docs/internal/philo/phase-6/toast/placement-proof/final-validation.sh; .githooks/dw check holdspeak-philo; .githooks/dw verify d8f608c812e540678ed3f945156aeeccc46d795a..HEAD; git diff --check; test -z "$(git status --porcelain -- pm/roadmap/holdspeak/)"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d9f32f686cdef6547fd98dd0036a1baf5ba4da16

```text
dw check: ok
dw verify: ok (1 commits verified, 0 pre-epoch skipped)
```

Publication qualification: Main advanced during this build: lane A merged as PR #646 (`e64114df`). PR #649 is open but reports five conflicts: `docs/internal/philo/graph/atlas.json`, `docs/generated/graph.json`, `docs/generated/boundary-candidates.json`, this project README, and the Phase 6 status file. The read-only merge preflight auto-merges ChairHome and the atlas tests; no combined-tree test or glass result is claimed. Muad’Dib’s integration and counsel remain before merge. Raw output: `docs/internal/philo/phase-6/toast/placement-proof/merge-preflight.txt`.
