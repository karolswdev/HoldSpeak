# HS-201-12 - Write a thought is one clean note

- **Project:** holdspeak
- **Phase:** 201
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** (optional)
- **Owner:** unassigned

## Problem

The owner's first real-use verdict (2026-09-20, after Phase 201 landed): "the interface to develop a thought is completely unusable. It hides things. It doesn't look good either." His shot: the title clipped mid-sentence; an orphan mic button; a raw formatting toolbar (B I U H1 H2 H3 List 1. code Link Quote) over a dictated note; a tag row and an Info verb; a Filed/Saved footer; then an INTERVIEW section whose kicker "ONE THING TO SHARPEN" stands over an EMPTY question (the h2 renders nothing) with the answer pad off the bottom; the context fact stated twice ("Everyday context · 5 NOTES" and "Attached Everyday context"); two verbs in two species and two typefaces. Two features in one window (`web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx`, Phase 141 + the Phase 153 Interview). Tenets 3, 4, 5, 6, 7; Article VII; UX-CANON A.

## The settled design (Muad'Dib, on the owner's deferral "JUST GET THIS REDONE"; Astra checks)

The job: a Senior Software Architect dictated something. He wants ONE clean note, kept and findable, and, only if he asks, ONE question from the AI that sharpens it. Nothing else on the screen.

One window, one column, four bands, top to bottom. Every verb is the library Button. No prose. No modal. No counter of zero. ASD-STE100 labels.

```
┌ ▤ Thought ─────────────────────────────────────────────────┐
│ Well, there's just a little bit of misunderstanding here,   │  1 TITLE: wraps to as many lines as it
│ I believe my team...                                        │    needs; editable in place (EditInPlace)
├─────────────────────────────────────────────────────────────┤
│ Yeah, I have it that way and what about you?                │  2 NOTE: the text, plain, full width, the
│                                                             │    body typeface; no toolbar; the mic is
│                                                             │    the StringGadget/PadGadget micLabel of
│                                                             │    the field, not a separate button
├─────────────────────────────────────────────────────────────┤
│ ONE QUESTION                                    [Ask]       │  3 QUESTION band (folded to one row until
│ (after Ask:)                                                │    asked): the question as body text, the
│ Who is misunderstanding what, and what would settle it?     │    answer pad beneath, one verb
│ [ your answer                                          ]     │    "Add to note"; a failed ask says one
│                                        [Add to note]        │    line and keeps the note unchanged
├─────────────────────────────────────────────────────────────┤
│ Reads: Everyday context · 5 notes   [Change]                │  4 FOOT (SurfaceFooter): what the AI may
│ Kept · not in a drawer                       [Finish]       │    read (one line, one verb); kept state
└─────────────────────────────────────────────────────────────┘    (one line); one filled primary: Finish
```

Rules: band 3 is folded (one row: "ONE QUESTION · Ask") until the owner asks, and never renders an empty heading; with no engine assigned the row reads "ONE QUESTION · No engine yet" with the Choose an engine Button and nothing else. The context receipt ("Attached …") is the Reads line itself; it is never stated twice. Tags, Info, the toolbar, the Note/Interview tab nav, the synthesis draft state and the inserted-marker chips leave this window (parked, not deleted: the code stays behind a flag or in the pullout editor). At 393 the same four bands stack; nothing is hidden behind a tab. Finish is the one filled primary; Ask and Add to note and Change are default species. "Filed" becomes "Kept"; "Saved" is not shown (a save failure is shown, once, as a line).

## Scope

- **In:** `ThoughtWorkspaceWindow.tsx` and `ThoughtDocumentPane.tsx` recomposed to the four bands from library species only (SurfaceFooter, EditInPlace, PadGadget with micLabel, FoldGadget or a single ledger row for band 3, Button); the CSS for this window only; the two plain bugs (title wrap; empty question never a heading); the labels above; the existing controller and services untouched except where a label or a receipt string lives.
- **Out:** the Interview's synthesis/draft mode (parked); the pullout editor; new AI behaviour; the correction loop.

## Acceptance criteria

- [ ] The window renders the four bands and nothing else; a title of 120 characters wraps and is fully visible at 1440 and 393.
- [ ] With no question asked, band 3 is one row; no empty heading exists in the DOM (fence).
- [ ] After Ask, the question and the answer pad are visible without scrolling at 1440x900 and reachable at 393 without a tab.
- [ ] The context fact appears once; "Attached …" receipts do not duplicate it.
- [ ] Exactly one filled primary in the window (Finish); every verb a library Button; zero raw <button>; zero prose sentences outside the note and the question.
- [ ] The owner's own shot state (the dictated note in his shot) reproduced in the rig at both widths, before and after, in assets/story-12-shots/.
- [ ] Existing thought-workspace vitest and the thought e2e rigs green or honestly re-pointed (a) with the doctrine stated.

## Test plan

- **Unit:** vitest for band folding, no-empty-heading, single context line, one primary.
- **Integration:** the existing thought e2e rig extended: dictated note → Ask → answer → Add to note → Finish, both widths.
- **Manual / device:** shots.

## Notes / open questions

Lane B (Muad'Dib, one Opus worker) in worktree wt-201-thought, branch feat/hs-201-12-thought. Astra checks the design in parallel; findings fold into the build's fix round (the owner's ruling of 2026-09-17: counsel ratifies the canvas on his behalf). Serves the owner's first-use verdict directly.
