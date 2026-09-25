VERDICT: RATIFY-WITH-CONDITIONS — present **set B** after the documentation corrections below. The principal r1 blockers are paid.

FINDINGS:

1. **The OFF visibility rule still contradicts the canvas and beat.** `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/assets/story-02-canvas/README.md:28` says OFF hides every non-LIVE row. `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/assets/story-02-canvas/harness/main.tsx:263` retains every orphan delegation, consistent with `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/design/grant-lifecycle-beat.md:155`. Changing only board 5c’s switch to OFF still renders the expired orphan ([reproduction](/tmp/astra-grant-r2.QPlcU2/off-expired.json)). Keep the implemented, beat-consistent rule and correct the sentence. **Conflicting implementation instructions fail Tenet 3.**

2. **The receipt, PREFS and grant verbs pass independent pointer verification.** Across 50 renders, all **146 requested controls** owned their centers, edge midpoints and corners at both widths, using `elementFromPoint` and real pointer movement. The receipt’s library composition and reserved grip corner resolve r1. [Independent proof](/tmp/astra-grant-r2.QPlcU2/pointer-proof.json).

   **One bounded limitation remains:** on board 4b at 393, minimally scrolling “Issue credential” into view leaves its lower halo under the footer: point `(85.6, 681.1)` hits `surface-footer-layout`. Scrolling fully down restores ownership. The submitted probe centers each control (`pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/assets/story-02-canvas/harness/shoot.py:70`), so it misses this position. [Scroll-position proof](/tmp/astra-grant-r2.QPlcU2/edge-proof.json). Carry this into the built fence; it does not warrant another canvas redesign.

3. **The library typography repair is supported by verification.** I reproduced zero sub-12 px readable text in the 50 canvas renders and no horizontal overflow. Production Arrival and Meetings components, supplied with visual fixtures at 393, showed no new horizontal overflow; sampled chips fit and dock geometry remained unchanged against the previous CSS. [Arrival shot](/tmp/astra-grant-r2.QPlcU2/arrival-393.png), [Meetings shot](/tmp/astra-grant-r2.QPlcU2/meetings-393.png), [CSS comparison](/tmp/astra-grant-r2.QPlcU2/css-comparison.json). The web result reproduces: **2,872 passed, zero branch-new, five healed**. [Baseline report](/tmp/astra-grant-r2.QPlcU2/baseline-report.txt).

4. **The new states have the claimed evidence, within the disclosed canvas boundary.** The real credential producer again returned `review-agent` with `active=false`; **one producer test plus 45 guards collected and passed**. [Collection](/tmp/astra-grant-r2.QPlcU2/collect.txt), [run](/tmp/astra-grant-r2.QPlcU2/producer-guards.txt). Expiry now derives from stored LIVE plus a past timestamp (`pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/assets/story-02-canvas/harness/main.tsx:93`). Board 5d retains credential-backed authority while OFF; 4b separates credential expiry from grant authority; 6b preserves the refused act outside the removed row. The effective-state wire contract is implementable and matches the beat, apart from finding 1’s visibility wording.

5. **Support B and the revised words/order.** “Revoke credential,” the explicit ACTIVE CREDENTIAL count, and CANNOT ALLOW / CANNOT STOP distinguish the actions adequately. My support does **not** extend to A’s omission of decision authority. The `docs/internal/philo/phase-7/grant-canvas/index.html:63` now honestly identifies static states, fixture receipts, omitted Settings content and the unbuilt producer. The disappearance and credential-revocation fences are appropriately specified at `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/assets/story-02-canvas/README.md:126`.

6. **One geometry claim needs narrowing.** `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/assets/story-02-canvas/README.md:77` says every row is one line at 1440. Board 6’s refused desk-agent row wraps its verbs onto another line ([shot](/tmp/astra-grant-r2.QPlcU2/6-refused-b-1440.png)). It remains readable; correct the claim, not the layout. **The overstatement fails Article VI’s honesty requirement.**

CONDITIONS:

1. Before presentation, reconcile OFF visibility and correct the universal one-line claim.
2. Carry OFF-plus-expired-orphan and scroll-edge target coverage into implementation verification. Preserve the real-producer, matching-operation-ID and rendered-disappearance fences.
3. Present B as the version this check supports.

MISSED:

1. Conflicting OFF rules could send the two implementation lanes toward different behavior.
2. Centering controls proves that position; it does not cover a partially exposed halo.
3. The refusal row’s acceptable wrapping was overstated as single-line geometry.

TUESDAY: Yes for B’s proposed interaction: the owner can distinguish authority from credentials, find Stop while OFF, and reach the receipt; actual execution remains to be proved.

UNKNOWN: No real grant execution, durable receipt transition, atlas case or owner-device walk was verified—the producer remains unbuilt. Other-surface checks were fixture-fed geometry samples. Full Python-suite and generated-document freshness were not checked. The worktree remained unchanged.