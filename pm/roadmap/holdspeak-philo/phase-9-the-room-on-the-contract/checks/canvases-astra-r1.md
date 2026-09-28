VERDICT: DO-NOT-RATIFY

FINDINGS:

1. **The principal rulings are represented correctly. — Tenets 1/3/7 satisfied.** ITEMS has no Add control. Mark delivered remains available after Copy and reopening. Pending disables the field; the recorded double-click produces one confirmation; Priya and Tomas remain separate entries, including the mistaken mark. The project-grant canvas shows a LIVE orphan with Remote Access OFF and a Stop control. **R4-3’s required boards are present.** Delivery transitions exercise the shim; grant boards are static compositions, not transition proof. Evidence: `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-items-canvas/harness/shoot.py:339`, `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-grant-canvas/harness/main.tsx:453`, `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-delivery-canvas/shots/6-mistake-kept-393.png`.

2. **The grant composition loses an existing authority state, and its fence describes an impossible result. — Tenets 3/7; Article VI.** The proposed `Wire` and renderer omit Phase 7’s desk-grant `delegations[]` orphan rows. The current product renders those rows with Stop filing. Extending the face must preserve them, including alongside project orphans with Remote Access OFF. Evidence: `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-grant-canvas/harness/main.tsx:88`, `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-grant-canvas/harness/main.tsx:381`, `web/src/pages/cores/SettingsCore.tsx:869`.

   The fence says credential revocation first revokes the grant, **then leaves an orphan with Stop**. A revoked grant cannot simultaneously be LIVE. Separate owner credential revocation—grant revoked, row removed, receipt retained—from restart/credential loss leaving a LIVE orphan. Draw the final orphan disappearing after Stop, with its receipt still reachable. Evidence: `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-grant-canvas/README.md:102`.

3. **The project controls are hidden behind an unmarked interaction. — Tenets 2/3; UX-CANON D.** The closed PROJECT row shows “Allow filing” and “Revoke credential”; its useful per-project controls require discovering that the row opens. This is not merely inherited: the canvas introduces `expands={capable}` where the current credential row has `expands={false}`. Add a visible library disclosure affordance on the canvas. Also resolve the irrelevant filing control on a PROJECT-only credential before presenting this as the intended face. Evidence: `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-grant-canvas/harness/main.tsx:348`, `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-grant-canvas/shots/a/2-live-a-393.png`.

4. **Delivery failure is neither drawn nor truthful enough. — Tenets 3/4; Articles V/VI.** Every caught error becomes `NOT MARKED`; the actual reason is discarded. A lost response after a committed confirmation does not establish that nothing was marked. Moreover, the controller retains only the command key while the recipient becomes editable again: changing To before retry can reuse that key with a different payload. The canvas needs a named refusal and an uncertain-result/retry state, with a settled rule for retaining the original confirmation’s payload. Backend concurrency enforcement can wait for build; these visible states cannot. Evidence: `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-items-canvas/harness/ProposedUpdatePosture.tsx:94`, `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-items-canvas/harness/proposedUpdateController.ts:245`.

5. **“Inherited” does not make the displayed geometry ratifiable. — Tenets 5/6; UX-CANON A/C.** Fix the ITEMS reason/why chips to 12 px **on the canvas**. For delivery, likewise fix the 10/11 px text, raw citation controls, 4.29:1 egress chip and draft-editor overflow. These repairs change wrapping, spacing and control dimensions. Represent the planned Ask-well repair in the Room composition too; its present footprint materially affects the proposed section’s visibility. Evidence: `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-items-canvas/README.md:51`, `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-delivery-canvas/README.md:58`, `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-items-canvas/shots/1a-late-first-view-393.png`.

   The failed Back transition also blocks a ratifiable delivery loop at 393; Escape is not an adequate phone return path. Diagnose and demonstrate Back working before ratification. The tall history rows are readable and are **not independently a blocker**; their space cost is a genuine layout choice. Evidence: `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-items-canvas/harness/shoot.py:364`.

