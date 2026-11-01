# Programs: the best of BroCrew (PG-IMPORT)

Owner, 2026-11-01: import the best of BroCrew, his sister project (an
Electron desktop app for teams of Claude and Codex agents), into HoldSpeak
Programs. We read a clone as data only. We ran nothing from it and we copy
no code from it; each slice below is our own build on our own engine.

BroCrew in one line (its README): "Give one agent a project. Follow the
team's work in one tree, answer requests in one queue, and get a report
back." Programs already has the engine (the tick, the gate, the ledger,
Decided for you, the briefing page, Reach). What BroCrew has that we lack is
a set of honesty rules about words: what the engine saw versus what an agent
said, how work ended versus where it stands, and what may travel to him and
what may not. Those rules are the import.

Nouns: `PROGRAMS-DESIGN-2026-10-28.md`, `PROGRAMS-REQUIREMENTS-2026-10-31.md`,
`PROGRAM-LANGUAGE-2026-10-31.md`, `PROGRAM-JOURNEYS-2026-10-31.md`,
`DIRECTION-2026-10-31.md`, `PROGRAM-WINDOW-2026-10-31.md`.

## The slices at a glance

| Slice | What | Build |
| --- | --- | --- |
| IMP1 | The step report in registers; the "finished · needs a decision" mark | Now |
| IMP2 | The to-do row; the ending word | Now |
| IMP3 | Wait sentences and "Since you were last here" on Today | Next |
| IMP4 | Never wider than the parent | Next (closes the open ruling) |
| IMP5 | Knowledge escalates, authority never does; four honest refusals | Next |
| IMP6 | Take it over, hand it back, on a step's lane | Next |
| IMP7 | The forest | Later (with handoffs and J5) |

## IMP1 · The step report in registers

**BroCrew.** README.md, "Read the result": "A finished piece of work comes
back with its outcome, what was checked, what wasn't, and where the files
are." And the rule that keeps it honest,
`apps/desktop/src/renderer/src/lib/work-report.ts`: "Nothing here is
computed from the words. Every value is copied off WorkReport, which the app
wrote beside the sentence it sent."

The second rule from the same file: "A person must be able to tell, at a
glance and without reading, the difference between finished and needs
nothing from me and finished and needs a decision." It solves this with "a
SECOND MARK on the row rather than a re-hue of the first … the mark is
achromatic", because "amber means frozen, waiting for a human" and a
finished task is not frozen.

**Programs today.** A step carries the agent's free text `report`
(`holdspeak/services/program_service.py`, `step_done`, `step["report"] =
text`) and at most three story lines (`brief_words.step_story`). The story
mixes what the engine did with what the agent said, and the face cannot
tell them apart. The checkpoints already carry `by` (engine, agent, owner;
`db/programs.py` `add_checkpoint`), which IS the register. A Done Program
shows the same word whether or not it left him a decision.

**The slice.**
- Hub: each engine checkpoint on a step records what the engine saw on the
  step at that moment (`seen`: the head commit when it differs from the
  base, the checked commit and its verdict, the PR number, the state) in the
  checkpoint's JSON. No new table. `brief_words.step_report` builds the
  report from the step's own fields and those checkpoints, never from a
  line's prose:
  - **Checked:** what the engine observed: the commit, the check result, the
    PR, the merge, each Check or Measure requirement the engine judged (with
    its value). Each line cites the engine checkpoint that saw it. A fact no
    engine checkpoint saw is not in this register.
  - **The agent says:** the agent's own `said_done` report (first sentence,
    scrubbed) and its own checkpoint lines (`by = agent`).
  - **Not checked:** each Your word requirement that is not judged, each
    Review that did not run, a gate check that was off or skipped.
  - **Files:** the step's diff file list against its base commit, bounded
    (at most 12 names and "and 4 more").
- Wire: `report` on each step in `/api/programs/{id}` becomes
  `{observed, claimed, not_checked, files, files_more}` when the step is
  Done, Merged, Parked or Skipped; the agent's raw text moves to
  `report_text`. The Program summary gains `finished` (`finished` or
  `needs_decision`).
