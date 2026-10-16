# Frozen material, PR-result and frame source counsel — 2026-10-16

UNCHECKED — awaiting formal Muad'Dib review. This is bounded source counsel,
not Muad'Dib's check or a delivery verdict. Reviewed the current diff against
`9038911d9` for CapabilitySection, PadGadget's voice callback,
PrReceiptsSection, the material composer CSS and the desktop footer reserve.
Read `BUILD-MATERIAL-RECEIPTS.md` and the named recorded validation files.
Product files were read only; no tests, browser or provider calls were run.
The Review-fit lane remains outside this pass.

VERDICT: RATIFY

FINDINGS:

1. No concrete product regression found in the frozen scope. Capability
   material now uses the library's controlled textarea, preserving paragraph
   breaks and the existing durable scope and Run value. There is one default
   integrated Pad microphone with the original accessible label and draft
   scope. Evidence:
   `web/src/desk/pullouts/shared/CapabilitySection.tsx:39`,
   `web/src/desk/pullouts/shared/CapabilitySection.tsx:98`,
   `web/src/desk/pullouts/shared/CapabilitySection.tsx:121`,
   `web/src/desk/surface/gadgets.tsx:369`,
   `web/src/desk/surface/gadgets.tsx:434`. This supports Tenets 3 and 5 and
   Constitution IV.

2. The shared voice repair is limited to the diagnosed stale callback seam.
   A retained callback reads the current controlled value and writer through
   the same ref, then uses the existing whitespace append rule. It adds no
   public API, scanner exemption or allowlist change. The focused tests hold
   the old callback, change both value and writer, and check the newest writer;
   Capability's case also checks exact paragraphs, durable storage, the Run
   argument and recovery after remount. Evidence:
   `web/src/desk/surface/gadgets.tsx:408`,
   `web/src/desk/surface/gadgets.tsx:456`,
   `web/src/desk/surface/gadgets.test.tsx:405`,
   `web/src/desk/components/__tests__/commonControls.test.tsx:179`.
   The actual diff contains no scanner/ceiling/allowlist edit. This is a small
   shared correction consistent with Tenets 1 and 5.

3. PR outcomes retain the action performed, separate from the busy label.
   `Review ready` requires a Draft review result with nonblank output and no
   error; an accepted Send remains `Accepted`. The current server producer
   returns draft output only after a succeeded, usable artifact/output
   publication; refusals return an error response. Operation/artifact IDs and
   the complete output remain in the existing disclosure. Evidence:
   `web/src/desk/components/PrReceiptsSection.tsx:34`,
   `web/src/desk/components/PrReceiptsSection.tsx:68`,
   `web/src/desk/components/PrReceiptsSection.tsx:108`,
   `web/src/desk/components/PrReceiptsSection.tsx:201`,
   `holdspeak/web/routes/delivery_prs.py:390`,
   `holdspeak/web/routes/delivery_prs.py:403`,
   `web/src/desk/components/PrReceiptsSection.test.tsx:73`.
   No new running-agent inference appears. This supports Tenets 3 and 4 and
   Constitution VI.

4. The footer correction adds only 6 px of bottom padding to a direct frame
   footer when the frame is not a sheet. The frame still marks compact views
   `is-sheet`, and still mounts its existing grip and edges only outside that
   mode. No handler, resize-edge dimension or corner reserve changed.
   Evidence: `web/src/desk/components/window-chrome.css:692`,
   `web/src/desk/components/DeskWindow.tsx:1182`,
   `web/src/desk/components/DeskWindow.tsx:1340`,
   `web/src/desk/components/window-chrome.css:96`,
   `web/src/desk/surface/surface-footer.css:20`. Source scope is correct; actual
   pointer ownership and resize behavior require the root's runtime proof.

5. Read the complete integrated collection and run tail: 51 named tests in
   five files, 51 passed. Read the canon collection and run tail: seven
   collected, seven passed. Evidence:
   `.tmp/edges/material-integrated-collect.log:7`,
   `.tmp/edges/material-integrated-collect.log:38`,
   `.tmp/edges/material-integrated-collect.log:51`,
   `.tmp/edges/material-integrated-run.log:5`,
   `.tmp/edges/material-canon-collect.log:9`,
   `.tmp/edges/material-canon-run.log:5`.
   These are recorded component/canon results, not a claim that I reran them
   or observed a real microphone, inference provider or durable server write.

CONDITIONS:

None required by this product source pass. Formal Muad'Dib review remains
outstanding under the current fast cycle; this report does not replace it.

MISSED:

1. Low record cost: `BUILD-MATERIAL-RECEIPTS.md` still describes a frozen host
   mic and an amendment awaiting GO, while the current source has the default
   integrated Pad mic and latest-value/writer repair. Its validation section
   recounts the earlier 22-case split run, while the complete integrated log
   now reports 51 passed. Root was informed; this counsel leaves the other
   lane's build record untouched. Evidence:
   `docs/internal/COHESIVE-EDGE-CONTROLS-2026-10-16/BUILD-MATERIAL-RECEIPTS.md:25`,
   `web/src/desk/pullouts/shared/CapabilitySection.tsx:121`,
   `.tmp/edges/material-integrated-run.log:6`.

TUESDAY:

The source lets the owner edit and run paragraphs, identify a completed review,
and retain the frame's resize controls; actual fit and pointer reach remain
unverified here.

UNKNOWN:

- Actual 1440/393 fit, material appearance, mic target/recovery placement and
  keyboard/pointer behavior. No browser or shots inspected in this task.
- Retry's nine points, real bottom-edge and corner drag, and the effect of the
  desktop reserve in other frame footers. Source preserves the handlers;
  recorded component tests do not prove those geometry relations.
- Real microphone, provider, agent launch, kernel receipt and durable server
  behavior. The producer was read; it was not executed.
- Test launch isolation/lock and the later quick check. The supplied run tails
  show results, not launch environment; the build record asserts isolation.
- Review-fit work, which was still building when this pass was assigned.
