# Evidence - HS-139-05

- **Story:** HS-139-05 - Seven tiles
- **Status:** done
- **Date:** 2026-08-17

## Proof

### Captured run — 2026-08-18T02:31:03Z

- **Command:** `npx vitest run src/pages/cores/__tests__/settingsFaceRoster.test.tsx src/pages/cores/__tests__/settingsModels.test.tsx src/pages/cores/__tests__/deskModule.test.tsx`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 1c2450c3acab696cb11cde3a5c4d03bf21c8a841

```text

 RUN  v4.1.10 /Users/karol/dev/tools/HoldSpeak

 ❯ web/src/pages/cores/__tests__/settingsModels.test.tsx (14 tests | 14 failed) 7ms
     × lists the profile-backed targets with key + readiness lamps 3ms
     × offers HUB DEFAULT plus every target on all three RUNS ON rows 0ms
     × writes a pointer pick through the settings updater with the one sentinel 0ms
     × tests each destination and offers its discovered models 0ms
     × edits a target through the one write path (/api/inference-targets) 1ms
     × renders the meetings placement rule where the placement is set 0ms
     × never touches a legacy endpoint field 0ms
     × names the local placement and leaves the provider fallback live 0ms
     × names the cloud placement 1ms
     × disables the provider fallback and names the override when a destination is adopted 0ms
     × names a dropped destination pointer and keeps the provider live 0ms
     × names a placement that cannot run 0ms
     × marks exactly one row as the deciding control, in every state 0ms
     × writes the provider fallback through the settings updater 0ms
 ❯ web/src/pages/cores/__tests__/deskModule.test.tsx (4 tests | 3 failed) 4ms
     × states what resets and what survives, as labels 2ms
     × arms before it fires: first press asks, second press resets 0ms
     × a refused reset says so in the danger tone 0ms

⎯⎯⎯⎯⎯⎯ Failed Tests 17 ⎯⎯⎯⎯⎯⎯⎯

 FAIL  web/src/pages/cores/__tests__/deskModule.test.tsx > DeskModule (HS-112-03) > states what resets and what survives, as labels
ReferenceError: document is not defined
 ❯ render web/node_modules/@testing-library/react/dist/pure.js:256:5
 ❯ web/src/pages/cores/__tests__/deskModule.test.tsx:26:5
     24|
     25|   it("states what resets and what survives, as labels", () => {
     26|     render(<DeskModule />);
       |     ^
     27|     expect(
     28|       screen.getByText(/RESETS · NOTES · KNOWLEDGE · AGENTS · WORKFLOW…

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[1/17]⎯

 FAIL  web/src/pages/cores/__tests__/deskModule.test.tsx > DeskModule (HS-112-03) > arms before it fires: first press asks, second press resets
TypeError: Cannot read properties of undefined (reading 'Symbol(Node prepared with document state workarounds)')
 ❯ prepareDocument web/node_modules/@testing-library/user-event/dist/esm/document/prepareDocument.js:10:17
 ❯ Object.setupMain [as setup] web/node_modules/@testing-library/user-event/dist/esm/setup/setup.js:52:5
 ❯ web/src/pages/cores/__tests__/deskModule.test.tsx:36:28
     34|
     35|   it("arms before it fires: first press asks, second press resets", as…
     36|     const user = userEvent.setup();
       |                            ^
     37|     render(<DeskModule />);
     38|     await user.click(screen.getByRole("button", { name: "RESET TO SEED…

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[2/17]⎯

 FAIL  web/src/pages/cores/__tests__/deskModule.test.tsx > DeskModule (HS-112-03) > a refused reset says so in the danger tone
TypeError: Cannot read properties of undefined (reading 'Symbol(Node prepared with document state workarounds)')
 ❯ prepareDocument web/node_modules/@testing-library/user-event/dist/esm/document/prepareDocument.js:10:17
 ❯ Object.setupMain [as setup] web/node_modules/@testing-library/user-event/dist/esm/setup/setup.js:52:5
 ❯ web/src/pages/cores/__tests__/deskModule.test.tsx:49:28
     47|   it("a refused reset says so in the danger tone", async () => {
     48|     resetDesk.mockResolvedValueOnce(null as never);
     49|     const user = userEvent.setup();
       |                            ^
     50|     render(<DeskModule />);
     51|     await user.click(screen.getByRole("button", { name: "RESET TO SEED…

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[3/17]⎯

 FAIL  web/src/pages/cores/__tests__/settingsModels.test.tsx > ModelsModule (HS-112-01) > lists the profile-backed targets with key + readiness lamps
ReferenceError: document is not defined
 ❯ Proxy.render web/node_modules/@testing-library/react/dist/pure.js:256:5
 ❯ web/src/pages/cores/__tests__/settingsModels.test.tsx:77:5
     75| describe("ModelsModule (HS-112-01)", () => {
     76|   it("lists the profile-backed targets with key + readiness lamps", as…
     77|     render(
       |     ^
     78|       <ModelsModule settings={settings} update={vi.fn()} onRefuse={vi.…
     79|     );

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[4/17]⎯

 FAIL  web/src/pages/cores/__tests__/settingsModels.test.tsx > ModelsModule (HS-112-01) > offers HUB DEFAULT plus every target on all three RUNS ON rows
ReferenceError: document is not defined
 ❯ Proxy.render web/node_modules/@testing-library/react/dist/pure.js:256:5
 ❯ web/src/pages/cores/__tests__/settingsModels.test.tsx:92:5
     90|
     91|   it("offers HUB DEFAULT plus every target on all three RUNS ON rows",…
     92|     render(
       |     ^
     93|       <ModelsModule settings={settings} update={vi.fn()} onRefuse={vi.…
     94|     );

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[5/17]⎯

 FAIL  web/src/pages/cores/__tests__/settingsModels.test.tsx > ModelsModule (HS-112-01) > writes a pointer pick through the settings updater with the one sentinel
ReferenceError: document is not defined
 ❯ Proxy.render web/node_modules/@testing-library/react/dist/pure.js:256:5
 ❯ web/src/pages/cores/__tests__/settingsModels.test.tsx:107:5
    105|   it("writes a pointer pick through the settings updater with the one …
    106|     const update = vi.fn();
    107|     render(
       |     ^
    108|       <ModelsModule settings={settings} update={update} onRefuse={vi.f…
    109|     );

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[6/17]⎯

 FAIL  web/src/pages/cores/__tests__/settingsModels.test.tsx > ModelsModule (HS-112-01) > tests each destination and offers its discovered models
ReferenceError: document is not defined
 ❯ Proxy.render web/node_modules/@testing-library/react/dist/pure.js:256:5
 ❯ web/src/pages/cores/__tests__/settingsModels.test.tsx:126:5
    124|
    125|   it("tests each destination and offers its discovered models", async …
    126|     render(
       |     ^
    127|       <ModelsModule settings={settings} update={vi.fn()} onRefuse={vi.…
    128|     );

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[7/17]⎯

 FAIL  web/src/pages/cores/__tests__/settingsModels.test.tsx > ModelsModule (HS-112-01) > edits a target through the one write path (/api/inference-targets)
ReferenceError: document is not defined
 ❯ Proxy.render web/node_modules/@testing-library/react/dist/pure.js:256:5
 ❯ web/src/pages/cores/__tests__/settingsModels.test.tsx:149:7
    147|     vi.useFakeTimers();
    148|     try {
    149|       render(
       |       ^
    150|         <ModelsModule settings={settings} update={vi.fn()} onRefuse={v…
    151|       );

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[8/17]⎯

 FAIL  web/src/pages/cores/__tests__/settingsModels.test.tsx > ModelsModule (HS-112-01) > renders the meetings placement rule where the placement is set
ReferenceError: document is not defined
 ❯ Proxy.render web/node_modules/@testing-library/react/dist/pure.js:256:5
 ❯ web/src/pages/cores/__tests__/settingsModels.test.tsx:169:5
    167|
    168|   it("renders the meetings placement rule where the placement is set",…
    169|     render(
       |     ^
    170|       <ModelsModule settings={settings} update={vi.fn()} onRefuse={vi.…
    171|     );

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[9/17]⎯

 FAIL  web/src/pages/cores/__tests__/settingsModels.test.tsx > ModelsModule (HS-112-01) > never touches a legacy endpoint field
ReferenceError: document is not defined
 ❯ Proxy.render web/node_modules/@testing-library/react/dist/pure.js:256:5
 ❯ web/src/pages/cores/__tests__/settingsModels.test.tsx:180:5
    178|   it("never touches a legacy endpoint field", async () => {
    179|     const update = vi.fn();
    180|     render(
       |     ^
    181|       <ModelsModule settings={settings} update={update} onRefuse={vi.f…
    182|     );

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[10/17]⎯

 FAIL  web/src/pages/cores/__tests__/settingsModels.test.tsx > meetings placement dial (HS-132-10) > names the local placement and leaves the provider fallback live
ReferenceError: document is not defined
 ❯ Proxy.render web/node_modules/@testing-library/react/dist/pure.js:256:5
 ❯ web/src/pages/cores/__tests__/settingsModels.test.tsx:221:5
    219| describe("meetings placement dial (HS-132-10)", () => {
    220|   it("names the local placement and leaves the provider fallback live"…
    221|     render(
       |     ^
    222|       <ModelsModule settings={placed(LOCAL)} update={vi.fn()} onRefuse…
    223|     );

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[11/17]⎯

 FAIL  web/src/pages/cores/__tests__/settingsModels.test.tsx > meetings placement dial (HS-132-10) > names the cloud placement
ReferenceError: document is not defined
 ❯ Proxy.render web/node_modules/@testing-library/react/dist/pure.js:256:5
 ❯ web/src/pages/cores/__tests__/settingsModels.test.tsx:235:5
    233|
    234|   it("names the cloud placement", async () => {
    235|     render(
       |     ^
    236|       <ModelsModule
    237|         settings={placed(

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[12/17]⎯

 FAIL  web/src/pages/cores/__tests__/settingsModels.test.tsx > meetings placement dial (HS-132-10) > disables the provider fallback and names the override when a destination is adopted
ReferenceError: document is not defined
 ❯ Proxy.render web/node_modules/@testing-library/react/dist/pure.js:256:5
 ❯ web/src/pages/cores/__tests__/settingsModels.test.tsx:255:5
    253|
    254|   it("disables the provider fallback and names the override when a des…
    255|     render(
       |     ^
    256|       <ModelsModule
    257|         settings={placed(

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[13/17]⎯

 FAIL  web/src/pages/cores/__tests__/settingsModels.test.tsx > meetings placement dial (HS-132-10) > names a dropped destination pointer and keeps the provider live
ReferenceError: document is not defined
 ❯ Proxy.render web/node_modules/@testing-library/react/dist/pure.js:256:5
 ❯ web/src/pages/cores/__tests__/settingsModels.test.tsx:289:5
    287|
    288|   it("names a dropped destination pointer and keeps the provider live"…
    289|     render(
       |     ^
    290|       <ModelsModule
    291|         settings={placed(

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[14/17]⎯

 FAIL  web/src/pages/cores/__tests__/settingsModels.test.tsx > meetings placement dial (HS-132-10) > names a placement that cannot run
ReferenceError: document is not defined
 ❯ Proxy.render web/node_modules/@testing-library/react/dist/pure.js:256:5
 ❯ web/src/pages/cores/__tests__/settingsModels.test.tsx:313:5
    311|
    312|   it("names a placement that cannot run", async () => {
    313|     render(
       |     ^
    314|       <ModelsModule
    315|         settings={placed({

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[15/17]⎯

 FAIL  web/src/pages/cores/__tests__/settingsModels.test.tsx > meetings placement dial (HS-132-10) > marks exactly one row as the deciding control, in every state
ReferenceError: document is not defined
 ❯ Proxy.render web/node_modules/@testing-library/react/dist/pure.js:256:5
 ❯ web/src/pages/cores/__tests__/settingsModels.test.tsx:331:25
    329|
    330|   it("marks exactly one row as the deciding control, in every state", …
    331|     const { unmount } = render(
       |                         ^
    332|       <ModelsModule settings={placed(LOCAL)} update={vi.fn()} onRefuse…
    333|     );

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[16/17]⎯

 FAIL  web/src/pages/cores/__tests__/settingsModels.test.tsx > meetings placement dial (HS-132-10) > writes the provider fallback through the settings updater
ReferenceError: document is not defined
 ❯ Proxy.render web/node_modules/@testing-library/react/dist/pure.js:256:5
 ❯ web/src/pages/cores/__tests__/settingsModels.test.tsx:358:5
    356|   it("writes the provider fallback through the settings updater", asyn…
    357|     const update = vi.fn();
    358|     render(
       |     ^
    359|       <ModelsModule settings={placed(LOCAL)} update={update} onRefuse=…
    360|     );

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[17/17]⎯


 Test Files  2 failed | 1 passed (3)
      Tests  17 failed | 6 passed (23)
   Start at  20:31:05
   Duration  342ms (transform 334ms, setup 0ms, import 687ms, tests 14ms, environment 0ms)
```

### Captured run — 2026-08-18T02:32:22Z

- **Command:** `bash -c cd web && npx vitest run src/pages/cores/__tests__/settingsFaceRoster.test.tsx src/pages/cores/__tests__/settingsModels.test.tsx src/pages/cores/__tests__/deskModule.test.tsx`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 43e65b3d6a16df6ce4b890248ac39fa53d8c913b

```text

 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web


 Test Files  3 passed (3)
      Tests  23 passed (23)
   Start at  20:32:23
   Duration  1.32s (transform 399ms, setup 195ms, import 778ms, tests 855ms, environment 883ms)
```
