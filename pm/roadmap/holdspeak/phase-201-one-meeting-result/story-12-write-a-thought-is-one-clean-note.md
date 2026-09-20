# HS-201-12 - Write a thought is one clean note

- **Project:** holdspeak
- **Phase:** 201
- **Status:** done
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

### Amendments (counsel on built, 2026-09-20)

Astra's counsel on PR #592 (`checks/story-12-built-astra.md`) carried three
corrections to the settled text; Muad'Dib accepted all of them.

- **A finished note does NOT reopen editable.** The hub refuses every
  working-note write on a completed Thought
  (`holdspeak/services/refinement_thought_service.py:1147`, code
  `thought_completed`), so an editable field would be a save that always
  fails. The settled rule is: a finished note names `FINISHED` on the title
  and in the foot, and `Resume` is the one filled primary — one press, then
  it is editable.
- **A returned draft is APPENDED, never accepted.** The hub's `accept`
  replaces title, body and tags with the AI's
  (`refinement_thought_service.py:1060`), which deletes the owner's own
  words. Band 3's `Add to note` appends the draft through the working-note
  writer and never calls `accept`; the durable edit supersedes the review by
  itself, so the band folds with no second command.
- **The parked things are parked, not reachable.** See Scope below: the
  original-capture disclosure, the tag row and the default-context picker
  have no route from a thought-owned note today. They are deliberate
  removals (a), ledgered with their reason, not "still available elsewhere".

## Scope

- **In:** `ThoughtWorkspaceWindow.tsx` and `ThoughtDocumentPane.tsx` recomposed to the four bands from library species only (SurfaceFooter, EditInPlace, PadGadget with micLabel, FoldGadget or a single ledger row for band 3, Button); the CSS for this window only; the two plain bugs (title wrap; empty question never a heading); the labels above; the existing controller and services untouched except where a label or a receipt string lives.
- **Out:** the pullout editor; new AI behaviour; the correction loop.
- **Removed from this window, ledgered (a) with the reason** (counsel on
  built, finding 3 — the earlier "parked in the pullout" claim was false:
  `desk/components/Pullout.tsx:123` sends a thought-owned note to THIS
  window, so nothing reaches the legacy pullout's copies):
  - the formatting rail — a dictated note is prose, not markup; `DeskEditor`
    keeps the rail for every other host;
  - the tag row — no tag is read by anything on this path today;
  - `Info` / the original-capture disclosure — the raw capture stays in
    custody on the hub and this window never fetches it (fenced);
  - the default-context picker — this window's `Change` settles THIS note's
    context only; default policy has no owned-note route now;
  - the Note/Interview tab nav, `Filed`/`Saved`, the duplicate `Attached …`
    receipt and the inserted-marker chips.
- **Not removed, but with no caller from this window:** the chained turn
  (`answer_and_continue`, `desk/thoughts.ts:423`) — band 3 has one verb by
  the settled design, so nothing in the product calls it today.

## Acceptance criteria

- [x] The window renders the four bands and nothing else; a title of 120 characters wraps and is fully visible at 1440 and 393.
- [x] With no question asked, band 3 is one row; no empty heading exists in the DOM (fence).
- [x] After Ask, the question and the answer pad are visible without scrolling at 1440x900 and reachable at 393 without a tab.
- [x] The context fact appears once; "Attached …" receipts do not duplicate it.
- [x] Exactly one filled primary in the window (Finish); every verb a library Button; zero raw <button>; zero prose sentences outside the note and the question.
- [x] The owner's own shot state (the dictated note in his shot) reproduced in the rig at both widths, before and after, in assets/story-12-shots/.
- [x] Existing thought-workspace vitest and the thought e2e rigs green or honestly re-pointed (a) with the doctrine stated.

## Test plan

- **Unit:** vitest for band folding, no-empty-heading, single context line, one primary.
- **Integration:** the existing thought e2e rig extended: dictated note → Ask → answer → Add to note → Finish, both widths.
- **Manual / device:** shots.

## Notes / open questions

Lane B (Muad'Dib, one Opus worker) in worktree wt-201-thought, branch feat/hs-201-12-thought. Astra checks the design in parallel; findings fold into the build's fix round (the owner's ruling of 2026-09-17: counsel ratifies the canvas on his behalf). Serves the owner's first-use verdict directly.
