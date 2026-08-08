# Evidence - HS-129-07

- **Story:** HS-129-07 - The speakable desk
- **Status:** done
- **Date:** 2026-08-08

## Proof

### Captured run — 2026-08-08T21:03:18Z

- **Command:** `bash -lc cd web && npx vitest run --maxWorkers=2 src/desk/__tests__/speakableDesk.test.tsx src/desk/pullouts/views/ReceiptsView.test.tsx src/desk/surface/gadgets.test.tsx`
- **Cwd:** .
- **Exit code:** 134
- **Index-tree:** 434eb1a78c8ab360e3e9a644d1b9531f3d3f0cad

```text
dyld[73386]: Library not loaded: /opt/homebrew/opt/llhttp/lib/libllhttp.9.3.dylib
  Referenced from: <BD9D65B7-B478-3E6C-8530-96FD5D1D2AF9> /opt/homebrew/Cellar/node/25.9.0/bin/node
  Reason: tried: '/opt/homebrew/opt/llhttp/lib/libllhttp.9.3.dylib' (no such file), '/System/Volumes/Preboot/Cryptexes/OS/opt/homebrew/opt/llhttp/lib/libllhttp.9.3.dylib' (no such file), '/opt/homebrew/opt/llhttp/lib/libllhttp.9.3.dylib' (no such file), '/opt/homebrew/Cellar/llhttp/9.4.1/lib/libllhttp.9.3.dylib' (no such file), '/System/Volumes/Preboot/Cryptexes/OS/opt/homebrew/Cellar/llhttp/9.4.1/lib/libllhttp.9.3.dylib' (no such file), '/opt/homebrew/Cellar/llhttp/9.4.1/lib/libllhttp.9.3.dylib' (no such file)
bash: line 1: 73386 Abort trap: 6           npx vitest run --maxWorkers=2 src/desk/__tests__/speakableDesk.test.tsx src/desk/pullouts/views/ReceiptsView.test.tsx src/desk/surface/gadgets.test.tsx
```

### Captured run — 2026-08-08T21:03:36Z

- **Command:** `env PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:/usr/bin:/bin /Users/karol/.nvm/versions/node/v22.21.0/bin/npx --prefix /Users/karol/dev/tools/HoldSpeak/web vitest run --maxWorkers=2 src/desk/__tests__/speakableDesk.test.tsx src/desk/pullouts/views/ReceiptsView.test.tsx src/desk/surface/gadgets.test.tsx`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 434eb1a78c8ab360e3e9a644d1b9531f3d3f0cad

