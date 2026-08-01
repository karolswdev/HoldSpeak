# HS-111-02 - Speak

- **Project:** holdspeak
- **Phase:** 111
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-111-10
- **Owner:** unassigned

## The thesis (the bar)

The Speak/Dictation program is the flagship — the dictation cockpit,
the journal, correction memory, and pipeline config. It must feel
like the OS's primary instrument, not a web recording widget. The
bar: **the cockpit reads as a piece of signal equipment — dense,
opaque, beveled, mono-labeled — and the journal reads as a machine
ledger, not a feed of cards.**

## Method (phase canon)

1. **Audit.** An agent walks the cockpit, journal, correction memory,
   and pipeline config as they render today, filing every SaaS-ism.
2. **Rethink.** Propose the native interior per the phase question
   (CD-ROM 2004, Workbench 2.0 grammar, dark techy render). Not
   "apply tokens" — layout, density, control style, typography.
3. **Implement** in `web/src`.
4. **Prove** with live screenshots on the real desk, 1440 and 393.

## Test plan

- The cockpit's live state (idle, listening, committing) reads
  through beveled/etched treatment, not glows or pills.
- Journal rows are dense ledger rows with full-width hover bands.
- Correction memory and pipeline config panes speak the same control
  kit as the rest of the program.
- Screenshot walk at both viewports, no overflow.
