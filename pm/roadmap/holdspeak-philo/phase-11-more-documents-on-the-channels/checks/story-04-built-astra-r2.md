VERDICT: DO-NOT-RATIFY

FINDINGS:

1. **Blocking: detailed failure and refusal receipts can disappear when the row closes. Tenets 3 and 7.** `LatestReceipt` and `OutcomeLine` are rendered inside the open-row preview branch (`web/src/desk/surface/send/SendWell.tsx:501`, `web/src/desk/surface/send/SendWell.tsx:547`). The closed row keeps only a summary chip; `SendHistory` excludes `failed` rows (`web/src/desk/surface/send/SendWell.tsx:252`, `web/src/desk/surface/send/SendWell.tsx:667`). The tests check the receipt before closing or changing the row; they do not fence that rendered transition (`web/src/desk/surface/send/__tests__/SendWell.test.tsx:103`, `web/src/desk/surface/send/__tests__/SendWell.test.tsx:263`).

2. **The PR cannot merge against its current base.** GitHub reports [PR #708](https://github.com/karolswdev/HoldSpeak/pull/708) as `CONFLICTING`; #708 is at `f4127c441`, while [PR #707](https://github.com/karolswdev/HoldSpeak/pull/707) has advanced to `fd1028f3` and remains open. Resolve the stack against the settled #707 result before merge.

3. **G2’s contract and consumer proof are now clear; producer proof is still pending story 02.** Both ends should use top-level integer `size` and `limit`, beside `code`/`error_code`; `size` is the final Slack text’s character count and `limit` is `39000` (`pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/story-02-the-slack-channel-and-the-aftercare-rewrite.md:28`, `web/src/features/channels/channels.ts:441`). The nested fallback is gone. The red-before pinned to `3552be416` is valid **consumer** evidence, but the UI tests inject those numbers; the current refusal producer does not send them (`web/src/desk/surface/send/__tests__/SendWell.test.tsx:163`, `holdspeak/services/channel_service.py:344`). Keep G2 marked as consumer behavior until story 02 proves the real producer and HTTP response.

4. **The other round-two corrections hold.** The two document-switch probes failed on `13ec2a7b3` and pass now; their A/B records are mocked but explicitly carry the corresponding `document_ref` (`pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/evidence-story-04.md:29`, `web/src/desk/surface/send/__tests__/SendWell.test.tsx:292`). T2 presses again and checks `dig1` then `dig2` (`web/src/desk/surface/send/__tests__/SendWell.test.tsx:263`). The own-container G4 rule is right: the well declares `container: surface / inline-size`, and the recursive guard catches a nested viewport-query mutation (`web/src/desk/surface/send/send-well.css:132`, `tests/unit/test_native_surfaces_guard.py:93`). The 12 px heading rule and G4 are implemented, but their Chair/picker proof remains owed by story 05, as the lane records (`pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/evidence-story-04.md:31`).

5. **The DELIVERY reversion matches the ratified Phase 10/E1a look.** I inspected the paired `34-history-several` and `34b-history-manual` shots at 1440 and 393; the DELIVERY head, To field, Mark delivered action and row/chip arrangement match. The new SEND row above is the expected species change. The four glass checks pass; moving all DELIVERY rows to one grammar is correctly backlog work (`pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/evidence-story-04.md:32`; shots under `phase-10-the-channels/assets/story-04-shots/34*` and `phase-11-more-documents-on-the-channels/assets/story-04-shots/34*`).

6. **The atlas gap is closed in this review.** I reran all six real Phase 10 cases on `f4127c441` with the current built bundle: SENT and PREPARED at 1440/393, plus both `.op` cases at 1440. All six observations are `pass`, complete, settled, `dirty=false`, with DBs under isolated walk homes; I inspected each before/after shot. Evidence is under `/tmp/astra-708-atlas-r2/`. The focused web run passed 37 tests; the recorded library fences passed 21 and the web baseline reports 2,987 passed with zero branch-new failures (`pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/evidence-story-04.md:526`).

CONDITIONS:

- Keep the failed/refused receipt visible after the click closes or changes its row, and add tests that assert the rendered transition for both the update and a non-update host.
- Resolve #708’s conflict against the settled #707/main tree and verify the resulting integration.
- Keep G2 producer/route proof assigned to story 02, and Chair/picker proof assigned to story 05; do not describe either as proven here.

MISSED:

1. Highest cost: a failed or refused send can lose its detailed explanation when the user clicks away.
2. The current GitHub stack is conflicting, so this head cannot merge as-is.
3. The SEND species is exercised in the update host, but the Chair/picker rules still lack product-face proof.
4. The displayed Slack size currently depends on fields the real producer does not emit.

TUESDAY: Yes—the existing update DELIVERY flow remains visually as before, including manual delivery; the SEND species adds the ratified row above it.

UNKNOWN: I did not observe the owner using the Chair/picker, and I did not verify real Slack refusal fields; story 05 and story 02 own those proofs. The supplied worktree remained clean at `f4127c441`; I changed nothing in it.