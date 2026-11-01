# The Program window as one object (PG-WINDOW)

Owner, 2026-10-31: Programs are HoldSpeak's flagship. They are "not that
clear to browse, adjust… not clear how to add additional requirements/checks,
see how they are met"; "UX will be key. If it means canvas? It means that."
That night he judged the live window ("README touch", 1440) and the briefing
page. On the window the one thing that needed him was a tinted "Your turn"
box whose line was raw git stderr; a shape bar that read as a search box sat
above it; a bare "R1 Add a requirement / Review / Every step / Required /
Add" form floated over the steps; five grey dots per row meant nothing; the
brief hid under a "Step 1 · … · Parked" fold with four tabs.

The binding verdicts: no tinted callout box around the thing that needs him;
no "▸ label" disclosure rows; a brief reads like a note from a chief of staff
in his terms (`holdspeak/services/brief_words.py`, #1684); show where we are
(the step line with the current step lit and what waits on this answer); the
delight system (kind hues, lamps that breathe, depth only on the choice
tray); every verb the library Button; no modals; no zero counters; no egress
chips; ASD-STE100 words.

Canvas: `canvases/program-window-2026-10-31.html`, three directions at 1440
and 393 on the same state (five steps mid-run: two done, one running, one
held on him at its merge gate, one planned; two requirements, one met and one
unmet; three rounds answered). Nouns: `PROGRAM-LANGUAGE-2026-10-31.md`,
`PROGRAMS-REQUIREMENTS-2026-10-31.md` §7 to §9.

## The direction: A, the line and the note

- **A, the line and the note (chosen).** One column, the same object at both
  widths. The program's station track at the top (one station per step and
  the end, "Done when"); the held thing as the headline under it, in the
  brief's order, with the choice tray as the one raised thing; the steps as
  rows, the open step carrying what it must prove (requirement lines with a
  lamp, Add a requirement at the step) and what the agent did (at most three
  plain lines); the composer at the foot.
- B, the rail and the page: a vertical track on the left and the selected
  step as a page. Good for a long program at 1440, but two places to look,
  the headline moves when he browses, and at 393 it becomes A.
- C, the conversation: the program as a thread with the composer under it.
  The best story once, but browse and adjust have no fixed place.

Why A: it answers "where are we", "what waits on whom", "what must this step
prove and is it met" and "what did the agent do" in one top-to-bottom read,
reflows by the window's container alone, and reuses the rows and requirement
lines that exist. The owner's "go with suggestions" (2026-10-27) pre-approves
it; he judges it live on his desk.

## The slices (one build PR)

1. **W1, the hub's words on the wire (additive).** Each `your_turn_items` row
   gains `brief`: `goal`, `doing`, `happened`, `question`, `blocked_words`,
   `blocked` (ordinals) and `consequences` (choice → its sentence), from
   `brief_words.py`, the same lines the briefing page, Telegram and the call
   read. Each step gains `story`: at most three `{at, line}` rows from its
   ledger through `brief_words.changed_line`.
2. **W2, the line and the headline.** `ProgramLine` draws the program's
   steps with the surface `StationTrack` (word form); the first held item is
   the brief and the tray (each choice a library Button with its consequence);
   the rest are one line each. The tinted Your turn box style is parked.
3. **W3, the open step.** The selected step unfolds under its row: what it
   must prove (`RequirementRow`s, Add a requirement with this step as its
   Where), what the agent did (the story), then the step's parts (Brief, Gate,
   Findings, Handoffs, Ledger) and verbs. No fold head. "Done when" closes the
   list with the program's own and the every-step requirements and its own
   Add a requirement. The Requirements board above the steps is parked.
4. **W4, the composer.** The shape bar moves to the foot, above the status
   bar: "Tell the program what to change", the mic, Shape.
5. **W5, the status line.** "check:" names the script, never a flag.

## Not in this change

- The rounds strip during a run (the answered rounds are a quiet token under
  the goal only when the wire says they were asked).
- B's rail for long programs; it can come back as the 1440 form of the line
  if a twelve-step program reads badly in A.
