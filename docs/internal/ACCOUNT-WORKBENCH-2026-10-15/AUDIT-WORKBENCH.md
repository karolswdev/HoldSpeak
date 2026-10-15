# Workbench source audit — 2026-10-15

**DRAFT — UNCHECKED, awaiting Muad'Dib. HOLD FOR BUILD.**

Historical pre-build audit snapshot. Root subsequently settled DESIGN.md,
built the bounded direction through workers, and recorded finished source
review and actual verification in README.md. The original unknowns below
describe the audit's source-only state; this is not a Muad'Dib check.

Source at `3d46ffdc3`, worktree `wt-account-layout-20261015`. Read the Two Brains protocol, fast cycle, UX Canon, and Constitution. No code changes, tests, browsers, installs, or owner-state access. These are source findings; live severity and geometry remain unverified.

The real door is `open-workbenches` / `/workbenches` (`web/src/desk/applications.ts:287`). A home card opens `workbench:<id>` (`web/src/pages/cores/WorkbenchesHomeCore.tsx:123`); `web/src/desk/DeskApp.tsx:262` mounts its object window. Create opens the chooser (`web/src/desk/store/dataSlice.ts:318`); its exits POST a template or blank workbench and open the returned ID (`web/src/desk/components/WorkbenchTemplatePicker.tsx:67`).

## Three current findings

1. **The main instruction field loses the shared field material and hides long instructions in one line.** `web/src/desk/components/WorkbenchWindow.tsx:1762` explicitly leaves the inlet as a raw `input type="text"`; `web/src/desk/components/workbench-config.css:423` makes it transparent, borderless, and without an outline. The narrow rule at `:686` changes width and height, but the instruction cannot wrap. This is the first productive control the architect uses, including the full task body saved at `WorkbenchWindow.tsx:1340`. The claim in the inline comment that a combobox cannot use the library field is stale: `web/src/desk/surface/gadgets.tsx:300` supports native combobox attributes through `inputProps`; the shared field's material and focus treatment live in `web/src/desk/surface/gadgets.css:327`. A longer instruction is preserved correctly; its presentation is the gap. **Tenets 3, 5, 6, 7; UX Canon B and D.**

2. **The two Run doors disagree about a known missing engine.** The title bar refuses Run when `engine === "none"` (`web/src/desk/components/WorkbenchWindow.tsx:1569`), but the empty Runs wing receives only agent binding (`:1964`). `web/src/desk/components/workbench/WorkbenchRunsWing.tsx:45` consequently offers **Run now** for a bound agent even when the engine is known absent. Its callback directly reaches `triggerRun` (`WorkbenchWindow.tsx:1970`), which has no matching prerequisite guard (`:1368`). The real producer returns the named 409; `tests/integration/test_workbench_run_no_engine_route.py:33` documents that exact case. The owner is invited to press a verb already known to fail. **Tenet 3; UX Canon A.10–11.**

3. **Home progress can call active or failed items DONE, and an active run FAIL.** `web/src/pages/cores/WorkbenchesHomeCore.tsx:142` derives DONE as `item_count - pending_count`. The producer counts all items at `holdspeak/services/workbench_service.py:693`, and only pending items at `:694`; claimed and failed rows therefore inflate DONE. Separately, `WorkbenchesHomeCore.tsx:185` maps every non-completed run to FAIL. The real runner inserts `status='running'` at `holdspeak/services/workbench_runner.py:229`; the Runs wing correctly recognizes that state at `web/src/desk/components/workbench/WorkbenchRunsWing.tsx:56`. A still-running job can have conflicting labels across the two faces. **Tenets 3 and 7; Article VI.1.**

## Focused proof available

- `web/src/desk/components/__tests__/workbenchEditing.test.tsx:316` proves long-instruction custody, not visible instruction layout. Preserve its draft, references, and Retry behavior in any face change.
- `web/src/desk/components/__tests__/workbenchOperates.test.tsx:218` proves the title-bar no-engine door; `web/src/desk/components/workbench/WorkbenchRunsWing.test.tsx:22` proves the empty Run now callback. Neither covers their combined **bound agent + no engine + empty Runs** state.
- `web/src/pages/cores/__tests__/workbenchesHome.test.tsx:18` supplies only a completed run; its three tests cover read recovery. It has no running run or mixed item-state case.
- Configuration wiring remains covered at `workbenchEditing.test.tsx:459` and `web/src/desk/components/__tests__/workbenchAutomations.test.tsx:91`; run frames at `web/src/desk/components/__tests__/workbenchFrames.test.tsx:126`; the generic face sweep is `tests/e2e/test_desk_sweep.py:1055`.

The current result has one Material render and a real Open artifact door (`WorkbenchWindow.tsx:824`, `:854`). Runs and Memory now name failed reads and retain known rows (`:1962`, `:1979`); those earlier defects are not findings here. Configuration replaces the selected wing's body (`:1695`, `:1958`, `:1976`).

**Tuesday:** the architect can queue a real task and open its output, but the instruction affordance and conflicting Run/progress states slow that job. **Unknown:** actual 1440/393 appearance, pointer and keyboard behavior, and the owner's intended screen. Root owns live proof and the face direction.
