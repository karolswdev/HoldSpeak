VERDICT: DO-NOT-RATIFY

FINDINGS:

1. **Blocker: a known FAILED send can still show the previous SAVED receipt. — Tenets 3/7; Articles V/VI.** Reproduced at both widths: save successfully → make the folder unwritable → fail subsequent sends-list reads → Send again. The POST answers `failed / permission_denied`, but the header and expanded receipt still show the earlier success. The returned record is stored as `settled`, then ignored by the renderer, which uses stale read data. Evidence: `web/src/features/channels/SendWell.tsx:290`, `web/src/features/channels/SendWell.tsx:405`, [response and rendered facts](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-697-fhgppyoz/probes-with-icons/settled-read-failed-1440.json), [shot](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-697-fhgppyoz/probes-with-icons/settled-read-failed-1440.png).

2. **Blocker: Remove swallows failure and closes the row. — Tenet 3; Article VI.** At both widths, a failed DELETE leaves the destination active but closes its details without a named failure or recovery action. Evidence: `web/src/pages/cores/connections/Destinations.tsx:344`, [stored state and face](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-697-fhgppyoz/probes-with-icons/remove-failed-393.json), [shot](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-697-fhgppyoz/probes-with-icons/remove-failed-393.png).

3. **Microseconds reduce collisions; they do not establish dispatch order. — Tenets 1/3/7.** Using real producers with only the boundary clock pinned: prepare A → inline B succeeds → A fails. Equal microseconds make `latestFor` select B’s older success at both widths. The timestamp is also sampled before the transaction lock. For guaranteed ordering, use a persistent increasing dispatch sequence allocated inside that transaction; preparation row order or an arbitrary ID tie-break is insufficient. This controlled tie is **not an additional part-one blocker**; its natural frequency was not established. Evidence: `holdspeak/services/channel_service.py:337`, `web/src/features/channels/SendWell.tsx:302`, [producer records and rendered result](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-697-fhgppyoz/probes-with-icons/equal-clock-393.json).

4. **The covered canvas fixes otherwise hold, with one additional deviation. — Tenets 2/3/5/6.** Compared the shipped shots with the corresponding canvases at both widths and independently reproduced **8/8 glass tests**. Setup returns without reload; prepared failure/discard results persist; normal latest-failure reopening is correct; UNKNOWN remains separate; Retry preserves its key; unreadable states are named. The declared SAVED wording, folder-only prepared preview and path clamp are reasonable. However, B10 omits the canvas’s **Checked time**: `pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-04-send-canvas/harness/Destinations.tsx:313`, `web/src/pages/cores/connections/Destinations.tsx:331`. “Every ratified state is faithful” would overstate this result. [Verification summary](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-697-fhgppyoz/review-summary.json).

5. **The “every board” proof claim is too broad. — Tenet 3; Article IX.** There are **84 shots, 80 measured boards**. Armed Discard and Remove at both widths use direct screenshots, bypassing the board visibility, byte and pointer checks. Their pictured controls are visible; this is a proof qualification. Evidence: `tests/e2e/test_philo10_04_send_face_glass.py:525`, `tests/e2e/test_philo10_04_send_face_glass.py:746`.

CONDITIONS:

Fix findings 1–2 and fence their rendered transitions through real producers at both widths, with implementation and tests together. Merge returned Send records into the shared result source without allowing stale reads to replace them. Keep Remove failures visible with recovery.

Record finding 3’s ordering limitation for the concurrency follow-up. Restore or explicitly ledger B10’s missing time; measure the four armed shots or narrow the proof claim.

MISSED:

1. Highest owner cost: a refresh failure hides an already-known send failure behind green success.
2. Next: failed removal provides no explanation.
3. Lower: timestamp precision was treated as ordering, and aggregate proof obscured four exceptions.

TUESDAY: The normal file workflow works; the owner still cannot trust the displayed result when a refresh or Remove fails.

UNKNOWN: Reviewed PR #697 at `84657927..8d7fa1ea` in a fresh, unchanged worktree. Remote-channel boards, running-send transitions, restart-on-glass and steward destination selection remain unverified here. Full suites were not rerun. The real Phase 9 manual-delivery atlas case passed at both widths; exported-source runs lack Git revision metadata, qualified by the [matching source manifest](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-697-fhgppyoz/source-manifest.json). No repository files changed.