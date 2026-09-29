VERDICT: DO-NOT-RATIFY

FINDINGS:

1. **B11 presents historical acceptance as current sender verification. — Tenets 3/7; Article VI.** Reproduced at both widths: a real send accepted with its clock pinned to August 1 → replace the key through the real producer → Check. The face shows **SENDER VERIFIED** and today’s **Checked** time, with no provider call or historical qualification. Reading the last answer is acceptable; this wording overclaims. Evidence: `holdspeak/services/channel_service.py:209`, `web/src/pages/cores/connections/Destinations.tsx:243`, `:362`; [producer records and face text](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-697-r2-otr2v2t9/email-probes/old-answer-393.json), [shot](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-697-r2-otr2v2t9/email-probes/old-answer-393.png).

2. **A known pre-boundary lock refusal becomes UNKNOWN on the face. — Tenet 3; Articles V/VI.** An actual competing file lock produces HTTP 503 with a terminal `refused / lock_timeout` receipt, zero CLI calls and no dispatch. The client recognizes named refusals only for 4xx, so it displays **NO ANSWER · RESULT UNKNOWN**. After release, Retry retrieves the same refusal as 409; only then does the face show **REFUSED · LOCK TIMEOUT · NOTHING SENT**. Reproduced at both widths. Evidence: `web/src/features/channels/channels.ts:325`, `SendWell.tsx:313`; [responses and rendered transitions](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-697-r2-otr2v2t9/timeout-face/lock-timeout-393.json).

3. **The Atlassian glass fixture repeats the lying-producer scar. — Tenet 3; Article IX.** It inserts `wpc-{provider}-{ref}`; production reads `wpc_{provider}_{ref}`. The supposedly checked B10 board therefore shows **NEVER CHECKED**, and its assertion merely compares that result with the same mistaken lookup. Evidence: `tests/e2e/test_philo10_04_send_face_glass.py:910`, `:1220`; `holdspeak/services/channel_service.py:94`. My replacement probe used the real connection-check producer: **CONNECTED / CHECKED passed at both widths**. [Proof](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-697-r2-otr2v2t9/connection-probes/canonical-check-393.json).

4. **The r1 repairs and backend lock ordering hold.** All six original probes pass. Eight additional Atlassian probes pass: the second send waits while still prepared; another DB write completes during that wait; release permits both sends; sign-in, switch, identity and lock refusals cause no dispatch. The lock is released before the boundary transaction, then reacquired for switch → status → create. [Verification summary](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-697-r2-otr2v2t9/review-summary.json).

5. **Canvas comparison otherwise holds, with a measurement qualification.** Compared 59 canvas boards at both widths and the additional built shots. All 138 shipped shots have measurements, including the armed controls. Checked time is restored. My initial glass run passed 21/22; board 05 at 393 clips a sufficiently long receipt at the harness’s chosen scroll position. Shorter-path reruns pass, and scrolling exposes the complete long receipt. This is a positioning limitation, not a lost receipt. [Measured reproduction](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-697-r2-otr2v2t9/longer-path-boards/receipt-after-scroll-393.json).

CONDITIONS:

Correct B11’s historical wording and timestamp; no live SendGrid probe is required. Preserve the known terminal refusal on the first 503 response. Fence both rendered transitions at both widths, changing words and fences together. Replace the Atlassian seed with real producers and assert the intended connection state explicitly.

MISSED:

1. Historical success appears freshly verified after credentials change.
2. A known non-delivery makes the owner investigate an apparently uncertain send.
3. Comparing the face with the same malformed fixture lets the wrong board pass.

TUESDAY: The normal send workflow works; the owner still cannot trust what Check verified or whether a timed-out Send was refused.

UNKNOWN: Reviewed `8d7fa1ea..702fd3bb`; the fresh worktree remains unchanged. Tests ran from a verified source export. The real manual-delivery atlas case passed at both widths; export revision metadata is qualified by the source manifest. Real remote accounts and Muad’Dib’s full-suite result remain unverified; CI was incomplete at the final read.