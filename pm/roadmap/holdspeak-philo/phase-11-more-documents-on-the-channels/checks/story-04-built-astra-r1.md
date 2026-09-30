VERDICT: DO-NOT-RATIFY

FINDINGS:

1. **Blocking: changing documents can send the previous document. Tenets 3, 5 and 7.** In an isolated copy, I loaded A’s prepared send, changed `doc.ref` to B, and delayed B’s read. The face labelled the row **BRIEF B**, but clicking Send submitted `send_id: "chs_prepared_A"`. A second probe showed a late A response populating B’s history. `useSends` retains unkeyed state and accepts obsolete responses; `mergeKnown` filters cached records but not incoming read rows. This lifecycle weakness is inherited, but the new species contract must resolve it. Evidence: `web/src/desk/surface/send/SendWell.tsx:91`, `web/src/desk/surface/send/SendWell.tsx:351`, [two failing probes and submitted request](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-708-web-4hy0xmiz/document-switch-probe.log).

2. **G2’s red-before is valid consumer evidence, not producer evidence. Tenet 3.** I reproduced `NO PREVIEW · NO ANSWER` against base `3552be416`; the current focused tests pass. However, the test injects the numeric fields. The current producer supplies neither, and the HTTP adapter does not serialize arbitrary exception context. Story 02 should emit **top-level integer `size` and `limit`**, alongside `code`/`error_code: "payload_too_large:slack"`; `size` counts the final Slack text’s characters and `limit` is `39000`. Preserve the existing receipt envelope where applicable. Fence that response through the real producer and HTTP route. The nested-context fallback is not a second contract. Also pin the red-before script to the baseline: its present `HEAD` reference no longer selects the old implementation. Evidence: `holdspeak/services/channel_service.py:344`, `holdspeak/web/routes/channels.py:68`, `pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-04-logs/g2_red_before.sh:7`.

3. **G4’s own-container approach is right. Its product proof remains pending.** The guard forbids viewport media queries, not container width queries. Making the well a `surface` container gives its controls the correct local width in the Chair and other hosts. The heading’s intrinsic wrapping is also reasonable. Neither change has been demonstrated on the affected product face, so “G4 and the head rules paid” overstates verification. Record them as implemented, with Chair/picker integration proof owed by story 05: both widths, actual pointer ownership, readable headings and ordinary scrolling. Tenets 3 and 5; evidence: `web/src/desk/surface/send/send-well.css:132`, `web/src/desk/surface/surface.css:75`.

4. **DELIVERY’s new grammar is a visible deviation from E1a.** I support the consistent grammar under Tenet 5, but E1a retained the old update history. It cannot satisfy the unchanged “no visible change” criterion. Record an explicit scope/design amendment with the comparison shots; passing behavioral fences does not establish visual equivalence. The manual row and Mark delivered remain. Evidence: `pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/story-04-the-send-well-species.md:25`, `pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-04-shots/34-history-several-1440.png`, `pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-04-shots/34-history-several-1440.png`. UX-CANON A.2 applies.

5. **The separate import path is acceptable; extend the guard in 04.** `desk/surface/send` is documented and keeps this connected component out of the general barrel. No barrel export is required. But the CSS guard’s top-level glob misses the new species—and other nested library CSS. Change it to recursive scanning and demonstrate rejection of a nested viewport-query violation. My read-only recursive scan found no existing viewport violations, so this needs no exception list. Tenet 5; evidence: `web/src/desk/surface/contract.md:404`, `tests/unit/test_native_surfaces_guard.py:89`.

6. **The stated state coverage exists, with narrower proof than some wording suggests.** I collected and reran **35 passing tests: 14 species, 17 update, 4 provider**. The required non-update states are represented. T2 checks refreshed preview text; despite its name, it does not press Send again or verify the replacement digest. The four glass passes cover file/setup and prepared flows at both widths. All six recorded atlas runs are actual cases with temporary-HOME databases and passing terminal predicates. The identical `.op` screenshots are not visual-transition evidence; those cases prove protocol outcomes. Evidence: `web/src/desk/surface/send/__tests__/SendWell.test.tsx:263`, `pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/evidence-story-04.md:170`, `pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/evidence-story-04.md:272`.

CONDITIONS:

- Before merge, isolate reads and rendered actions by document identity; reject obsolete responses. Add both failing transition cases and prove them green.
- Extend the CSS guard, pin the G2 baseline, and correct the visual-equivalence and completed-proof claims.
- Record the numeric refusal contract for story 02 and the remaining product-face/receipt-transition obligations for story 05.
- Merge after #707’s settled result and the lane owner’s full-suite verification of the resulting tree.

MISSED:

1. Highest owner cost: a correctly labelled document can expose another document’s consequential Send.
2. Next: producer fields and their HTTP serialization are separate seams; adding exception context alone will not deliver the numbers.
3. Next: the shared renderer always says `CHARACTERS`. If numeric metadata is extended to byte-limited channels, carry and render the unit.
4. Lower: the evidence miscounts the test groups, and T2’s title promises an untested second press.

TUESDAY: The demonstrated update workflow remains usable at both widths, including manual delivery; its appearance has changed, and document switching is not yet trustworthy.

UNKNOWN: I inspected all 48 story shots, 12 walk shots and eight E1a–d canvas shots, plus the prior canvas checks. I did not rerun the real hub walks or full suite, verify real Slack delivery, or observe the owner’s session. The new failure probes used mocked transport in an external temporary copy. The supplied worktree remains clean at `13ec2a7b3`; I changed nothing in it.