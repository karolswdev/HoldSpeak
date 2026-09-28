VERDICT: DO-NOT-RATIFY

FINDINGS:

1. **Delivery’s retry rule still loses part of the confirmation — r1 finding 4 is only partly paid. Tenets 3/7; Article XI.3.** Boards 6b–6d correctly show refusal, uncertainty and same-update retry. But the held confirmation contains only `{key, to}`; the request takes its target from `current.id`. Back and opening another update preserve the old uncertainty state.

   I reproduced: lose the answer on update A → Back → open B → B inherits the locked `Lena` field and Retry → the same command key is sent to **B’s URL**, producing `idempotency_conflict`. The face then calls this `KEY USED WITH OTHER TO`, although To never changed. The README’s claim that this conflict is unreachable is therefore false.

   Evidence: `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-items-canvas/harness/proposedUpdateController.ts:110`, `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-items-canvas/harness/proposedUpdateController.ts:146`, `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-items-canvas/harness/proposedUpdateController.ts:276`, [probe result](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-681-r2-7n0yxpif/retry-target.json).

2. **The draft repair introduces viewport-dependent content layout. Tenets 5/6; UX-CANON D.** Delivery board 8 now fits at 393, but the mic’s move into flow, child sizing and editor grid repair sit inside `@media (max-width: 420px)`. Canon requires content layout to follow the `surface` container. A narrow window on a wide desktop does not receive these repairs. Device target sizing may remain device-dependent; the content changes may not.

   Evidence: `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-items-canvas/harness/canvas.css:74`, `docs/internal/UX-CANON.md:119`. The list’s fold itself now correctly uses a container query.

3. **The pointer evidence does not yet meet r1’s condition. Tenets 5/6; UX-CANON C.** Including menus and footers is paid. However, the Room/delivery and list probes use `elementFromPoint` without a real pointer pass. All three harnesses sample centre plus four corners, omitting edge midpoints. Grant does perform real pointer moves. The recorded results support five-point hit-testing, not the complete canon claim.

   Evidence: `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-items-canvas/harness/shoot.py:175`, `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-list-canvas/harness/shoot.py:315`, `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-grant-canvas/harness/shoot.py:127`, `docs/internal/UX-CANON.md:100`.

4. **The remaining r1 accounting is substantially good.** Board references below are under `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/`, in the named canvas’s `shots/` directory.

   | r1 finding | Disposition and evidence |
   |---|---|
   | 1 — principal rulings | **Preserved.** ITEMS has no Add; delivery retains separate confirmations and the mistaken mark; grant retains LIVE authority with Remote Access OFF. Items 1b, delivery 6, grant 7. |
   | 2 — lost desk orphans; contradictory revoke fence | **Paid for the canvas.** Grant boards 6/7 show both orphan families; 10 shows the last orphan gone with its receipt retained; 11 distinguishes credential revocation. The receipt well is outside the ledger branch. `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-grant-canvas/harness/main.tsx:423`, `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-grant-canvas/README.md:104`. |
   | 3 — hidden project controls | **Paid.** Grant boards 2/3 show the library Projects disclosure, and PROJECT has no filing verb. `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-grant-canvas/harness/main.tsx:396`. |
   | 4 — delivery failure/retry | **Partly paid.** Boards 6b–6d fix the original failure words and recipient lock; finding 1 above remains. |
   | 5 — Room/delivery geometry and Back | **Shown repairs paid; layout/proof conditions remain.** Items 1b/1c show readable chips and clear SOURCES at 393. Delivery 8 fits; 7a follows Back. Recorded `_back` shows one successful click at each width. `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-items-canvas/harness/ProposedUpdatePosture.tsx:518`. Findings 2/3 above qualify closure. |
   | 6 — list/menu | **Visual corrections paid.** List board 3 has ten 44 px menu rows, Delete ending at y=841 within 852; board 4 has no page overflow; board 7 shows real nonzero Attention. The menu participates in scanning and the fold uses `@container surface`. `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-list-canvas/harness/shoot.py:152`, `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-list-canvas/harness/canvas.css:119`. Pointer qualification remains. |
   | 7 — dishonest item states | **Paid.** Items 1b distinguishes MISSED and DROPPED; board 4 shows ITEMS UNAVAILABLE with Retry; board 3 omits a genuinely empty section. `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-items-canvas/harness/ProposedProjectRoomCore.tsx:988`. |

5. **The three disclosed opens do not independently block this canvas sitting.** Keep the Room chrome and Speak/Submit ownership failures as named library/build debt. Keep the 1440 RECEIPTS overlap as Room build debt: items boards 1a/2a show it, while 1c exposes the section after scrolling; the chartered F10 repair specifically names 393. Grant board 11’s vertical offset needs diagnosis during integration, but the shown receipt and footer remain visible. None warrants claiming a clean production face. Evidence: `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-items-canvas/README.md:62`, `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/story-03-the-rooms-face-tells-the-truth.md:19`, grant `shots/a/11-credential-revoked-a-393.png`. The expiry mismatch is correctly ledgered at `pm/roadmap/holdspeak/BACKLOG.md:1332`.

6. **The seven owner prompts now cover appropriate presentation choices, with appropriate recommendations.** I support ITEMS after NEEDS YOU and omitted when empty; `DELIVERED ×N`; confirmation above the body; grant set A; the visible inline Projects disclosure; the proposed selection colours; and folded list metadata. Late health, mistaken-mark retention, palette compatibility and reachable menus are correctly stated as settled requirements. Evidence: the four canvas READMEs at items `:47`, delivery `:61`, grant `:70`, list `:79`. These choices need no new owner policy question.

CONDITIONS:

Before presenting the four-canvas package as ready:

- Bind an unresolved confirmation to its original update as well as its key and recipient. Settle and demonstrate Back → another update → return, without transferring uncertainty or retry authority between updates. Update the words and fence sketch together.
- Move the draft’s content repairs to container-based layout; keep device target sizing in the canon’s permitted location. Recapture the affected composition.
- Complete real-pointer and hit-test checks at centre, edges and corners for touched controls, including menu and footer controls. Preserve the disclosed inherited failures separately.

These are bounded canvas corrections, not a demand to build the backend. Give the three accepted opens explicit build/BACKLOG homes.

MISSED:

1. Highest owner cost: uncertainty from one update contaminates another update’s delivery controls.
2. Next: a repair that follows device width rather than window width.
3. Next: “all owned” evidence that omits part of the required pointer procedure.
4. Small cleanup: the ITEMS review-page caption still says `ITEMS 3` while board 1a shows five; source is `story-03-items-canvas/harness/build_review.py:16`.

TUESDAY: The normal items, grant and list jobs are understandable; delivery still makes a tired owner carry an unexplained retry conflict between two reports.

UNKNOWN: Reviewed `eb3b7d55` in fresh worktree `/Users/karol/dev/tools/wt-astra-pr681-r2-eb3b7d55`, reading source, review pages, recorded facts and relevant shots at both widths. The fresh retry probe used two updates minted through a real isolated hub, then the unchanged canvas controller and delivery shim in a minimal React harness; it was not a full-face or atlas walk. No full suite or fresh complete pointer run. Grant transitions remain static compositions; durable replay, authority enforcement and real receipts remain build verification. Grant board 11’s offset cause remains unknown. `git diff --check fe85952fd..HEAD` passed; the review worktree is clean. No repository files changed.