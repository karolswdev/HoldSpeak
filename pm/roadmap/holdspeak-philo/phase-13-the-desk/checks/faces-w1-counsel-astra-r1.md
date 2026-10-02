# Counsel on built — Astra (Codex `gpt-6-astra`, xhigh): PR #725 faces lane wave 1, r1

Session `01a0fa6d-1a34-7691-9a65-c14aa074fbc9`. Verbatim.

VERDICT: DO-NOT-RATIFY

FINDINGS:

1. **P1 — Room Retry can erase newer words.** After Save fails, type more, then press Try again: the stored callback resends the earlier text, replaces the editor with it, and clears `dirty`. I reproduced this: both requests contained `"first edit"`; the newer words disappeared. The callback captures the failed render’s `save`. **Tenets 3 and 7.** Evidence: `web/src/features/project-room/update/useUpdateController.ts:175`, `web/src/features/project-room/update/UpdatePosture.tsx:538`.

2. **P2 — Voice “Open Setup” opens New Project.** I reproduced the missing-model failure and pressed the new button: it dispatched `project-setup`. That application loads `DoorCore` and is named “New Project”; the actual Setup application is `configure-setup`. **Tenet 3; UX A.11.** Evidence: `web/src/desk/components/MicButton.tsx:459`, `web/src/desk/applications.ts:348`.

3. **P2 — People can clear a failed read without recovering the person.** If the relationship-detail request fails, Try again calls only `/api/people/readiness`. A ready answer clears the error without fetching the missing detail. My rendered probe recorded **one** relationship read before and after Retry. This can leave existing notes absent while the failure disappears. **Tenets 3 and 7.** Evidence: `web/src/pages/cores/PeopleCore.tsx:202`, `web/src/pages/cores/PeopleCore.tsx:243`.

4. **P2 — Raw server text remains in Ask’s hover UI.** The refusal’s model path moves into `title={errorDetail}`. A tooltip is still product UI. The static fence merely prohibits `setError(r.output)` and therefore passes this implementation. Mic’s sentences likewise move into titles, explicitly permitted by the new fence. This does not establish “no raw server text or prose.” **Tenet 4; UX A.3/A.10.** Evidence: `web/src/desk/components/AskPanel.tsx:348`, `web/src/desk/__tests__/philo13FacesDoNotLie.test.tsx:52`.

5. **A4’s chrome fix is at the right seam.** All three production mounts pass the stored ID, including the Thought transition. I found no omitted card mount. The glass tests exercise all three mounts, qualified and bare IDs, and the subsequent Chair Retry. The `pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-05-shots/j1-retry-reached-393.png` supports the result. However, this proves representative opener paths, not the acceptance’s literal “every opener.” Record that distinction. Evidence: `web/src/desk/components/Pullout.tsx:73`, `tests/e2e/test_philo13_05_close_glass.py:130`.

6. **The core fences have substance, but recovery coverage is incomplete.** The glass fixtures use real routes and `save_meeting`; Record observes the hub’s 501. I inspected both actual atlas cases’ red/green observations at both widths and verified isolated DB paths. Independently, the five changed test files passed **40 tests**; four files against pre-fix source produced **14 failures, 19 passes**. Settings retains both switch states and the forbidden-name assertion. Mic retains positive/negative audio-retention checks. Those guards were rehomed, not simply removed. But the `tests/e2e/test_philo13_04_faces_glass.py:201` covers Brief and People, with no Room-publish or Ask recovery walk. Findings 1–3 pass the shipped fences. **Tenets 3/4; Article IX.**

7. **H-A3 accepted for Astra’s lane.** The list producer lacks the stored-summary fact; the `pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-04-shots/meetings-stored-1440.png` visibly shows `OFF` beside `SUMMARY STORED`. Deliver a separate stored-summary boolean derived from the same persisted summary as detail, independent of configuration and run status. Fence summarized and unsummarized meetings through real producers and the list route, including search. Muad’Dib owns the rail wiring in `CatalogRail`/its state helper. A3 stays in progress until both halves merge. Evidence: `holdspeak/db/meetings.py:628`, `web/src/pages/cores/history/CatalogRail.tsx:99`.

CONDITIONS:

- Fix findings 1–4 and fence the rendered recovery transitions, including the actual destination of Open Setup.
- Supply the missing Room/Ask/voice evidence and the orchestrator’s quiet full-suite result. Both capture commands pipe through `tail` without `pipefail`; preserve the verification command’s failure status.
- Record H-A3 and A4’s precise coverage. H-A3 need not block an honestly partial A3 merge after the defects above are repaired.

MISSED:

Highest owner cost: lost update edits → wrong recovery destination → missing person detail presented without an error → raw diagnostics in tooltips. Two inherited close callers also bypass the repaired callback: `web/src/desk/pullouts/CoderPullout.tsx:177` and `web/src/desk/pullouts/MeetingPullout.tsx:107`. I reproduced Watch live leaving `coder:s1` open. Ledger these separately from the verified chrome Close fix.

TUESDAY: Close and refused Record are substantially better; recovery still risks losing his words or sending him to the wrong task.

UNKNOWN: I did not run new live walks or the full Python suite. New probes used archived source outside the worktree with controlled failures. The PR advanced to `1467d917` during review; this verdict covers `82353f48` and `07aa76e3`, excluding canvas work. I changed nothing in the repository tree.