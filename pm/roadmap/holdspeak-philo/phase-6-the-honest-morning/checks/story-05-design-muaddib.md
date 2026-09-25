Reading is done. Here is the check.

**VERDICT: RATIFY-WITH-CONDITIONS**

**FINDINGS**

1. **The cause is narrower than the diagnosis says, and the raw data already names it.** The diagnosis states "the run does not record request start times, so the exact member of the overlapping refresh pair is unidentified" and offers "the hub's read is still serving the pre-PUT snapshot" as an alternative. The continuous observation records start times. At 393 the blank collection GET started at 2287 ms and resolved at 2297 ms. The PUT started at 3928 ms. No other decisions GET happens until 4241 ms. The unreadable frame lands at click+159 ms, about 4087 ms. So the read finished 1.6 s before the write began, and its result was committed 1.8 s after it resolved. The only mechanism for that delay is `Promise.all([loadAll(), loadSetup()])` at `web/src/desk/store/dataSlice.ts:164-168` waiting on a slower sibling. The 1440 run repeats it: GET 2265, PUT 3869, unreadable at 3946. The refresh that committed is the CREATE's `desk_changed` refresh, since the POST resolved at 1984 and the hook waits 300 ms (`web/src/desk/useDeskChangedRefresh.ts:38,52`), landing at 2286. Diagnosis must record this. It is acceptance criterion 1, and the "still serving the pre-PUT snapshot" hypothesis is refuted by the trace. Tenet: help and accelerate, since a wrong cause on file misleads the next reader.

2. **The retained test still asserts the retracted hypothesis as the pre-fix failure.** `web/src/desk/__tests__/philo605DecisionBodyDiagnosis.test.tsx:1-6` (header), and the third test's comments at the `expect(decisionSection?.textContent).toBe("Decision")` line say "This is the pre-fix failure the repair must fence." The diagnosis and design say the held-prop case is a negative control only. A green test whose comment names the wrong cause is a lying fence in the sense of the 2026-09-08 scar. Rename and re-comment it as a control, or drop it.

3. **The unreachable-kind retention is a second behaviour change and is broader than the story.** Design "Refresh fence" last paragraph: retain the current bucket for any unreachable kind. Today `loadAll` (`web/src/desk/api.ts:626-636`) returns an empty bucket plus `status[kind]="unreachable"` and the READ receipt at `dataSlice.ts:173-178`. Changing it for all eleven kinds changes what every zone shows on a hub hiccup. It is probably the right behaviour for a Tuesday, but it is not the S4 repair and it has no fence of its own in the plan. The failed-save-plus-failed-read case only needs the protected item kept when its bucket is unreachable, and only while its rollback refresh is the one in flight. Tenet 1: no over-engineering. Either scope to protected items, or name the widening in the story and phase status as deliberate with its own red test.

4. **A stale refusal's Retry replays a superseded patch.** Design "Write result fence" step 2 keeps `reportWriteFailure` for a stale refusal. The receipt's retry closure at `dataSlice.ts:347-349` re-sends the old `patch`. If write 1 is refused after write 2 succeeded, the face shows SAVE FAILED for text the owner already replaced, and Retry would overwrite the newer text with the older. Either skip the receipt when the version is stale, or retry with the current item. The seventh test does not cover this order because it resolves the refusal before the success.

5. **Items absent from the incoming bucket.** Preserving a protected item that the hub's read does not return also resurrects an item deleted from another surface during the write window. Cheap to accept, but the design should say so in one line rather than leave the reader to infer it.

**CONDITIONS**

- Diagnosis records the refresh-commit-held-by-slower-sibling cause with the two start times, and drops the "hub still serving pre-PUT snapshot" hypothesis.
- Test 3 re-labelled a negative control in header and inline comments, or removed.
- Unreachable retention either scoped to protected items or declared as deliberate widening with its own fence and a phase-status line.
- Stale refusal does not post a receipt whose Retry replays a superseded patch.
- Story criterion 2 reworded as proposed: observer armed before the click, first read frame readable, every frame to the terminal observation readable, the continuous fence is the pre-fix red. Add "the first-frame-only assertion was green on main" so nobody later claims a first-frame red. The two raw red directories under `docs/internal/philo/phase-6/body/` are the honest evidence for that.

**MISSED**

1. **Every desk refresh takes about 1.8 s on the rig.** The stale commit was only visible because the whole-desk read is that slow. The same delay puts the owner's every write behind a 1.8 s window where any earlier refresh can land. Not this story, but it belongs on BACKLOG with the trace as evidence.
2. **Delete has the same race in the other direction.** `deletePrimitive` and `renameZone` patch `items` optimistically and then refresh, with no version. A refresh that started before a delete can resurrect the deleted item for a beat. Same class, ledger it, do not build it here.
3. **The design carries no check of `loadSetup` rejecting.** `Promise.all` throws on a setup failure and the rollback refresh then rejects out of `refused`. Pre-existing, one line to note.

**TUESDAY:** Yes. After the fix the owner presses Done and the text stays; a refused save shows the old text with SAVE FAILED and Retry. Nothing new to learn.

**UNKNOWN:** Which sibling in `loadAll` holds the commit for 1.8 s. The observation's hub log is 800 bytes and carries no per-request timings, and I ran no hub. I also did not run the probe test; I read Astra's `probe-tests.log` claim of 2 passed, 5 failed and the test bodies, which are consistent with it.

Recommendation: pay the conditions in the docs and the test comments, then let Luna build the minimal repair. The version map, the refresh snapshot, and the synchronous rollback are the right shape and the right size.

Claude session: `1f5b1e23-c8c4-464f-8fde-39732b368924`. Raw check record: `docs/internal/philo/phase-6/body/design-check-response.json`.
