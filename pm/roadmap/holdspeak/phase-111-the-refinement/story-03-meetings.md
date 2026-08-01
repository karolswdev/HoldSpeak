# HS-111-03 - Meetings

- **Project:** holdspeak
- **Phase:** 111
- **Status:** backlog
- **Depends on:** —
- **Unblocks:** HS-111-10
- **Owner:** unassigned

## The thesis (the bar)

The Meetings program — history list, meeting detail, transcript view,
artifact cards, aftercare panel — still carries the frosted-card,
feed-of-tiles interior of its web-app past. The bar: **a meeting is a
record in the OS's archive; the program reads as an archive browser —
dense listing, sunken transcript well, etched artifact receipts —
in the Workbench 2.0 grammar rendered dark.**

## Method (phase canon)

1. **Audit.** An agent walks history, detail, transcript, artifacts,
   and aftercare as rendered today; files every SaaS-ism.
2. **Rethink.** Propose the native interior (layout, density,
   controls, typography) against the CD-ROM-2004 question.
3. **Implement** in `web/src`.
4. **Prove** with live screenshots on the real desk, 1440 and 393.

## Test plan

- History renders as a dense ledger, not a card feed.
- The transcript view is a sunken well (terminal-style inset), not a
  floating panel.
- Artifact receipts are solid bordered insets; aftercare controls use
  the shared gadget kit.
- Screenshot walk at both viewports, no overflow.