```text

 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak

 ❯ web/src/desk/surface/gadgets.test.tsx (16 tests | 16 failed) 8ms
     × CheckGadget is a real checkbox 3ms
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
 ❯ .claude/worktrees/agent-a9c608ea96d2670ce/web/src/desk/surface/gadgets.test.tsx (16 tests | 16 failed) 9ms
     × CheckGadget is a real checkbox 3ms
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
 ❯ .claude/worktrees/agent-abbf68fe2324f953e/web/src/desk/surface/gadgets.test.tsx (0 test)
 ❯ .claude/worktrees/agent-ab29ddb1420d500bb/web/src/desk/surface/gadgets.test.tsx (0 test)
 ❯ .claude/worktrees/agent-ace7e51320a364b7d/web/src/desk/surface/gadgets.test.tsx (16 tests | 16 failed) 9ms
     × CheckGadget is a real checkbox 3ms
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
     × the armed face self-disarms after 3s (a late press only re-arms) 1ms
     × PadGadget is a real textarea 0ms
     × FoldGadget keeps details semantics and carries the token slot 0ms
 ❯ .claude/worktrees/agent-aeb023a4f3a91aa8b/web/src/desk/surface/gadgets.test.tsx (16 tests | 16 failed) 8ms
     × CheckGadget is a real checkbox 3ms
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
 ❯ .claude/worktrees/agent-acf31ab3d17ae1af2/web/src/desk/surface/gadgets.test.tsx (0 test)
 ❯ .claude/worktrees/agent-adb180ff61e1dff2b/web/src/desk/surface/gadgets.test.tsx (0 test)
 ❯ .claude/worktrees/agent-addf5256665a9e069/web/src/desk/surface/gadgets.test.tsx (16 tests | 16 failed) 8ms
     × CheckGadget is a real checkbox 3ms
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
 ❯ web/src/desk/__tests__/speakableDesk.test.tsx (3 tests | 3 failed) 4ms
     × census: the ten rendered audited text wells each carry a mic affordance 3ms
     × fills the Workflow, Note, and knowledge-base fields through their mics 1ms
     × fills receipt search and both composer variants through their mics 0ms
 ❯ .claude/worktrees/agent-aead56ccba8ca2542/web/src/desk/surface/gadgets.test.tsx (16 tests | 16 failed) 9ms
     × CheckGadget is a real checkbox 3ms
     × CycleGadget is a real select and keeps an off-roster value visible 1ms
     × StepperGadget arrows step and clamp 0ms
     × MxRadio reveals only the selected option's gadgets 0ms
     × SecretRow shows the chip, arms an in-row replace, Enter commits 0ms
     × SecretRow Escape reverts the armed replace without committing 0ms
     × GadgetRow carries the label and a token fact 0ms
     × LedMeter is a labeled meter: lit segments follow the value, hot above 0.8 1ms
     × LedMeter scanning posture reads as scanning, not a level 1ms
     × LampGadget is never color-only: the axis label rides with the lamp 0ms
     × TransportKey: held = pressed (inverted video is the CSS contract) 0ms
     × GadgetTable verbs slot renders per-row verbs in place of the bare × 0ms
     × GadgetTable default delete ARMS: × → DELETE? → gone 1ms
     × the armed face self-disarms after 3s (a late press only re-arms) 0ms
     × PadGadget is a real textarea 0ms
     × FoldGadget keeps details semantics and carries the token slot 0ms
 ❯ web/src/desk/pullouts/views/ReceiptsView.test.tsx (2 tests | 2 failed) 3ms
     × searches on keystroke and supports a governing-only WHY filter 2ms
     × opens full receipt evidence in place and returns to the preserved ledger 0ms

⎯⎯⎯⎯⎯⎯ Failed Suites 4 ⎯⎯⎯⎯⎯⎯⎯

 FAIL  .claude/worktrees/agent-ab29ddb1420d500bb/web/src/desk/surface/gadgets.test.tsx [ .claude/worktrees/agent-ab29ddb1420d500bb/web/src/desk/surface/gadgets.test.tsx ]
Error: Cannot find package '@testing-library/react' imported from /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-ab29ddb1420d500bb/web/src/desk/surface/gadgets.test.tsx
 ❯ .claude/worktrees/agent-ab29ddb1420d500bb/web/src/desk/surface/gadgets.test.tsx:4:1
      2| // interaction contracts hold (checkbox species, cycle select, stepper
      3| // arrows, mx radio reveal, secret armed replace).
      4| import { act, fireEvent, render, screen } from "@testing-library/react…
       | ^
      5| import userEvent from "@testing-library/user-event";
      6| import { describe, expect, it, vi } from "vitest";

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[1/105]⎯

 FAIL  .claude/worktrees/agent-abbf68fe2324f953e/web/src/desk/surface/gadgets.test.tsx [ .claude/worktrees/agent-abbf68fe2324f953e/web/src/desk/surface/gadgets.test.tsx ]
Error: Cannot find package '@testing-library/react' imported from /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-abbf68fe2324f953e/web/src/desk/surface/gadgets.test.tsx
 ❯ .claude/worktrees/agent-abbf68fe2324f953e/web/src/desk/surface/gadgets.test.tsx:4:1
      2| // interaction contracts hold (checkbox species, cycle select, stepper
      3| // arrows, mx radio reveal, secret armed replace).
      4| import { act, fireEvent, render, screen } from "@testing-library/react…
       | ^
      5| import userEvent from "@testing-library/user-event";
      6| import { describe, expect, it, vi } from "vitest";

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[2/105]⎯

 FAIL  .claude/worktrees/agent-acf31ab3d17ae1af2/web/src/desk/surface/gadgets.test.tsx [ .claude/worktrees/agent-acf31ab3d17ae1af2/web/src/desk/surface/gadgets.test.tsx ]
Error: Cannot find package '@testing-library/react' imported from /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-acf31ab3d17ae1af2/web/src/desk/surface/gadgets.test.tsx
 ❯ .claude/worktrees/agent-acf31ab3d17ae1af2/web/src/desk/surface/gadgets.test.tsx:4:1
      2| // interaction contracts hold (checkbox species, cycle select, stepper
      3| // arrows, mx radio reveal, secret armed replace).
      4| import { act, fireEvent, render, screen } from "@testing-library/react…
       | ^
      5| import userEvent from "@testing-library/user-event";
      6| import { describe, expect, it, vi } from "vitest";

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[3/105]⎯

 FAIL  .claude/worktrees/agent-adb180ff61e1dff2b/web/src/desk/surface/gadgets.test.tsx [ .claude/worktrees/agent-adb180ff61e1dff2b/web/src/desk/surface/gadgets.test.tsx ]
Error: Cannot find package '@testing-library/react' imported from /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-adb180ff61e1dff2b/web/src/desk/surface/gadgets.test.tsx
 ❯ .claude/worktrees/agent-adb180ff61e1dff2b/web/src/desk/surface/gadgets.test.tsx:4:1
      2| // interaction contracts hold (checkbox species, cycle select, stepper
      3| // arrows, mx radio reveal, secret armed replace).
      4| import { act, fireEvent, render, screen } from "@testing-library/react…
       | ^
      5| import userEvent from "@testing-library/user-event";
      6| import { describe, expect, it, vi } from "vitest";

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[4/105]⎯


⎯⎯⎯⎯⎯⎯ Failed Tests 101 ⎯⎯⎯⎯⎯⎯

 FAIL  web/src/desk/__tests__/speakableDesk.test.tsx > HS-129-07 speakable desk > census: the ten rendered audited text wells each carry a mic affordance
ReferenceError: document is not defined
 ❯ Proxy.render web/node_modules/@testing-library/react/dist/pure.js:256:5
 ❯ web/src/desk/__tests__/speakableDesk.test.tsx:68:27
     66|   it("census: the ten rendered audited text wells each carry a mic aff…
     67|     apiFetch.mockResolvedValue([]);
     68|     const { container } = render(
       |                           ^
     69|       <>
     70|         <WorkflowEditor object={workflow} onClose={vi.fn()} />

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[5/105]⎯

 FAIL  web/src/desk/__tests__/speakableDesk.test.tsx > HS-129-07 speakable desk > fills the Workflow, Note, and knowledge-base fields through their mics
ReferenceError: document is not defined
 ❯ Proxy.render web/node_modules/@testing-library/react/dist/pure.js:256:5
 ❯ web/src/desk/__tests__/speakableDesk.test.tsx:87:5
     85|
     86|   it("fills the Workflow, Note, and knowledge-base fields through thei…
     87|     render(
       |     ^
     88|       <>
     89|         <WorkflowEditor object={workflow} onClose={vi.fn()} />

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[6/105]⎯

 FAIL  web/src/desk/__tests__/speakableDesk.test.tsx > HS-129-07 speakable desk > fills receipt search and both composer variants through their mics
ReferenceError: document is not defined
 ❯ Proxy.render web/node_modules/@testing-library/react/dist/pure.js:256:5
 ❯ web/src/desk/__tests__/speakableDesk.test.tsx:113:5
    111|     const onLineChange = vi.fn();
    112|     const onPadChange = vi.fn();
    113|     render(
       |     ^
    114|       <>
    115|         <ReceiptsView />

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[7/105]⎯

 FAIL  web/src/desk/surface/gadgets.test.tsx > gadget kit > CheckGadget is a real checkbox
TypeError: Cannot read properties of undefined (reading 'Symbol(Node prepared with document state workarounds)')
 ❯ prepareDocument web/node_modules/@testing-library/user-event/dist/esm/document/prepareDocument.js:10:17
 ❯ Object.setupMain [as setup] web/node_modules/@testing-library/user-event/dist/esm/setup/setup.js:52:5
 ❯ web/src/desk/surface/gadgets.test.tsx:25:28
     23|   it("CheckGadget is a real checkbox", async () => {
     24|     const onChange = vi.fn();
     25|     const user = userEvent.setup();
       |                            ^
     26|     render(<CheckGadget label="Enabled" checked={false} onChange={onCh…
     27|     const box = screen.getByRole("checkbox", { name: "Enabled" });

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[8/105]⎯

 FAIL  web/src/desk/surface/gadgets.test.tsx > gadget kit > CycleGadget is a real select and keeps an off-roster value visible
ReferenceError: document is not defined
 ❯ render web/node_modules/@testing-library/react/dist/pure.js:256:5
 ❯ web/src/desk/surface/gadgets.test.tsx:34:5
     32|   it("CycleGadget is a real select and keeps an off-roster value visib…
     33|     const onChange = vi.fn();
     34|     render(
       |     ^
     35|       <CycleGadget
     36|         label="Theme"

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[9/105]⎯

 FAIL  web/src/desk/surface/gadgets.test.tsx > gadget kit > StepperGadget arrows step and clamp
TypeError: Cannot read properties of undefined (reading 'Symbol(Node prepared with document state workarounds)')
 ❯ prepareDocument web/node_modules/@testing-library/user-event/dist/esm/document/prepareDocument.js:10:17
 ❯ Object.setupMain [as setup] web/node_modules/@testing-library/user-event/dist/esm/setup/setup.js:52:5
 ❯ web/src/desk/surface/gadgets.test.tsx:50:28
     48|   it("StepperGadget arrows step and clamp", async () => {
     49|     const onChange = vi.fn();
     50|     const user = userEvent.setup();
       |                            ^
     51|     render(
     52|       <StepperGadget

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[10/105]⎯

 FAIL  web/src/desk/surface/gadgets.test.tsx > gadget kit > MxRadio reveals only the selected option's gadgets
ReferenceError: document is not defined
 ❯ render web/node_modules/@testing-library/react/dist/pure.js:256:5
 ❯ web/src/desk/surface/gadgets.test.tsx:72:26
     70|   it("MxRadio reveals only the selected option's gadgets", () => {
     71|     const onChange = vi.fn();
     72|     const { rerender } = render(
       |                          ^
     73|       <MxRadio
     74|         label="Runs on"

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[11/105]⎯

 FAIL  web/src/desk/surface/gadgets.test.tsx > gadget kit > SecretRow shows the chip, arms an in-row replace, Enter commits
TypeError: Cannot read properties of undefined (reading 'Symbol(Node prepared with document state workarounds)')
 ❯ prepareDocument web/node_modules/@testing-library/user-event/dist/esm/document/prepareDocument.js:10:17
 ❯ Object.setupMain [as setup] web/node_modules/@testing-library/user-event/dist/esm/setup/setup.js:52:5
 ❯ web/src/desk/surface/gadgets.test.tsx:104:28
    102|   it("SecretRow shows the chip, arms an in-row replace, Enter commits"…
    103|     const onReplace = vi.fn();
    104|     const user = userEvent.setup();
       |                            ^
    105|     render(
    106|       <SecretRow

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[12/105]⎯

 FAIL  web/src/desk/surface/gadgets.test.tsx > gadget kit > SecretRow Escape reverts the armed replace without committing
TypeError: Cannot read properties of undefined (reading 'Symbol(Node prepared with document state workarounds)')
 ❯ prepareDocument web/node_modules/@testing-library/user-event/dist/esm/document/prepareDocument.js:10:17
 ❯ Object.setupMain [as setup] web/node_modules/@testing-library/user-event/dist/esm/setup/setup.js:52:5
 ❯ web/src/desk/surface/gadgets.test.tsx:124:28
    122|   it("SecretRow Escape reverts the armed replace without committing", …
    123|     const onReplace = vi.fn();
    124|     const user = userEvent.setup();
       |                            ^
    125|     render(
    126|       <SecretRow label="Device audio key" configured={false} onReplace…

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[13/105]⎯

 FAIL  web/src/desk/surface/gadgets.test.tsx > gadget kit > GadgetRow carries the label and a token fact
ReferenceError: document is not defined
 ❯ render web/node_modules/@testing-library/react/dist/pure.js:256:5
 ❯ web/src/desk/surface/gadgets.test.tsx:137:5
    135|
    136|   it("GadgetRow carries the label and a token fact", () => {
    137|     render(
       |     ^
    138|       <GadgetRow label="Latency budget" fact="ms">
    139|         <span>gadget</span>

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[14/105]⎯

 FAIL  web/src/desk/surface/gadgets.test.tsx > gadget kit > LedMeter is a labeled meter: lit segments follow the value, hot above 0.8
ReferenceError: document is not defined
 ❯ render web/node_modules/@testing-library/react/dist/pure.js:256:5
 ❯ web/src/desk/surface/gadgets.test.tsx:149:27
    147|
    148|   it("LedMeter is a labeled meter: lit segments follow the value, hot …
    149|     const { container } = render(
       |                           ^
    150|       <LedMeter label="Level" value={0.5} segments={12} />,
    151|     );

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[15/105]⎯

 FAIL  web/src/desk/surface/gadgets.test.tsx > gadget kit > LedMeter scanning posture reads as scanning, not a level
ReferenceError: document is not defined
 ❯ render web/node_modules/@testing-library/react/dist/pure.js:256:5
 ❯ web/src/desk/surface/gadgets.test.tsx:160:27
    158|
    159|   it("LedMeter scanning posture reads as scanning, not a level", () =>…
    160|     const { container } = render(<LedMeter label="Level" value={1} sca…
       |                           ^
    161|     const meter = screen.getByRole("mete
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-08-08T21:03:52Z

- **Command:** `/bin/sh -c cd /Users/karol/dev/tools/HoldSpeak/web && PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:/usr/bin:/bin npx vitest run --maxWorkers=2 src/desk/__tests__/speakableDesk.test.tsx src/desk/pullouts/views/ReceiptsView.test.tsx src/desk/surface/gadgets.test.tsx`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 434eb1a78c8ab360e3e9a644d1b9531f3d3f0cad

```text

 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web


 Test Files  3 passed (3)
      Tests  21 passed (21)
   Start at  15:03:54
   Duration  4.20s (transform 1.00s, setup 445ms, import 2.03s, tests 1.63s, environment 2.16s)
```

### Captured run — 2026-08-08T21:04:06Z

- **Command:** `/bin/sh -c cd /Users/karol/dev/tools/HoldSpeak/web && PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:/usr/bin:/bin npm run typecheck`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 434eb1a78c8ab360e3e9a644d1b9531f3d3f0cad

```text

> holdspeak-web@0.0.1 typecheck
> tsc --noEmit
```

## Suite triage

The orchestrator reproduced the full-web-suite failures on pre-129 main
`4c63c997`; they are pre-existing debt, not HS-129-07 regressions. Affected
areas: ask, chat, commandDeck, floorMenu, grounding, verbRegistry,
DeskArrival, and DeskListView. HS-129-11 owns the phase ledger.