- Faces: the open step (`StepFold`) shows the four registers in that order,
  each a plain label ("Checked:", "The agent says:", "Not checked:",
  "Files:") over its lines. No chips, no badges. The briefing page's evidence
  row gets "Report". The Programs list row and the track show "finished" or
  "finished · needs a decision" as an achromatic mark beside the state;
  never the amber Your turn lamp.
- Fence: a hub test that no report line comes from a checkpoint's prose
  and that every Checked line cites a checkpoint by engine.

## IMP2 · The to-do row and the ending word

**BroCrew.** `apps/desktop/src/renderer/src/lib/work-waits.ts`: the presses
on a to-do are `TODO_DONE = 'Done'`, `TODO_CANT = "Can't do it"`, the note
`'Add a note (optional)'`, and the head "`${askedByName} asks you to do
this · ${label}`". After the press: "Done. Ada is told." or "Sent. Ada is
told you can't do it."

`apps/desktop/src/renderer/src/lib/ending.ts`: "The status column answers
'is this conversation over' … It has never answered 'did the work in it
finish', and those are different questions with different actions behind
them." Its words: finished, failed, interrupted, cut off, unknown. And "Why
`completed` has a word too": "a row with no word would then mean either 'it
finished' or 'we hold no closed turn for it'".

**Programs today.** A Your word requirement with walk lines
(`program_requirements.py`, `spec.walk`) becomes a `requirement_word` row
only at the merge gate, with Met and Unmet (`program_service.py`,
`requirement_items`). The row does not say who asks, and the agent hears his
answer only on Unmet with a launch (`_send_back`). A step's state word
(Parked) does not say whether the agent finished, failed or was cut off; the
parked reason is prose.

**The slice.**
- To-do: a required Your word requirement with walk lines on a step that
  runs or waits at its gate becomes a Your turn row of kind `todo`: the head
  "Claude asks you to do this · step 3", the walk lines, the presses Done
  and Can't do it, and an optional note (StringGadget with the mic). Done
  writes the requirement Met (his word, his note as the evidence); Can't do
  it writes it Unmet with his note. The agent is told in the step's next
  prompt (a line in `facts.amendments`, sent with the next prompt). The same
  words reach the page, Telegram and the call through `brief_words`
  (QUESTIONS, consequences, settle words).
- Ending: each step carries `ending` (finished, failed, interrupted, none)
  apart from its state, set by the engine from the lane's end: a green
  finish (merged, done) is finished; a stopped or cut-off launch is
  interrupted; a failed push, PR or check after the last round is failed;
  else none. The step row says "Parked · interrupted"; the list row and the
  track use the word.

## IMP3 · Wait sentences and "Since you were last here"

**BroCrew.** `apps/desktop/src/shared/tasks.ts`, `WAITING_STANDS_FOR`:
"Each one says what the LEDGER holds and never who must move. 'Nobody has'
rather than 'you have not'". And the stop sentences, `UNDRIVEN_SENTENCES`:
"its turn ended with this work still open", "the turn it was running in was
stopped", "the app restarted while it was open". The Today block,
`components/SinceYouWereLastHere.vue`: "Part of the record couldn't be read,
so some lines may be missing." and "Only the newest N were read; older ones
may be missing."

**Programs today.** The step's held reason and parked reason are free
prose (`held_reason`, `parked_reason`); `brief_words.parked_cause` maps some
of it back. Today (`today_service.py`) has no line for what Programs did
while he was away; Decided for you lives only in each Program window.

**The slice.** A closed vocabulary of wait and stop causes on the step
(`facts.wait`, `facts.stopped`), each with one sentence in `brief_words`;
Today gains "Since you were last here": the Programs ledger and Decided for
you since his last visit (newest first, at most N), with the two honesty
lines when a read failed or was capped. Faces: Today's fold, the step row's
line. Engine: the runner writes the cause key, never only the sentence.

## IMP4 · Never wider than the parent

**BroCrew.** `docs/development.md`, "Where an agent can reach": "a spawned
session inherits its parent's mode and may never be wider than it … A
spawned session runs as its parent does and never wider." `docs/safety.md`:
"when an agent starts another agent, the new one runs in the starter's
mode, so an agent in 'ask' mode can't start one in 'auto' mode."

**Programs today.** `ProgramService.create` takes any `control` from any
writer, and `update` lets "the agent that made it" set `control` to YOLO
(`program_service.py`, `update`, `program["control"] = control`). #1682 and
#1683 stop an agent lowering the bar through the text, a sentence, a round,
a draft and a step gate; the Program's own control level is still open.

**The slice.** An agent-made Program, a handoff, a race entrant and a
sub-agent run at a control no wider than what made them (Secure < Normal <
YOLO, by `program_rules.level_of`). An agent's `program.create` at a wider
level is made at its parent's level and says so in the ledger; an agent's
`program.update` to a wider level is refused (`control_wider`: "An agent
cannot widen the control level. Ask the owner."). His own press is never
refused. This closes the open ruling. Faces: none new; the refusal reaches
the agent as the tool's error.

## IMP5 · Knowledge escalates, authority never does

**BroCrew.** `packages/runtime/src/question-channel.ts`: "Knowledge
escalates. Authority does not. A question is knowledge … A permission is
authority, it is always a person's, and it never travels." Each routing is
recorded: "its answer is RECORDED by its caller … whose `because` field is
what makes 'has anything permission-shaped ever arrived here?' a question
the ledger answers". And `answer-refused.ts`: "The four ways answering a
card can be refused, and they are genuinely different events": not-pending,
not-offered, not-usable, not-kept.

**Programs today.** Reach routes a held item to the page, Telegram or a
call by the rules (`reach_service.py`), but the ledger does not say why it
went. A late answer on the page says "Answered already: …" or "Answered
already on your desk." (`briefing_service.py`, `_answer`), without when or
from where, and a bad choice is "This choice is not on the page."

**The slice.** Every routed request to the page, Telegram or a call records
a `because` (the rule key: `level`, `quiet_hours`, `may_call`, `kind`) on
its Reach row. The four refusals of a late answer, each one sentence:
not pending → "Answered at 21:46 from the desk" (the clock and the channel
from the decision record); not offered → "That choice was not offered";
not usable → "Say which one" (the item stays live); not kept → "Your answer
was not kept; nothing was sent. Try again." Faces: the page's settled face,
the Telegram reply, the call's last line.

## IMP6 · Take it over, hand it back, on a step's lane

**BroCrew.** `apps/desktop/src/renderer/src/lib/taking-over.ts`: "It says
'take it over', because it IS that act." `handing-it-back.ts`: "This one
still asks once and never twice: a confirmation in front of a REVERSIBLE
act teaches a person the act weighs what an irreversible one does. Handing
back is undone by taking it again."

**Programs today.** The step row has Open lane (`StepRow.tsx`), which opens
the agent's pane. Nothing tells the engine that he is typing in it; the tick
can prompt the agent over him (a commit nudge, an amend at turn end).

**The slice.** Take it over on a running step's row: the engine records
`facts.taken_by = owner`, the tick sends no prompt and no nudge to that
lane, and the row says "You have the lane". Hand it back gives it back and
the tick goes on from the branch head. No confirmation on either press.

## IMP7 · The forest (later)

**BroCrew.** README.md: "Work is a tree, not a thread. Every request
becomes a labelled piece of work with an owner. An agent can hand part of
it to another agent, which shows up as a child piece: you can watch one
request become several agents' work, and trace any result back to what
asked for it."

**Programs today.** A Program is a line of steps; handoffs and race
entrants hang off a step (`handoffs`, `contenders`); an agent-made Program
names its origin (`origin_ref`) but no face draws the tree.

**The slice (later).** With the handoff work and journey J5 (the race):
the Programs list can fold a Program made by another Program's step under
it, and the Program window's line can show a step's handoffs and entrants
as a branch. Not designed here.

## What this note did not establish

- Whether every runner path that sets `head_commit`, `check_verdict` or
  `pr_number` writes an engine checkpoint in the same tick. IMP1 drops a
  fact no engine checkpoint saw, so a missing checkpoint shows as a
  missing line, never as a false one.
- Old steps carry no `seen` record; their Checked register is empty until
  the engine writes again.