6. **The list’s menu correction was measured against an incomplete bar. — Tenets 5/6.** The recorded Delete row occupies y=813–841: **28 px**, whereas chrome menu rows must be at least 44 px at 393. Growing those rows changes the panel placement being ratified. The text scan also excludes the portalled menu, so its zero-small-text result does not cover that face. Evidence: `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-list-canvas/shots/facts.json:2841`, `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-list-canvas/harness/shoot.py:108`, `docs/internal/UX-CANON.md:100`.

   Also resolve board 4’s horizontal overflow, draw a real nonzero Attention state, and use the required container layout on the canvas. “The build picks one” is not an available choice between viewport and container queries under current canon. Evidence: `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-list-canvas/README.md:80`, `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-list-canvas/harness/canvas.css:74`.

7. **ITEMS has two unshown dishonest states. — Tenets 3/7; Article VI.** `missed` and `dropped` milestones receive the same green success check as `reached`. A failed items read becomes `[]`, making the section disappear exactly as if the project had no items. Draw a missed milestone with an appropriate state and distinguish unavailable items from an empty project. These are small corrections to the proposed visual contract. Evidence: `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-items-canvas/harness/ProposedProjectRoomCore.tsx:954`, `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-items-canvas/harness/ProposedProjectRoomCore.tsx:988`.

CONDITIONS:

Before ratification, correct findings 2–7 in the canvases and recapture the affected states at both widths. Include the menu and footer in geometry checks, and prove pointer ownership for the touched controls. Keep corrected words and their fences together.

The owner’s genuine choices and my recommendations are:

| Canvas | Recommendation |
|---|---|
| ITEMS | After NEEDS YOU; omit the empty section. Counting late milestones is already chartered, not a new fork. |
| Delivery | Prefer `DELIVERED ×N` and the confirmation controls above the body. Retaining mistaken marks acknowledges the settled limitation. Remove the suggestion that the latest recipient is necessarily “the right one”: several valid recipients are explicitly supported. |
| Grant | Prefer set A’s concrete words and an inline project list, with a visible opening affordance. Palette compatibility is a correctness constraint, not a preference. |
| List | Prefer the proposed selection colors and folded metadata. Keeping menus reachable is mandatory; ratify their appearance after compliant sizing. |

The harness stand-ins are **honestly disclosed for design review**: real item/credential producers, derived proposed health, session-storage deliveries, and static projected grants. They establish the shown compositions, not durable delivery, authority enforcement or kernel receipts. Fix the contradictory grant fence; retain those qualifications.

During build, verify real-producer replay, concurrent duplicates, lost responses, restart persistence, atomic receipt linkage and rendered disappearance transitions through the actual atlas cases. No backend implementation is required merely to redraw these canvases.

The credential POST/GET expiry mismatch belongs in the backend repair ledger, not the canvas gate. GET converts monotonic time to epoch; POST returns the raw value. Settings uses the POST token and then rereads GET, so this path does not display the POST expiry. Evidence: `holdspeak/web/routes/mcp_http.py:237`, `holdspeak/web/routes/mcp_http.py:330`, `web/src/pages/cores/SettingsCore.tsx:699`.

MISSED:

1. Highest owner cost: authority disappearing from the proposed Settings composition, and no visible way into project grant controls.
2. Next: an uncertain delivery reported as “not marked,” with retry payload semantics unsettled.
3. Next: menu placement declared improved using undersized rows and a scan that excludes the menu.
4. Next: missed milestones painted successful and failed reads painted empty.
5. Avoidable owner effort: asking him to approve settled behavior or mandatory compliance as though each were a design fork.

TUESDAY: At 393, ITEMS is understandable once reached; delivery’s normal confirmation is clear but its return/error loop fails; grant controls require discovery; the list is readable but its menu and overflow are not ready.

UNKNOWN: Reviewed `fe85952f` in fresh worktree `/Users/karol/dev/tools/wt-astra-pr681-review`, reading the charter, source artifacts, harnesses, recorded facts and shots at both widths. No fresh browser/atlas run or full suite; Back’s cause and board 4’s overflowing element remain unverified. `git diff --check HEAD^` passed; the worktree is clean. No repository files changed.