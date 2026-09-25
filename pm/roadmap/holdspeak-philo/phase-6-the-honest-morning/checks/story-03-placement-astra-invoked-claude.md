# PHILO-6-03 placement — Astra-invoked Claude check

2026-09-24 night. Invoked by Astra with `claude -p --model claude-fable-5-1 --permission-mode bypassPermissions`. Read-only review of the built worktree. This is not the calling Muad'Dib's eventual PR counsel of record; that remains before merge. The raw check follows verbatim.

VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:

1. The phone no-overlap proof rests on `overflow-anchor`, which Safari does not implement, and the rig only runs Chromium. `web/src/desk/chair/chair.css:651-658` is the correction that turned run 20260925T045018Z (fail) into 20260925T045707Z (pass). Run 045018's raw JSON shows the failure shape that a browser without scroll anchoring produces: `scrollIntoView` fired once (scroll_top 0 → 218), then the late summary grew above the slot and the card landed at y 642–822 under the capture bar (y 573–711), 0/9 points owned. `scripts/graph_walk.py:5027,5172` launches only `play.chromium`. WebKit has no scroll anchoring, so on an iPhone at 393 the first-run geometry returns and the story's third acceptance box ("at 393 the toast covers neither the summary text nor the capture bar") is false on the device that width stands for. Tenet 2 (the creator's first real use) and UX-CANON "egress where egress happens" are not at issue; the failing tenet is 2 with the rendered fence as the proof gap. Chromium at 393 is honestly green; the claim should be scoped to it or the anchor made explicit in the effect.

2. The rendered "leaves" half of the transition proof is jsdom only. Story AC 5 says the toast appears "and leaves, at both widths". The six passing atlas runs end with the card present; Dismiss clearing the slot is proven only in `web/src/components/aftercarePlacement.test.tsx:118-120` under jsdom. `intelligenceAttention.ts:70-107` has no expiry, so "leaves" means Dismiss; no shot shows the Arrival after Dismiss, and in particular no shot shows that the chair's capture clearance restores after the `:has(+ …:empty)` rule at `chair.css:646` takes back over. Proof gap, not an observed defect.

3. Window slot selection can land the card behind another window. `AmbientLayer.tsx:240-251` picks `.desk-surface-window.is-front` first, then any open surface window. `is-front` sits on the same element (`DeskWindow.tsx:779-785`), so the front path works; but when the front window is a pullout or trust window rather than a surface window, the fallback picks the first open surface window in DOM order, which may be under the front one. Minimized windows are unmounted (`SurfaceWindows.tsx:176`), so the "hidden window" case the parent worried about is not reachable. Low cost; realistic only with two or more windows up.

4. Doc drift inside the canvas README. `docs/internal/philo/phase-6/toast/README.md` keeps "does not apply product placement or edit ChairHome.tsx" and "the product transition and its ChairHome seam remain unimplemented pending owner ratification" below a header that says the build shipped. The header disclaims the body, so this is hygiene, not a defect.

Verified and not contested: the ChairHome diff from d8f608c8 is exactly the four ratified lines at `ChairHome.tsx:1443-1446`, nothing else in that file. No producer, string, or species change (`intelligenceAttention.ts` untouched; the card keeps the library Button verbs). All six after.png shots match the ratified boards in position and grammar; the Floor list shot differs from the board only by the fixture's "FLOOR · LIST VIEW" band, which the board invented. The archive reds are real product reds (slot absent, card fixed), including the Floor red at 050903Z, which is already recorded as fail. The luna-models.json rollouts name `gpt-5.6-luna` at `xhigh`.

CONDITIONS:

- C1 (finding 1): either run the 393 Arrival case once under Playwright WebKit and record the result, or state in the story and evidence that the phone proof is Chromium-only and that Safari lacks scroll anchoring, with a ledger row naming the fallback (re-scroll after the summary settles, or scroll the slot after the async summary resolves in the effect). Do not flip AC 3 as a device-wide claim without one of these.
- C2 (finding 2): one rendered Dismiss observation at 393 on the Arrival (card gone, capture clearance back), or reword AC 5 to say "appears" on glass and "leaves" under the unit fence.
- Findings 3 and 4 may be ledgered, not paid, before the PR.

MISSED (ranked by cost to the owner):

1. Safari has no scroll anchoring, so the one fix that made the phone pass is engine-specific and the rig cannot see it.
2. No glass proof of the card leaving or of the clearance rule restoring after Dismiss.
3. Multi-window fallback order.
4. Stale proposal prose in the canvas README.

TUESDAY: Yes on the desktop and on a Chromium phone: the card sits in flow above the capture bar with two verbs and reads in one glance; on an iPhone the late summary can push it back under the capture bar, which is the exact thing he complained about.

UNKNOWN: Which phone the owner will actually use; whether the summary consistently arrives after the aftercare signal on his real engine (the replay ordering produced it in run 045018, and that ordering is what makes finding 1 bite); the pending 235-test scoped run and the final generation checks, which I did not run and do not declare passed; the parent's lane report, which was being assembled while I read.

## Astra disposition

C1 is paid by an explicit evidence boundary: the story and lane report claim Chromium at 393/1440, not a device-wide Safari result. The review's blanket assertion that Safari lacks scroll anchoring is outdated: [WebKit's Safari 27 release notes](https://webkit.org/blog/18325/webkit-features-for-safari-27-0/#scroll-anchoring) say that version adds it. No Safari device walk or older-Safari compatibility claim is made. Native anchoring is the implementation dependency; older implementations without it can reproduce the observed late-summary shift. This limit and the possible later remedy (coordinate the one scroll with the completed summary render) are ledgered, without adding a backwards-compatibility mechanism to this pre-alpha lane.

C2 is paid by the actual Arrival runs `20260925T052820Z-case.philo603.toast.arrival-astra-393` and `20260925T052913Z-case.philo603.toast.arrival-astra-1440`, under `../assets/story-03-shots/final/`. Each `observation.json` records `dismissal.done: true`: the real Dismiss Button removes the card, leaves the slot empty and hidden, and restores CaptureBar ownership at 9/9 points. Each keeps before, after and dismissed shots. Astra read both observations and viewed all six shots. The primary observer was sealed before Dismiss; its one phone/zero desktop scroll count is unchanged.

Finding 3 is ledgered as an unverified multi-window extension; only the ratified foreground Meetings/window and Floor list layouts are claimed. Finding 4 is paid by changing the retained canvas prose into past tense and linking the built report.

## Closing follow-up — Astra-invoked Claude

Same read-only CLI and model; still not the calling Muad’Dib’s PR counsel. The response follows verbatim.

Verification is complete. I have read the report, story, status, README, ledger, the rig helper, both final Arrival observations and all three shots per run, and confirmed the WebKit citation against the live page. Writing the verdict now.

VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:

1. **C1 is paid.** The claim is now scoped to Chromium in three places: the story's "Browser proof boundary" note, the ledger row "Browser proof limit" (`docs/internal/philo/phase-6/ledger.md`, new table rows), and the lane report's "Browser scope is Chromium only" paragraph. No Safari device result is claimed. My earlier blanket statement that Safari lacks scroll anchoring was outdated. The live WebKit Safari 27.0 release notes say scroll anchoring ships in 27.0, controlled by `overflow-anchor`, and the ledger cites that page correctly. The remaining limit (engines without anchoring reproduce the late-summary shift) and the named remedy are ledgered, with no compatibility shim added. Tenet 1 respected.

2. **C2 is paid.** Both final Arrival observations carry a `dismissal` block with `done: true` and all three checks true: card absent from the DOM, slot present, empty and hidden, capture bar 9/9. Evidence: `assets/story-03-shots/final/20260925T052820Z-case.philo603.toast.arrival-astra-393/observation.json` (capture rect 12,573,369,138; scroll_top 435 after Dismiss) and `…/20260925T052913Z-case.philo603.toast.arrival-astra-1440/observation.json` (capture rect 256,758,928,74). Both `dismissed.png` shots show the summary and capture bar with no card between them. The Dismiss click is the real product Button through selector `.ambient-aftercare button:has-text('Dismiss')`, declared in the atlas case only for the Arrival case.

3. **The probe is sealed before Dismiss.** `scripts/graph_walk.py:4818-4838`: after.png, the placement seal, and the verdict are computed before `capture_dismissal` runs. The primary scroll record is unchanged: one call, delta 501 at 393; zero at 1440. A failed Dismiss fails the overall verdict, so the fence has teeth.

4. **The shot-list overwrite is fixed for this case, but a latent overwrite remains.** `scripts/graph_walk.py:4857-4866`: dismissal appends `dismissed.png`, then the framing branch, if a case declares framing, resets the list to before/after/framing and drops the dismissed shot. No philo603 case declares framing, so the shipped observations are correct. Ledger it.

5. **Structural lint fails until the story flip runs.** `.githooks/dw check holdspeak-philo` returns one ERROR: the story header reads in-progress while the phase table already reads done. The brief says the flip and gate are not yet performed, so this is expected pre-gate state, but the flip must go through `dw story status … done` before `dw contract new`, or the gate refuses.

6. **Two superseded Arrival runs sit inside `final/`.** `final/20260925T051357Z-…-393` and `final/20260925T051652Z-…-1440` pass but have no Dismiss and are not in the report's six-row table; they appear only in `live-readings.txt`. They will ship as untracked assets under the evidence folder. Hygiene, not a defect. Either name them in the report as superseded or move them out of `final/`.

7. **Heartbeat and drainer as stated.** Both final provenance blocks record `scheduler_thread: false`, and the trigger response body carries `"drainer": "running"`. The intel job reaches ready/succeeded on the durable meeting read.

Verified and not contested: the six-row table matches the observation files; the 393 card (y 381 to 561) clears the capture bar (y 573) and the summary (y 151 to 241); the BRIEF row scrolls offscreen at 393 and the report says so; the raw log tails match the report's verbatim blocks (30/30, 104, 235 with one inherited error, 214 with the same error on the untouched archive, five generated checks at the 05:31:40Z capture, exit 0); `intelligenceAttention.ts` is not in the diff; the card keeps library Buttons and its words; the canvas README's stale proposal prose is corrected to past tense; the multi-window fallback is a ledger row.

CONDITIONS:

- C3 (finding 5): flip the story through `dw story status holdspeak-philo phase-6-the-honest-morning 03 done`, confirm `dw check` is clean, then generate the contract. Do not hand-edit the header.
- C4 (finding 6): name or relocate the two superseded `final/` Arrival runs so every folder under `final/` is either in the report table or labelled superseded.
- Finding 4 may be ledgered, not paid, before the PR.

MISSED (ranked by cost to the owner):

1. The two unreferenced `final/` runs will confuse whoever reads the folder next.
2. The framing-plus-dismissal shot-list overwrite, latent only.
3. Nothing else of cost within the scoped lane.

TUESDAY: Yes on the desktop and on a Chromium phone: after a summary, the card sits in flow above the capture bar with two verbs, Dismiss removes it, and the capture bar comes back where it was.

UNKNOWN: Whether the gate accepts the final index tree once the flip and staging happen, since I did not stage or run `dw gate`. Real-provider timing on the owner's engine, which the replay does not exercise. The lane-A reconciliation of the four-line ChairHome commit, outside this lane by the brief's scope.

## Closing disposition — Astra

C4 is paid: the lane report names the two earlier Arrival final-folder runs as superseded; raw evidence stays intact. Finding 4 is ledgered as a latent framing-plus-dismissal combination, absent from every PHILO-6-03 case. C3 is paid through the story-status CLI and the captured clean PHILO Workbench check before contract generation; the paired story evidence records the command and result. The final gate result is recorded at publication.

Global lint qualification: the owning PHILO check is clean; global `dw check` retains six errors in `pm/roadmap/holdspeak/`, reproduced verbatim in the pinned origin/main archive and ledgered. The lane rule forbids changing those files; none changed. This is not a claim of global lint success.
